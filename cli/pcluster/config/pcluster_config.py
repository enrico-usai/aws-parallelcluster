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
import configparser
import errno
import inspect
import logging
import os
import stat

import boto3

from pcluster.config.mapping import get_section_type, AWS, CLUSTER, ALIASES, GLOBAL
from pcluster.utils import fail

LOGGER = logging.getLogger(__name__)


class PclusterConfig(object):
    """Manage ParallelCluster Config."""
    def __init__(
            self,
            config_file=None,
            file_sections=[AWS],
            cluster_label=None,  # args.cluster_template
            region=None,
            cluster_name=None,
            fail_on_config_file_absence=False,
    ):
        self.sections = {}

        # always parse the configuration file if there, to get AWS section
        self._init_config_parser(config_file, fail_on_config_file_absence)
        # init AWS section
        section_type = get_section_type(AWS)
        section = section_type(AWS, pcluster_config=self, config_parser=self.config_parser, fail_on_absence=False)
        self.add_section(section)
        self.__init_region(region)
        self.__init_aws_credentials()

        # init pcluster_config object, from cfn or from config_file
        if cluster_name:
            self.__from_cfn(cluster_name)
        else:
            self.__from_file(file_sections, cluster_label, self.config_parser, fail_on_config_file_absence)

        self.__validate()

    def _init_config_parser(self, config_file, fail_on_config_file_absence=True):
        """
        Parse the config file and initialize config_file and config_parser attributes
        :param config_file: The config file to parse
        """
        if config_file:
            self.config_file = config_file
            default_config = False
        elif "AWS_PCLUSTER_CONFIG_FILE" in os.environ:
            self.config_file = os.environ["AWS_PCLUSTER_CONFIG_FILE"]
            default_config = False
        else:
            config_file = os.path.expanduser(os.path.join("~", ".parallelcluster", "config"))
            default_config = True

        self.config_file = (
            config_file if config_file else os.path.expanduser(os.path.join("~", ".parallelcluster", "config"))
        )

        if not os.path.isfile(self.config_file):
            if fail_on_config_file_absence:
                error_message = "Configuration file {0} not found."
                if default_config:
                    error_message += (
                        "\nYou can copy a template from {1}{2}examples{2}config "
                        "or execute the 'pcluster configure' command".format(
                            self.config_file,
                            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
                            os.path.sep,
                        )
                    )
                fail(error_message)
            else:
                LOGGER.debug("Specified configuration file {0} doesn't exist.".format(self.config_file))
        else:
            LOGGER.debug("Parsing configuration file %s", self.config_file)
        self.config_parser = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
        self.config_parser.read(self.config_file)

    def get_sections(self, section_key):
        """
        Get the sections identified by the given key.

        :param section_key: the identifier of the section type
        """
        return self.sections.get(section_key, {})

    def get_section(self, section_key, section_label=None):
        """
        Get the section identified by the given key and label.

        :param section_key: the identifier of the section type
        :param section_label: the label of the section, returns the first section if empty.
        """
        if section_label:
            section = self.get_sections(section_key).get(section_label, None)
        else:
            sections = self.get_sections(section_key)
            section = next(iter(sections.values()), None) if sections else None
        return section

    def add_section(self, section):
        """Add a section to the PclusterConfig object."""
        if section.key not in self.sections:
            self.sections[section.key] = {}
        self.sections[section.key][section.label if section.label else "default"] = section

    def __init_aws_credentials(self):
        # set credentials in th environment to be available for all the boto3 calls
        os.environ["AWS_DEFAULT_REGION"] = self.region

        # Init credentials by checking if they have been provided in config
        try:
            aws_section = self.get_section("aws")
            aws_access_key_id = aws_section.get_param_value("aws_access_key_id")
            if aws_access_key_id:
                os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id

            aws_secret_access_key = aws_section.get_param_value("aws_secret_access_key")
            if aws_secret_access_key:
                os.environ["AWS_SECRET_ACCESS_KEY"] = aws_secret_access_key
        except AttributeError:
            # If there is no aws configuration
            pass

    def __init_region(self, region=None):
        """
        Evaluate region to use.

        Order is 1) explicit request 2) AWS_DEFAULT_REGION env 3) Config file 4) us-east-1
        """
        if region:
            self.region = region
        elif os.environ.get("AWS_DEFAULT_REGION"):
            self.region = os.environ.get("AWS_DEFAULT_REGION")
        else:
            self.region = self.get_section("aws").get_param_value("aws_region_name")

    def to_file(self):
        """
        Convert the internal representation of the cluster to the file sections.

        NOTE: aws, global, aliases sections will be excluded from this transformation.
        """
        self.get_section("cluster").to_file(self.config_parser)

        # ensure that the directory for the config file exists
        if not os.path.isfile(self.config_file):
            try:
                config_folder = os.path.dirname(self.config_file) or "."
                os.makedirs(config_folder)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise  # can safely ignore EEXISTS for this purpose...

            # Fix permissions
            with open(self.config_file, "a"):
                os.chmod(self.config_file, stat.S_IRUSR | stat.S_IWUSR)

        # Write configuration to disk
        with open(self.config_file, "w") as cf:
            self.config_parser.write(cf)

    def to_cfn(self):
        """
        Convert the internal representation of the cluster to a list of CFN parameters.

        :return: the region, the template_url,
        the list of cfn parameters associated with the given configuration and the tags
        """
        cluster_section = self.get_section("cluster")
        cfn_params = cluster_section.to_cfn()
        template_url = cluster_section.get_param_value("template_url")
        tags = cluster_section.get_param_value("tags")

        return self.region, template_url, cfn_params, tags

    def __from_file(self, file_sections, cluster_label=None, config_parser=None, fail_on_cluster_config_absence=False):
        if ALIASES in file_sections:
            section_type = get_section_type(ALIASES)
            section = section_type(ALIASES, pcluster_config=self, config_parser=config_parser, fail_on_absence=False)
            self.add_section(section)

        if GLOBAL in file_sections:
            section_type = get_section_type(GLOBAL)
            section = section_type(GLOBAL, pcluster_config=self, config_parser=config_parser, fail_on_absence=False)
            self.add_section(section)
            # FIXME it could initializes also CLUSTER

        # get cluster by cluster_label
        if CLUSTER in file_sections:
            if not cluster_label:
                cluster_label = self.get_section("global").get_param_value("cluster_template") if self.get_section("global") else None
            section_type = get_section_type(CLUSTER)
            section = section_type(CLUSTER, pcluster_config=self, section_label=cluster_label, config_parser=config_parser, fail_on_absence=fail_on_cluster_config_absence)
            self.add_section(section)

    def __from_cfn(self, cluster_name):
        stack_name = "parallelcluster-" + cluster_name

        cfn_client = boto3.client("cloudformation", region_name=self.region)
        stack = cfn_client.describe_stacks(StackName=stack_name).get("Stacks")[0]

        section_type = get_section_type(CLUSTER)
        section = section_type(CLUSTER, pcluster_config=self, cfn_params=stack.get("Parameters", []))
        self.add_section(section)

    def __validate(self):
        fail_on_error = self.get_section("global").get_param_value("sanity_check") if self.get_section("global") else True

        for section_key, sections in self.sections.items():
            for section_label, section in sections.items():
                section.validate(fail_on_error=fail_on_error)

    def get_master_avail_zone(self):
        """
        Get the Availability zone of the Master Subnet, by searching in pcluster_config dictionary

        :return: master avail zone
        """
        master_subnet_id = self.get_section("vpc").get_param_value("master_subnet_id")
        master_avail_zone = (
            boto3.client("ec2").describe_subnets(SubnetIds=[master_subnet_id]).get("Subnets")[0].get("AvailabilityZone")
        )
        return master_avail_zone
