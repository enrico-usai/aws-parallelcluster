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
import logging
import re
from configparser import DuplicateSectionError, NoSectionError, NoOptionError

from pcluster.utils import fail, get_cfn_param, get_efs_mount_target_id, warn

LOGGER = logging.getLogger(__name__)


class Param(object):

    def __init__(self, param_key, param_map):
        self.param_key = param_key
        self.param_map = param_map

    def to_cfn_value(self, param_value):
        return str(param_value if param_value is not None else self.param_map.get("default", "NONE"))

    def from_cfn_value(self, cfn_value):
        return self.param_map.get("default", None) if cfn_value.strip() == "NONE" else cfn_value.strip()

    def from_file(self, config_parser, parent_section_name):
        try:
            param_value = config_parser.get(parent_section_name, self.param_key)
            self._check_allowed_values(param_value)

        except NoOptionError:
            param_value = self.param_map.get("default")
            if param_value:
                LOGGER.debug("Setting default value '{0}' for key '{1}'".format(param_value, self.param_key))
        except NoSectionError as e:
            LOGGER.error(e)
            raise e

        return self.param_key, param_value

    def to_file(self, config_parser, parent_section_dict, parent_section_name, param_value):
        if param_value is not None and param_value != self.param_map.get("default"):
            config_parser.set(parent_section_name, self.param_key, str(param_value))
        else:
            # remove parameter from config_parser if there
            try:
                config_parser.remove_option(parent_section_name, self.param_key)
            except NoSectionError:
                pass

    def _check_allowed_values(self, param_value):
        # verify if value is one of the allowed values
        allowed_values = self.param_map.get("allowed_values", None)
        if allowed_values:
            if isinstance(allowed_values, list):
                if param_value not in allowed_values:
                    fail(
                        "The configuration parameter '{0}' has an invalid value '{1}'\n"
                        "Allowed values are: {2}".format(self.param_key, param_value, allowed_values)
                    )
            else:
                # convert to regex
                if not re.compile(allowed_values).match(str(param_value)):
                    fail(
                        "The configuration parameter '{0}' has an invalid value '{1}'\n"
                        "Allowed values are: {2}".format(self.param_key, param_value, allowed_values)
                    )

    def validate(self, param_value, section_dict, pcluster_dict):
        validation_func = self.param_map.get("validator", None)

        if not validation_func:
            LOGGER.debug("Configuration parameter '{0}' has no validator".format(self.param_key))  # TODO remove
        elif not param_value:
            LOGGER.debug("Configuration parameter '{0}' has not a value".format(self.param_key))  # TODO remove
        else:
            errors, warnings = validation_func(self.param_key, param_value, pcluster_dict)
            if errors:
                fail(
                    "The configuration parameter '{0}' has an invalid value '{1}'\n{2}".format(
                        self.param_key, param_value, "\n".join(errors)
                    )
                )
            elif warnings:
                warn(
                    "The configuration parameter '{0}' has a wrong value '{1}'\n{2}".format(
                        self.param_key, param_value, "\n".join(warnings)
                    )
                )
            else:
                LOGGER.debug("Configuration parameter '{0}' is valid".format(self.param_key))

    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}
        cfn_converter = self.param_map.get("cfn", None)

        if cfn_converter:
            cfn_value = self.to_cfn_value(parent_section_dict.get(self.param_key))
            cfn_params.update({cfn_converter: str(cfn_value)})

        return cfn_params

    def from_cfn(self, cfn_params):
        cfn_converter = self.param_map.get("cfn", None)
        cfn_value = get_cfn_param(cfn_params, cfn_converter) if cfn_converter else "NONE"

        return self.param_key, self.from_cfn_value(cfn_value)


class FloatParam(Param):
    def from_file(self, config_parser, parent_section_name):

        try:
            param_value = config_parser.getfloat(parent_section_name, self.param_key)
            self._check_allowed_values(param_value)

        except NoOptionError:
            param_value = self.param_map.get("default")
            if param_value:
                LOGGER.debug("Setting default value '{0}' for key '{1}'".format(param_value, self.param_key))
        except NoSectionError as e:
            LOGGER.error(e)
            raise e
        except ValueError:
            fail("Configuration parameter '{0}' must be a Float".format(self.param_key))

        return self.param_key, param_value

    def from_cfn_value(self, cfn_value):
        try:
            param_value = float(cfn_value.strip())
        except ValueError:
            param_value = self.param_map.get("default", None)

        return param_value


