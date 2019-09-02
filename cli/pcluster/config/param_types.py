# Copyright 2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
# limitations under the License.
import json
import logging
import re

from configparser import DuplicateSectionError, NoOptionError, NoSectionError

from pcluster.utils import error, get_cfn_param, get_efs_mount_target_id, warn
from future.moves.collections import OrderedDict

LOGGER = logging.getLogger(__name__)


# ---------------------- standard Parameters ---------------------- #
# The following classes represent the Param of the standard types
# like String, Int, Float, Bool and Json
# and how to convert them from/to CFN/file.


class Param(object):
    def __init__(
        self,
        section_key,
        section_label,
        param_key,
        param_map,
        pcluster_config,
        cfn_value=None,
        config_parser=None,
        cfn_params=None,
    ):
        self.section_key = section_key
        self.section_label = section_label
        self.key = param_key
        self.map = param_map
        self.pcluster_config = pcluster_config

        # initialize param value
        if cfn_params or cfn_value:
            self._init_from_cfn(cfn_params=cfn_params, cfn_value=cfn_value)
        elif config_parser:
            try:
                self._init_from_file(config_parser)
            except NoOptionError:
                self._init_from_map()
            except NoSectionError:
                section_name = _get_file_section_name(self.section_key, self.section_label)
                error("Section '[{0}]' not found in the config file.".format(section_name))
        else:
            self._init_from_map()

    def get_value_from_string(self, string_value):
        param_value = self.get_default_value()

        if isinstance(string_value, str):
            string_value = string_value.strip()

        if string_value and string_value != "NONE":
            param_value = string_value

        return param_value

    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoOptionError, NoSectionError if unable to get the param from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        self.value = config_parser.get(section_name, self.key)
        self._check_allowed_values()

    def _init_from_cfn(self, cfn_params=None, cfn_value=None):
        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            cfn_value = get_cfn_param(cfn_params, cfn_converter) if cfn_converter else "NONE"
            self.value = self.get_value_from_string(cfn_value)
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def _init_from_map(self):
        self.value = self.get_default_value()
        if self.value:
            LOGGER.debug("Setting default value '{0}' for key '{1}'".format(self.value, self.key))

    def _check_allowed_values(self):
        # verify if value is one of the allowed values
        allowed_values = self.map.get("allowed_values", None)
        if allowed_values:
            if isinstance(allowed_values, list):
                if self.value not in allowed_values:
                    error(
                        "The configuration parameter '{0}' has an invalid value '{1}'\n"
                        "Allowed values are: {2}".format(self.key, self.value, allowed_values)
                    )
            else:
                # convert to regex
                if not re.compile(allowed_values).match(str(self.value)):
                    error(
                        "The configuration parameter '{0}' has an invalid value '{1}'\n"
                        "Allowed values are: {2}".format(self.key, self.value, allowed_values)
                    )

    def validate(self, fail_on_error=True):
        validation_func = self.map.get("validator", None)

        if not validation_func:
            LOGGER.debug("Configuration parameter '{0}' has no validator".format(self.key))  # TODO remove
        elif not self.value:
            LOGGER.debug("Configuration parameter '{0}' has not a value".format(self.key))  # TODO remove
        else:
            errors, warnings = validation_func(self.key, self.value, self.pcluster_config)
            if errors:
                error(
                    "The configuration parameter '{0}' has an invalid value '{1}'\n"
                    "{2}".format(self.key, self.value, "\n".join(errors)),
                    fail_on_error,
                )
            elif warnings:
                warn(
                    "The configuration parameter '{0}' has a wrong value '{1}'\n{2}".format(
                        self.key, self.value, "\n".join(warnings)
                    )
                )
            else:
                LOGGER.debug("Configuration parameter '{0}' is valid".format(self.key))

    def to_file(self, config_parser):
        section_name = _get_file_section_name(self.section_key, self.section_label)
        if self.value is not None and self.value != self.get_default_value():
            config_parser.set(section_name, self.key, str(self.value))
        else:
            # remove parameter from config_parser if there
            try:
                config_parser.remove_option(section_name, self.key)
            except NoSectionError:
                pass

    def to_cfn(self):
        cfn_params = {}
        cfn_converter = self.map.get("cfn", None)

        if cfn_converter:
            cfn_value = self.get_cfn_value()
            cfn_params.update({cfn_converter: str(cfn_value)})

        return cfn_params

    def get_default_value(self):
        return self.map.get("default", None)

    def get_cfn_value(self):
        return str(self.value if self.value is not None else self.map.get("default", "NONE"))