class BoolParam(Param):
    def from_file(self, config_parser, parent_section_name):

        try:
            param_value = config_parser.getboolean(parent_section_name, self.param_key)
            self._check_allowed_values(param_value)
        except NoOptionError:
            param_value = self.param_map.get("default")
            if param_value:
                LOGGER.debug("Setting default value '{0}' for key '{1}'".format(param_value, self.param_key))
        except NoSectionError as e:
            LOGGER.error(e)
            raise e
        except ValueError:
            fail("Configuration parameter '{0}' must be a Boolean".format(self.param_key))

        return self.param_key, param_value

    def to_file(self, config_parser, parent_section_dict, parent_section_name, param_value):
        if param_value != self.param_map.get("default"):
            config_parser.set(parent_section_name, self.param_key, self.to_cfn_value(param_value))
        else:
            # remove parameter from config_parser if there
            try:
                config_parser.remove_option(parent_section_name, self.param_key)
            except NoSectionError:
                pass

    def to_cfn_value(self, param_value):
        if param_value is None:
            param_value = self.param_map.get("default")

        return "true" if param_value else "false"

    def from_cfn_value(self, cfn_value):
        return self.param_map.get("default") if cfn_value.strip() == "NONE" else cfn_value.strip() == "true"


class IntParam(Param):
    def from_file(self, config_parser, parent_section_name):

        try:
            param_value = config_parser.getint(parent_section_name, self.param_key)
            self._check_allowed_values(param_value)
        except NoOptionError:
            param_value = self.param_map.get("default")
            if param_value:
                LOGGER.debug("Setting default value '{0}' for key '{1}'".format(param_value, self.param_key))
                return self.param_key, param_value
            pass
        except NoSectionError as e:
            LOGGER.error(e)
            raise e
        except ValueError:
            fail("Configuration parameter '{0}' must be an Integer".format(self.param_key))

        return self.param_key, param_value

    def from_cfn_value(self, cfn_value):
        try:
            param_value = int(cfn_value.strip())
        except ValueError:
            param_value = self.param_map.get("default", None)

        return param_value


class SharedDirParam(Param):

    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}
        # if contains ebs_settings --> single SharedDir
        if not parent_section_dict.get("ebs"):
            cfn_value = parent_section_dict.get("shared_dir")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})
        # else let the EBSSettings parse the item
        return cfn_params

    def to_file(self, config_parser, parent_section_dict, parent_section_name, param_value):
        # if contains ebs_settings --> single SharedDir
        if not parent_section_dict.get("ebs"):
            config_parser.set(parent_section_name, self.param_key, parent_section_dict.get("shared_dir"))
        # else do nothing, let the EBSSettings parse the item


class SpotPriceParam(IntParam):
    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}

        if parent_section_dict.get("scheduler") != "awsbatch":
            cfn_value = parent_section_dict.get("spot_price")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})

        return cfn_params

    def from_cfn(self, cfn_params):
        cfn_converter = self.param_map.get("cfn", None)
        # We have both spot_price and spot_bid_percentage in the same param
        # TODO remove in the final version
        return self.param_key, int(float(get_cfn_param(cfn_params, cfn_converter)))


class SpotBidPercentageParam(FloatParam):
    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}

        if parent_section_dict.get("scheduler") == "awsbatch":
            cfn_value = parent_section_dict.get("spot_bid_percentage")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})

        return cfn_params


class DesiredSizeParam(IntParam):
    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}

        if parent_section_dict.get("scheduler") == "awsbatch":
            cfn_value = parent_section_dict.get("desired_vcpus")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})
        else:
            cfn_value = parent_section_dict.get("initial_queue_size")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})

        return cfn_params


class MaxSizeParam(IntParam):
    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}

        if parent_section_dict.get("scheduler") == "awsbatch":
            cfn_value = parent_section_dict.get("max_vcpus")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})
        else:
            cfn_value = parent_section_dict.get("max_queue_size")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})

        return cfn_params