class FloatParam(Param):
    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoOptionError, NoSectionError if unable to get the param from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        try:
            self.value = config_parser.getfloat(section_name, self.key)
            self._check_allowed_values()
        except ValueError:
            error("Configuration parameter '{0}' must be a Float".format(self.key))

    def get_value_from_string(self, string_value):
        param_value = self.get_default_value()

        try:
            if string_value is not None and isinstance(string_value, str):
                string_value = string_value.strip()
                if string_value != "NONE":
                    param_value = float(string_value)
        except ValueError:
            pass

        return param_value


class BoolParam(Param):
    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoOptionError, NoSectionError if unable to get the param from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        try:
            self.value = config_parser.getboolean(section_name, self.key)
            self._check_allowed_values()
        except ValueError:
            error("Configuration parameter '{0}' must be a Boolean".format(self.key))

    def get_value_from_string(self, string_value):
        param_value = self.get_default_value()

        if string_value is not None and isinstance(string_value, str):
            string_value = string_value.strip()
            if string_value != "NONE":
                param_value = string_value == "true"

        return param_value

    def to_file(self, config_parser):
        section_name = _get_file_section_name(self.section_key, self.section_label)
        if self.value != self.get_default_value():
            config_parser.set(section_name, self.key, self.get_cfn_value())
        else:
            # remove parameter from config_parser if there
            try:
                config_parser.remove_option(section_name, self.key)
            except NoSectionError:
                pass

    def get_cfn_value(self):
        param_value = self.get_default_value() if self.value is None else self.value
        return "true" if param_value else "false"


class IntParam(Param):
    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoOptionError, NoSectionError if unable to get the param from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        try:
            self.value = config_parser.getint(section_name, self.key)
            self._check_allowed_values()
        except ValueError:
            error("Configuration parameter '{0}' must be an Integer".format(self.key))

    def get_value_from_string(self, string_value):
        param_value = self.get_default_value()
        try:
            if string_value is not None and isinstance(string_value, str):
                string_value = string_value.strip()
                if string_value != "NONE":
                    param_value = int(string_value)
        except ValueError:
            pass

        return param_value


class JsonParam(Param):  # FIXME verify extra json in python 2.7
    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoOptionError, NoSectionError if unable to get the param from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        item_value = config_parser.get(section_name, self.key)
        self.value = self.get_value_from_string(item_value)
        self._check_allowed_values()

    def get_value_from_string(self, string_value):
        param_value = self.get_default_value()
        try:
            # do not convert empty string
            if string_value and isinstance(string_value, str):
                string_value = string_value.strip()
                if string_value != "NONE":
                    param_value = json.loads(string_value)
        except (TypeError, ValueError) as e:
            error("Error parsing JSON parameter '{0}'. {1}".format(self.key), e)

        return param_value

    def get_default_value(self):
        return self.map.get("default", {})


# ---------------------- custom Parameters ---------------------- #
# The following classes represent "custom" parameters
# that require some custom action during CFN/file conversion


class SharedDirParam(Param):
    """
    Class to manage the shared_dir configuration parameter.

    We need this class since the same CFN input parameter "SharedDir" is populated
    from the "shared" parameter of the cluster section (e.g. SharedDir = /shared)
    and the "shared" parameter of the ebs sections (e.g. SharedDir = /shared1,/shared2,NONE,NONE,NONE).
    """

    def to_cfn(self):
        cfn_params = {}
        # if contains ebs_settings --> single SharedDir
        if not self.pcluster_config.get_section("ebs"):
            cfn_params.update({self.map.get("cfn"): self.get_cfn_value()})
        # else: there are ebs volumes, let the EBSSettings populate the SharedDir CFN parameter.
        return cfn_params

    def to_file(self, config_parser):
        # if contains ebs_settings --> single SharedDir
        section_name = _get_file_section_name(self.section_key, self.section_label)
        if not self.pcluster_config.get_section("ebs") and self.value != self.get_default_value():
            config_parser.set(section_name, self.key, self.value)
        # else: there are ebs volumes, let the EBSSettings parse the SharedDir CFN parameter.


class SpotPriceParam(IntParam):
    def _init_from_cfn(self, cfn_params, cfn_value=None):
        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            if get_cfn_param(cfn_params, "Scheduler") == "awsbatch":
                self._init_from_map()
            else:
                # we have the same CFN input parameters for both spot_price and spot_bid_percentage
                # so the CFN input could be a float
                self.value = int(float(get_cfn_param(cfn_params, cfn_converter)))
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def to_cfn(self):
        cfn_params = {}

        cluster_config = self.pcluster_config.get_section(self.section_key)
        if cluster_config.get_param_value("scheduler") != "awsbatch":
            cfn_value = cluster_config.get_param_value("spot_price")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})

        return cfn_params


class SpotBidPercentageParam(FloatParam):
    def _init_from_cfn(self, cfn_params, cfn_value=None):
        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            if get_cfn_param(cfn_params, "Scheduler") == "awsbatch":
                self.value = float(get_cfn_param(cfn_params, cfn_converter))
            else:
                self._init_from_map()
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def to_cfn(self):
        cfn_params = {}

        cluster_config = self.pcluster_config.get_section(self.section_key)
        if cluster_config.get_param_value("scheduler") == "awsbatch":
            cfn_value = cluster_config.get_param_value("spot_bid_percentage")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})

        return cfn_params


class DesiredSizeParam(IntParam):
    def _init_from_cfn(self, cfn_params=None, cfn_value=None):
        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            cfn_value = get_cfn_param(cfn_params, cfn_converter) if cfn_converter else "NONE"
            # initialize the value from cfn or from map according to the scheduler
            if get_cfn_param(cfn_params, "Scheduler") == "awsbatch":
                if self.key == "initial_queue_size":
                    self._init_from_map()
                elif self.key == "desired_vcpus":
                    self.value = self.get_value_from_string(cfn_value)
            else:
                if self.key == "initial_queue_size":
                    self.value = self.get_value_from_string(cfn_value)
                elif self.key == "desired_vcpus":
                    self._init_from_map()
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def to_cfn(self):
        cfn_params = {}

        cluster_config = self.pcluster_config.get_section(self.section_key)
        if cluster_config.get_param_value("scheduler") == "awsbatch":
            cfn_value = cluster_config.get_param_value("desired_vcpus")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})
        else:
            cfn_value = cluster_config.get_param_value("initial_queue_size")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})

        return cfn_params


class MaxSizeParam(IntParam):
    def _init_from_cfn(self, cfn_params=None, cfn_value=None):

        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            cfn_value = get_cfn_param(cfn_params, cfn_converter) if cfn_converter else "NONE"
            # initialize the value from cfn or from map according to the scheduler
            if get_cfn_param(cfn_params, "Scheduler") == "awsbatch":
                if self.key == "max_queue_size":
                    self._init_from_map()
                elif self.key == "max_vcpus":
                    self.value = self.get_value_from_string(cfn_value)
            else:
                if self.key == "max_queue_size":
                    self.value = self.get_value_from_string(cfn_value)
                elif self.key == "max_vcpus":
                    self._init_from_map()
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def to_cfn(self):
        cfn_params = {}

        cluster_config = self.pcluster_config.get_section(self.section_key)
        if cluster_config.get_param_value("scheduler") == "awsbatch":
            cfn_value = cluster_config.get_param_value("max_vcpus")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})
        else:
            cfn_value = cluster_config.get_param_value("max_queue_size")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})

        return cfn_params