class MaintainInitialSizeParam(BoolParam):
    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}

        if parent_section_dict.get("scheduler") != "awsbatch":
            cfn_value = parent_section_dict.get("mantain_initial_size")
            min_size_value = parent_section_dict.get("initial_queue_size", "0") if cfn_value else "0"
            cfn_params.update({"MinSize": str(min_size_value)})

        return cfn_params


class MinSizeParam(IntParam):
    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}

        if parent_section_dict.get("scheduler") == "awsbatch":
            cfn_value = parent_section_dict.get("min_vcpus")
            cfn_params.update({self.param_map.get("cfn"): str(cfn_value)})

        return cfn_params


class SettingsParam(Param):

    def __init__(self, param_key, param_map):
        super().__init__(param_key, param_map)
        self.related_section_map = param_map.get("referred_section")
        self.related_section_key = self.related_section_map.get("key")
        self.related_section_type = self.related_section_map.get("type")

    def from_file(self, config_parser, parent_section_name):
        """
        From vpc_settings = a,b to vpc: [{label: a, ....}, {label: b, ....}]
        :param config_parser:
        :param parent_section_name:
        :return:
        """
        section_key = self.related_section_key
        section_type = self.related_section_type
        settings_dict = []

        try:
            param_value = config_parser.get(parent_section_name, self.param_key)
            if param_value:
                for section_label in param_value.split(','):
                    _, section_dict = section_type(
                        self.related_section_map, section_label.strip()
                    ).from_file(config_parser)
                    settings_dict.append(section_dict)
        except NoOptionError:
            param_value = self.param_map.get("default")
            if param_value:
                LOGGER.debug("Setting default value '{0}' for key '{1}'".format(param_value, self.param_key))
                return self.param_key, param_value
            pass
        except NoSectionError as e:
            LOGGER.error(e)
            raise e

        return section_key, settings_dict

    def to_file(self, config_parser, parent_section_dict, parent_section_name, param_value):
        sections = parent_section_dict.get(self.related_section_key, [])

        settings_param_created = False
        settings_param_value = ",".join(section_dict.get("label") for section_dict in sections)

        # create sections
        for section_dict in sections:

            for param_key, param_map in self.related_section_map.get("items").items():
                param_value = section_dict.get(param_key, None)

                if not settings_param_created and param_value != param_map.get("default", None):
                    # add "*_settings = *" to the parent section
                    # only if at least one value is different from the default one
                    config_parser.set(parent_section_name, self.param_key, settings_param_value)
                    settings_param_created = True

            self.related_section_type(
                self.related_section_map, section_dict.get("label")
            ).to_file(section_dict, config_parser)

    def to_cfn(self, parent_section_dict, pcluster_config):
        cfn_params = {}
        sections = parent_section_dict.get(self.related_section_key, [])
        for section_dict in sections:
            cfn_params.update(
                self.related_section_type(
                    self.related_section_map, section_dict.get("label")
                ).to_cfn(section_dict, pcluster_config)
            )
        return cfn_params

    def validate(self, param_value, parent_section_dict, pcluster_dict):
        # do not validate parameter but validate related sections
        sections = parent_section_dict.get(self.related_section_key, [])
        for section_dict in sections:
            self.related_section_type(
                self.related_section_map, section_dict.get("label")
            ).validate(section_dict, pcluster_dict)

    def from_cfn(self, cfn_params):
        sections = []

        # TODO fixme the label if available
        label = "{0}1".format(self.related_section_key)
        section_key, section_dict = self.related_section_type(self.related_section_map, label).from_cfn(cfn_params)
        sections.append(section_dict)

        return section_key, sections