class MaintainInitialSizeParam(BoolParam):
    def _init_from_cfn(self, cfn_params=None, cfn_value=None):

        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            # initialize the value from cfn or from map according to the scheduler
            if get_cfn_param(cfn_params, "Scheduler") == "awsbatch":
                self._init_from_map()
            else:
                # MinSize param > 0 means that maintain_initial_size was set to true at cluster creation
                min_size_cfn_value = get_cfn_param(cfn_params, cfn_converter) if cfn_converter else "0"
                min_size_value = int(min_size_cfn_value) if min_size_cfn_value != "NONE" else 0
                self.value = min_size_value > 0
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def to_cfn(self):
        cfn_params = {}

        cluster_config = self.pcluster_config.get_section(self.section_key)
        if cluster_config.get_param_value("scheduler") != "awsbatch":
            cfn_value = cluster_config.get_param_value("maintain_initial_size")
            min_size_value = cluster_config.get_param_value("initial_queue_size") if cfn_value else "0"
            cfn_params.update({self.map.get("cfn"): str(min_size_value)})

        return cfn_params


class MinSizeParam(IntParam):
    def _init_from_cfn(self, cfn_params=None, cfn_value=None):

        cfn_converter = self.map.get("cfn", None)
        if cfn_converter and cfn_params:
            cfn_value = get_cfn_param(cfn_params, cfn_converter) if cfn_converter else "NONE"
            # initialize the value from cfn or from map according to the scheduler
            if get_cfn_param(cfn_params, "Scheduler") == "awsbatch":
                self.value = self.get_value_from_string(cfn_value)
            else:
                self._init_from_map()
        elif cfn_value:
            self.value = self.get_value_from_string(cfn_value)
        else:
            self._init_from_map()

    def to_cfn(self):
        cfn_params = {}

        cluster_config = self.pcluster_config.get_section(self.section_key)
        if cluster_config.get_param_value("scheduler") == "awsbatch":
            cfn_value = cluster_config.get_param_value("min_vcpus")
            cfn_params.update({self.map.get("cfn"): str(cfn_value)})

        return cfn_params


# ---------------------- SettingsParam ---------------------- #


class SettingsParam(Param):
    def __init__(
        self,
        section_key,
        section_label,
        param_key,
        param_map,
        pcluster_config,
        cfn_value=None,
        config_parser=None,
        cfn_params=None,
    ):
        self.related_section_map = param_map.get("referred_section")
        self.related_section_key = self.related_section_map.get("key")
        self.related_section_type = self.related_section_map.get("type")
        super(SettingsParam, self).__init__(
            section_key, section_label, param_key, param_map, pcluster_config, cfn_value, config_parser, cfn_params
        )

    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoSectionError if unable to get the section from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        try:
            self.value = config_parser.get(section_name, self.key)
            if self.value:
                if "," in self.value:
                    error(
                        "The value of '{0}' parameter is invalid. "
                        "It can only contains a single {1} section label.".format(self.key, self.related_section_key)
                    )
                else:
                    # Calls the "from_file" of the Section
                    section = self.related_section_type(
                        self.related_section_map,
                        self.pcluster_config,
                        section_label=self.value,
                        config_parser=config_parser,
                        fail_on_absence=True,
                    )
                    self.pcluster_config.add_section(section)
        except NoOptionError:
            self._init_from_map()

    def _init_from_cfn(self, cfn_params, cfn_value=None):
        # TODO Use the label if available
        self.value = self.map.get("default", None)
        section = self.related_section_type(
            self.related_section_map, self.pcluster_config, section_label=self.value, cfn_params=cfn_params
        )
        self.pcluster_config.add_section(section)

    def _init_from_map(self):
        self.value = self.map.get("default", None)
        if self.value:
            # the SettingsParam has a default label, it means that it is required to initialize the
            # the related section with default values.
            LOGGER.debug("Initializing default Section '{0}' for key '{1}'".format(self.value, self.key))
            # Use the label defined in the SettingsParam map
            if "," in self.value:
                error(
                    "The default value of '{0}' parameter is invalid. "
                    "It can only contains a single {1} section label.".format(self.key, self.related_section_key)
                )
            else:
                section = self.related_section_type(
                    self.related_section_map, self.pcluster_config, section_label=self.value
                )
                self.pcluster_config.add_section(section)

    def to_file(self, config_parser):
        section = self.pcluster_config.get_section(self.related_section_key, self.value)

        settings_param_created = False
        if section:
            settings_param_value = section.label if section.label else None

            # create sections
            for param_key, param_map in self.related_section_map.get("params").items():
                param_value = section.get_param_value(param_key)

                if not settings_param_created and param_value != param_map.get("default", None):
                    # add "*_settings = *" to the parent section
                    # only if at least one value is different from the default one
                    section_name = _get_file_section_name(self.section_key, self.section_label)
                    config_parser.set(section_name, self.key, settings_param_value)
                    settings_param_created = True

            section.to_file(config_parser)

    def to_cfn(self):
        cfn_params = {}
        section = self.pcluster_config.get_section(self.related_section_key, self.value)
        if not section:
            # Crate a default section and convert it to cfn, to populate with default values (e.g. NONE)
            section = self.related_section_type(self.related_section_map, self.pcluster_config)

        cfn_params.update(section.to_cfn())

        return cfn_params