class EBSSettingsParam(SettingsParam):

    def to_cfn(self, parent_section_dict, pcluster_config):
        """
        Convert a list of sections to multiple cfn params.

        :param parent_section_dict:
        :return:
        """
        cfn_params = {}
        sections = parent_section_dict.get(self.related_section_key, [])

        max_number_of_ebs_volumes = 5

        if sections:
            number_of_ebs_volumes = len(sections)
            for param_key, param_map in self.related_section_map.get("items").items():
                param = param_map.get("type", Param)(param_key, param_map)

                cfn_value_list = [param.to_cfn_value(section_dict.get(param_key)) for section_dict in sections]
                # add missing items until the max
                cfn_value_list.extend([param.to_cfn_value(None)] * (max_number_of_ebs_volumes - number_of_ebs_volumes))
                cfn_value = ",".join(cfn_value_list)

                cfn_converter = param_map.get("cfn", None)
                if cfn_converter:
                    cfn_params.update({cfn_converter: cfn_value})

            cfn_params.update({"NumberOfEBSVol": str(number_of_ebs_volumes)})

        return cfn_params

    def from_cfn(self, cfn_params):
        sections = []

        num_of_ebs = int(get_cfn_param(cfn_params, "NumberOfEBSVol"))
        for index in range(num_of_ebs):
            configured_params = False
            label = "{0}{1}".format(self.related_section_key, str(index + 1))
            section_dict = {"label": label}
            # TODO fixme the label if available

            for param_key, param_map in self.related_section_map.get("items").items():
                cfn_converter = param_map.get("cfn", None)
                if cfn_converter:

                    param_type = param_map.get("type", Param)
                    cfn_value = get_cfn_param(cfn_params, cfn_converter).split(",")[index]
                    item_value = param_type(param_key, param_map).from_cfn_value(cfn_value)
                    section_dict[param_key] = item_value

                    if item_value != param_map.get("default", None):
                        configured_params = True

            if configured_params:
                sections.append(section_dict)

        return self.related_section_key, sections


class Section(object):

    def __init__(self, section_map, section_label=None):
        self.section_map = section_map
        self.section_key = section_map.get("key")
        self.section_label = section_label

    def __get_section_name(self):
        return self.section_key + (" {0}".format(self.section_label) if self.section_label else "")

    def from_file(self, config_parser):
        """
        Convert a section from the config_parser to the internal representation (dictionary).

        Example: [vpc test] --> vpc: { "label": "test", "vpc_id": ... }

        :param config_parser: ConfigParser object
        :return: the generated dictionary
        """
        section_dict = {}
        if self.section_label:
            section_dict["label"] = self.section_label

        section_map_items = self.section_map.get("items")
        section_name = self.__get_section_name()

        for param_key, param_map in section_map_items.items():
            param_type = param_map.get("type", Param)

            item_key, item_value = param_type(param_key, param_map).from_file(config_parser, section_name)
            section_dict[item_key] = item_value

            not_valid_keys = [key for key, value in config_parser.items(section_name) if key not in section_map_items]

            if not_valid_keys:
                fail(
                    "The configuration parameters '{0}' are not allowed in the [{1}] section".format(
                        ",".join(not_valid_keys), section_name
                    )
                )

        return self.section_key, section_dict

    def validate(self, section_dict, pcluster_dict):
        if section_dict:
            section_name = self.__get_section_name()

            # validate section
            validation_func = self.section_map.get("validator", None)
            if validation_func:
                errors, warnings = validation_func(section_name, section_dict, pcluster_dict)
                if errors:
                    fail("The section [{0}] is wrongly configured\n{1}".format(section_name, "\n".join(errors)))
                elif warnings:
                    warn("The section [{0}] is wrongly configured\n{1}".format(section_name, "\n".join(warnings)))
                else:
                    LOGGER.debug("Configuration section '{0}' is valid".format(section_name))
            else:
                LOGGER.debug("Configuration section '[{0}]' has not validators".format(section_name))  # TODO remove

            # validate items
            for param_key, param_map in self.section_map.get("items").items():
                param_value = section_dict.get(param_key, None)

                param_type = param_map.get("type", Param)
                param_type(param_key, param_map).validate(param_value, section_dict, pcluster_dict)

    def to_file(self, section_dict, config_parser):

        config_section_name = self.__get_section_name()
        config_section_created = False

        for param_key, param_map in self.section_map.get("items").items():
            param_value = section_dict.get(param_key, None)

            if not config_section_created and param_value != param_map.get("default", None):
                # write section in the config file only if at least one parameter value is different by the default
                try:
                    config_parser.add_section(config_section_name)
                except DuplicateSectionError:
                    LOGGER.debug("Section '{0}' is already present in the file.".format(config_section_name))
                    pass
                config_section_created = True

            param_type = param_map.get("type", Param)
            param_type(param_key, param_map).to_file(config_parser, section_dict, config_section_name, param_value)

    def to_cfn(self, section_dict, pcluster_config):
        cfn_params = {}
        #if section_dict:
        cfn_converter = self.section_map.get("cfn", None)
        if cfn_converter:
            # it is a section converted to a single CFN parameter
            cfn_items = [
                param_map.get("type", Param)(param_key, param_map).to_cfn_value(section_dict.get(param_key))
                for param_key, param_map in self.section_map.get("items").items()
            ]

            if cfn_items[0] == "NONE":
                # first item is NONE --> set all values to NONE
                cfn_items = ["NONE"] * len(cfn_items)

            cfn_params.update({cfn_converter: ",".join(cfn_items)})
        else:
            # get value from config object
            for param_key, param_map in self.section_map.get("items").items():
                param_type = param_map.get("type", Param)
                cfn_params.update(param_type(param_key, param_map).to_cfn(section_dict, pcluster_config))
        return cfn_params

    def from_cfn(self, cfn_params):

        # TODO get the label if saved in cfn
        section_dict = {}
        label = "{0}1".format(self.section_key)
        label_added = False

        cfn_converter = self.section_map.get("cfn", None)
        if cfn_converter:
            # It is a section converted to a single CFN parameter
            cfn_values = get_cfn_param(cfn_params, cfn_converter).split(",")

            cfn_param_index = 0
            for param_key, param_map in self.section_map.get("items").items():
                try:
                    cfn_value = cfn_values[cfn_param_index]
                except IndexError:
                    # This happen if the expected comma separated CFN param doesn't exist in the Stack,
                    # so it is set to a single NONE value
                    cfn_value = "NONE"

                param_type = param_map.get("type", Param)
                item_value = param_type(param_key, param_map).from_cfn_value(cfn_value)

                if not label_added and item_value != param_map.get("default", None):
                    # add "label" to the section dict
                    # only if at least one value is different from the default one
                    section_dict["label"] = label
                    label_added = True

                section_dict[param_key] = item_value
                cfn_param_index += 1
        else:
            for param_key, param_map in self.section_map.get("items").items():
                param_type = param_map.get("type", Param)
                item_key, item_value = param_type(param_key, param_map).from_cfn(cfn_params)
                section_dict[item_key] = item_value

        return self.section_key, section_dict


class EFSSection(Section):

    def to_cfn(self, section_dict, pcluster_config):

        cfn_params = {}
        #if section_dict:
        # it is a section converted to a single CFN parameter
        cfn_converter = self.section_map.get("cfn", None)
        cfn_items = [
            param_map.get("type", Param)(param_key, param_map).to_cfn_value(section_dict.get(param_key))
            for param_key, param_map in self.section_map.get("items").items()
        ]

        if cfn_items[0] == "NONE":
            # first item is NONE --> set all values to NONE
            cfn_items = ["NONE"] * len(cfn_items)
        cfn_value = ",".join(cfn_items)

        # latest CFN param will identify if create or no a Mount Target for the given EFS FS Id
        master_avail_zone = pcluster_config.get_master_avail_zone()
        mount_target_id = get_efs_mount_target_id(
            efs_fs_id=section_dict.get("efs_fs_id"), avail_zone=master_avail_zone
        )
        cfn_value += ",{0}".format("Valid" if mount_target_id else "NONE")

        cfn_params.update({cfn_converter: cfn_value})
        return cfn_params


class ClusterSection(Section):

    def from_cfn(self, cfn_params):
        section_dict = {"label": get_cfn_param(cfn_params, "CLITemplate")}

        for param_key, param_map in self.section_map.get("items").items():
            param_type = param_map.get("type", Param)
            item_key, item_value = param_type(param_key, param_map).from_cfn(cfn_params)
            section_dict[item_key] = item_value

        return self.section_key, section_dict


def get_default_param(section_map, param_key):
    param_map = section_map.get("items").get(param_key, None)
    return param_map.get("default", None) if param_map else None