class EBSSettingsParam(SettingsParam):
    def _init_from_file(self, config_parser):
        """
        Initialize param_value from config_parser.

        :param config_parser: the configparser object from which get the parameter
        :raise NoSectionError if unable to get the section from config_parser
        """
        section_name = _get_file_section_name(self.section_key, self.section_label)
        try:
            self.value = config_parser.get(section_name, self.key)
            if self.value:
                for section_label in self.value.split(","):
                    section = self.related_section_type(
                        self.related_section_map,
                        self.pcluster_config,
                        section_label=section_label.strip(),
                        config_parser=config_parser,
                        fail_on_absence=True,
                    )
                    self.pcluster_config.add_section(section)
        except NoOptionError:
            self._init_from_map()

    def _init_from_cfn(self, cfn_params, cfn_value=None):
        # init ebs section only if there are more than one ebs (the default one)
        labels = []
        num_of_ebs = int(get_cfn_param(cfn_params, "NumberOfEBSVol"))
        if num_of_ebs > 1:
            for index in range(num_of_ebs):
                configured_params = False
                # TODO fixme the label if available
                label = "{0}{1}".format(self.related_section_key, str(index + 1))
                labels.append(label)

                # create empty section
                related_section_type = self.related_section_map.get("type", Section)
                related_section = related_section_type(self.related_section_map, label)

                for param_key, param_map in self.related_section_map.get("params").items():
                    cfn_converter = param_map.get("cfn", None)
                    if cfn_converter:

                        param_type = param_map.get("type", Param)
                        cfn_value = get_cfn_param(cfn_params, cfn_converter).split(",")[index]
                        param = param_type(
                            self.section_key,
                            self.section_label,
                            param_key,
                            param_map,
                            self.pcluster_config,
                            cfn_value=cfn_value,
                        )
                        related_section.add_param(param)

                        if param.value != param_map.get("default", None):
                            configured_params = True

                if configured_params:
                    self.pcluster_config.add_section(related_section)
        self.value = ",".join(labels) if labels else None

    def to_file(self, config_parser):

        sections = {}
        if self.value:
            for section_label in self.value.split(","):
                sections.update(self.pcluster_config.get_section(self.related_section_key, section_label.strip()))

        settings_param_created = False
        # create sections
        for section_label, section in sections:
            for param_key, param_map in self.related_section_map.get("params").items():
                param_value = section.get_param_value(param_key)

                if not settings_param_created and param_value != param_map.get("default", None):
                    # add "*_settings = *" to the parent section
                    # only if at least one value is different from the default one
                    section_name = _get_file_section_name(self.section_key, self.section_label)
                    config_parser.set(section_name, self.key, self.value)
                    settings_param_created = True

            section.to_file(config_parser)

    def to_cfn(self):
        """Convert a list of sections to multiple CFN params."""
        sections = OrderedDict({})
        if self.value:
            for section_label in self.value.split(","):
                section = self.pcluster_config.get_section(self.related_section_key, section_label.strip())
                sections.update({section_label: section})

        max_number_of_ebs_volumes = 5

        cfn_params = {}
        number_of_ebs_sections = len(sections)
        for param_key, param_map in self.related_section_map.get("params").items():
            if number_of_ebs_sections == 0 and param_key == "shared_dir":
                # The same CFN parameter is used for both single and multiple EBS cases
                # if there are no ebs volumes, let the SharedDirParam populate the "SharedDir" CFN parameter.
                continue

            cfn_converter = param_map.get("cfn", None)
            if cfn_converter:

                cfn_value_list = []
                for section_label, section in sections.items():
                    param = section.get_param(param_key)
                    if param:
                        cfn_value_list.append(param.to_cfn().get(cfn_converter))
                    else:
                        # define a "default" param and convert it to cfn
                        param_type = param_map.get("type", Param)
                        param = param_type(section.key, section_label, param_key, param_map, self.pcluster_config)
                        cfn_value_list.append(param.to_cfn().get(cfn_converter))

                # add missing items until the max, with a default param
                param_type = param_map.get("type", Param)
                param = param_type(self.related_section_key, "default", param_key, param_map, self.pcluster_config)
                cfn_value_list.extend(
                    [param.to_cfn().get(cfn_converter)] * (max_number_of_ebs_volumes - number_of_ebs_sections)
                )

                cfn_value = ",".join(cfn_value_list)
                cfn_params.update({cfn_converter: cfn_value})

        # We always have at least one EBS volume
        cfn_params.update({"NumberOfEBSVol": str(max(number_of_ebs_sections, 1))})

        return cfn_params


# ---------------------- custom Section ---------------------- #
# The following classes represent the Section(s) and how to convert them from/to CFN/file.


class Section(object):
    def __init__(
        self,
        section_map,
        pcluster_config,
        section_label=None,
        cfn_params=None,
        config_parser=None,
        fail_on_absence=False,
    ):
        self.map = section_map
        self.key = section_map.get("key")
        self.label = section_label or self.map.get("label", "")
        self.pcluster_config = pcluster_config

        # initialize section_dict
        self.params = {}
        if cfn_params:
            self._init_params_from_cfn(cfn_params)
        elif config_parser:
            try:
                self._init_params_from_file(config_parser)
            except SectionNotFoundError:
                section_name = _get_file_section_name(self.key, self.label)
                if fail_on_absence:
                    error("Section '[{0}]' not found in the config file.".format(section_name))
                else:
                    LOGGER.info("Section '[{0}]' not found in the config file. Using defaults.".format(section_name))
                    self._init_params_from_map()
        else:
            self._init_params_from_map()

    def _init_params_from_file(self, config_parser):
        """
        :param config_parser: ConfigParser object
        """
        section_map_items = self.map.get("params")
        section_name = _get_file_section_name(self.key, self.label)

        if config_parser.has_section(section_name):
            for param_key, param_map in section_map_items.items():
                param_type = param_map.get("type", Param)

                param = param_type(
                    self.key,
                    self.label,
                    param_key,
                    param_map,
                    pcluster_config=self.pcluster_config,
                    config_parser=config_parser,
                )
                self.add_param(param)

                not_valid_keys = [
                    key for key, value in config_parser.items(section_name) if key not in section_map_items
                ]
                if not_valid_keys:
                    error(
                        "The configuration parameter{0} '{1}' {2} not allowed in the [{3}] section".format(
                            "s" if len(not_valid_keys) > 1 else "",
                            ",".join(not_valid_keys),
                            "are" if len(not_valid_keys) > 1 else "is",
                            section_name,
                        )
                    )
        else:
            raise SectionNotFoundError

    def _init_params_from_cfn(self, cfn_params):
        # TODO get the label if saved in cfn
        cfn_converter = self.map.get("cfn", None)
        if cfn_converter:
            # It is a section converted to a single CFN parameter
            cfn_values = get_cfn_param(cfn_params, cfn_converter).split(",")

            cfn_param_index = 0
            for param_key, param_map in self.map.get("params").items():
                try:
                    cfn_value = cfn_values[cfn_param_index]
                except IndexError:
                    # This happen if the expected comma separated CFN param doesn't exist in the Stack,
                    # so it is set to a single NONE value
                    cfn_value = "NONE"

                param_type = param_map.get("type", Param)
                param = param_type(
                    self.key, self.label, param_key, param_map, self.pcluster_config, cfn_value=cfn_value
                )

                self.add_param(param)
                cfn_param_index += 1
        else:
            for param_key, param_map in self.map.get("params").items():
                param_type = param_map.get("type", Param)
                param = param_type(
                    self.key, self.label, param_key, param_map, self.pcluster_config, cfn_params=cfn_params
                )
                self.add_param(param)

    def _init_params_from_map(self):
        for param_key, param_map in self.map.get("params").items():
            param_type = param_map.get("type", Param)
            param = param_type(self.key, self.label, param_key, param_map, self.pcluster_config)
            self.add_param(param)

    def validate(self, fail_on_error=True):
        if self.params:
            section_name = _get_file_section_name(self.key, self.label)

            # validate section
            validation_func = self.map.get("validator", None)
            if validation_func:
                errors, warnings = validation_func(self.key, self.label, self.pcluster_config)
                if errors:
                    error(
                        "The section [{0}] is wrongly configured\n" "{1}".format(section_name, "\n".join(errors)),
                        fail_on_error,
                    )
                elif warnings:
                    warn("The section [{0}] is wrongly configured\n{1}".format(section_name, "\n".join(warnings)))
                else:
                    LOGGER.debug("Section '[{0}]' is valid".format(section_name))
            else:
                LOGGER.debug("Section '[{0}]' has not validators".format(section_name))

            # validate items
            for param_key, param_map in self.map.get("params").items():
                param_type = param_map.get("type", Param)

                param = self.get_param(param_key)
                if param:
                    param.validate(fail_on_error)
                else:
                    # define a default param and validate it
                    param_type(self.key, self.label, param_key, param_map, self.pcluster_config).validate(fail_on_error)

    def to_file(self, config_parser):

        config_section_name = _get_file_section_name(self.key, self.label)
        config_section_created = False

        for param_key, param_map in self.map.get("params").items():
            param = self.get_param(param_key)
            if not param:
                # generate a default param
                param_type = param_map.get("type", Param)
                param = param_type(self.key, self.label, param_key, param_map, self.pcluster_config)

            if not config_section_created and param.value != param_map.get("default", None):
                # write section in the config file only if at least one parameter value is different by the default
                try:
                    config_parser.add_section(config_section_name)
                except DuplicateSectionError:
                    LOGGER.debug("Section '{0}' is already present in the file.".format(config_section_name))
                    pass
                config_section_created = True

            param.to_file(config_parser)

    def to_cfn(self):
        cfn_params = {}
        cfn_converter = self.map.get("cfn", None)
        if cfn_converter:
            # it is a section converted to a single CFN parameter
            cfn_items = []
            for param_key, param_map in self.map.get("params").items():
                param = self.get_param(param_key)
                if param:
                    cfn_items.append(param.get_cfn_value())
                else:
                    param_type = param_map.get("type", Param)
                    param = param_type(self.key, self.label, param_key, param_map, self.pcluster_config)
                    cfn_items.append(param.get_cfn_value())

            if cfn_items[0] == "NONE":
                # empty dict or first item is NONE --> set all values to NONE
                cfn_items = ["NONE"] * len(self.map.get("params"))

            cfn_params.update({cfn_converter: ",".join(cfn_items)})
        else:
            # get value from config object
            for param_key, param_map in self.map.get("params").items():
                param = self.get_param(param_key)
                if param:
                    cfn_params.update(param.to_cfn())
                else:
                    # set CFN value from a default param
                    param_type = param_map.get("type", Param)
                    param = param_type(self.key, self.label, param_key, param_map, self.pcluster_config)
                    cfn_params.update(param.to_cfn())

        return cfn_params

    def add_param(self, param):
        """
        Add a Param to the Section.

        The internal representation is a dictionary like:
        {
            "key_name": Param,
            "base_os": Param,
            "use_public_ips": BoolParam,
            ...
        }

        :param param: the Param object to add to the Section
        """
        self.params[param.key] = param

    def get_param(self, param_key):
        """
        Return the Param object corresponding to the given key.

        :param param_key: yhe key to identify the Param object in the internal dictionary
        :return: a Param object
        """
        return self.params[param_key]

    def get_param_value(self, param_key):
        """
        Return the value of the Param object corresponding to the given key.

        :param param_key: the key to identify the Param object in the internal dictionary
        :return: the value of the Param object or None if the param is not present in the Section
        """
        return self.get_param(param_key).value if self.get_param(param_key) else None


class EFSSection(Section):
    def to_cfn(self):

        cfn_params = {}
        cfn_converter = self.map.get("cfn", None)

        cfn_items = []
        for param_key, param_map in self.map.get("params").items():
            param = self.get_param(param_key)
            if param:
                cfn_items.append(param.get_cfn_value())
            else:
                param_type = param_map.get("type", Param)
                param = param_type(self.key, self.label, param_key, param_map, self.pcluster_config)
                cfn_items.append(param.get_cfn_value())

        if cfn_items[0] == "NONE":
            efs_section_valid = False
            # empty dict or first item is NONE --> set all values to NONE
            cfn_items = ["NONE"] * len(self.map.get("params"))
        else:
            # add another CFN param that will identify if create or no a Mount Target for the given EFS FS Id
            master_avail_zone = self.pcluster_config.get_master_avail_zone()
            mount_target_id = get_efs_mount_target_id(
                efs_fs_id=self.get_param_value("efs_fs_id"), avail_zone=master_avail_zone
            )
            efs_section_valid = True if mount_target_id else False

        cfn_items.append("Valid" if efs_section_valid else "NONE")
        cfn_params.update({cfn_converter: ",".join(cfn_items)})
        return cfn_params


class ClusterSection(Section):
    def _init_params_from_cfn(self, cfn_params):
        self.label = get_cfn_param(cfn_params, "CLITemplate")
        super(ClusterSection, self)._init_params_from_cfn(cfn_params)

    def to_cfn(self):
        cfn_params = super(ClusterSection, self).to_cfn()
        cfn_params.update({"CLITemplate": self.label})
        cfn_params.update({"AvailabilityZone": self.pcluster_config.get_master_avail_zone()})
        return cfn_params


class SectionNotFoundError(Exception):
    pass


def _get_file_section_name(section_key, section_label=None):
    return section_key + (" {0}".format(section_label) if section_label else "")
