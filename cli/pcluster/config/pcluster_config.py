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
from configparser import NoSectionError

import boto3
import pkg_resources

from pcluster.config.mapping import AWS, GLOBAL, ALIASES, CLUSTER
from pcluster.config.params_types import Section, ClusterSection
from pcluster.utils import fail

LOGGER = logging.getLogger(__name__)

class PclusterConfig(object):
    """Manage ParallelCluster Config."""
    def __init__(
            self,
            config_file=None,
            file_sections=[AWS, GLOBAL],
            cluster_label=None,  # args.cluster_template
            region=None,
            cluster_name=None,
            fail_on_config_file_absence=False,
    ):
        # always parse the configuration file if there, to get AWS section
        self._init_config_parser(config_file, fail_on_config_file_absence)
        # init AWS section
        self.__init_section_dict(self.config_parser, AWS)
        self.__init_region(region)
        self.__init_aws_credentials()

        # init pcluster_config object, from cfn or from config_file
        if cluster_name:
            self.__from_cfn(cluster_name)
        else:
            self.__from_file(file_sections, cluster_label, self.config_parser)

    def _init_config_parser(self, config_file, fail_on_config_file_absence=True):
        """
        Parse the config file and initialize config_file and config_parser attributes
        :param config_file: The config file to parse
        """
        self.config_file = (
            config_file if config_file else os.path.expanduser(os.path.join("~", ".parallelcluster", "config"))
        )
        if not os.path.isfile(self.config_file):
            if fail_on_config_file_absence:
                fail(
                    "Config file {0} not found.\n"
                    "You can copy a template from {1}{2}examples{2}config "
                    "or execute the 'pcluster configure' command".format(
                        self.config_file,
                        os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
                        os.path.sep,
                    )
                )
            else:
                LOGGER.debug("Configuration file doesn't exist. %s", self.config_file)
        else:
            LOGGER.debug("Parsing configuration file %s", self.config_file)
        self.config_parser = configparser.ConfigParser(inline_comment_prefixes=("#", ";"))
        self.config_parser.read(self.config_file)

    def get_section(self, section_name, default_value=None):
        """Get the PclusterConfig attribute"""
        return getattr(self, section_name, default_value)

    def __init_aws_credentials(self):
        # set credentials in th environment to be available for all the boto3 calls
        os.environ["AWS_DEFAULT_REGION"] = self.region

        # Init credentials by checking if they have been provided in config
        try:
            aws_access_key_id = self.get_section("aws").get("aws_access_key_id", None)
            if aws_access_key_id:
                os.environ["AWS_ACCESS_KEY_ID"] = aws_access_key_id

            aws_secret_access_key = self.get_section("aws").get("aws_secret_access_key", None)
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
            self.region = self.get_section("aws").get("aws_region_name")

    def __init_section_dict(self, config_parser, section_map, section_label=None, fail_on_absence=False):
        #try:
        section_type = section_map.get("type", Section)
        section_key, section_value = section_type(section_map, section_label).from_file(config_parser, fail_on_absence)
        #except NoSectionError as e:
            #LOGGER.info(e)
            #section_key, section_value = section_type(section_map, section_label).from_map()
            #pass
        setattr(self, section_key, section_value)

    def to_file(self):
        """
        Convert the internal representation of the cluster to the file sections.

        NOTE: aws, global, aliases sections will be excluded from this transformation.
        """
        self.__validate([CLUSTER])

        ClusterSection(CLUSTER, self.get_section("cluster").get("label")).to_file(self.get_section("cluster"), self.config_parser)

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
        # validate PclusterConfig object
        self.__validate([CLUSTER])
        cluster_config = self.get_section("cluster")

        params = ClusterSection(
            CLUSTER, cluster_config.get("label")
        ).to_cfn(section_dict=cluster_config, pcluster_config=self)

        return self.region, cluster_config.get("template_url"), params, cluster_config.get("tags")

    def __from_file(self, file_sections, cluster_label=None, config_parser=None):
        if GLOBAL in file_sections:
            self.__init_section_dict(config_parser, GLOBAL)
        if ALIASES in file_sections:
            self.__init_section_dict(config_parser, ALIASES)

        # get cluster by cluster_label
        if CLUSTER in file_sections:
            if not cluster_label:
                cluster_label = self.get_section("global").get("cluster_template")

            self.__init_section_dict(config_parser, CLUSTER, cluster_label)

    def __from_cfn(self, cluster_name):
        stack_name = "parallelcluster-" + cluster_name

        cfn_client = boto3.client("cloudformation", region_name=self.region)
        stack = cfn_client.describe_stacks(StackName=stack_name).get("Stacks")[0]

        section_key, section_dict = ClusterSection(CLUSTER).from_cfn(stack.get("Parameters", []))
        setattr(self, section_key, section_dict)

    def __validate(self, file_sections):
        fail_on_error = self.get_section("global").get("sanity_check")

        for section_map in file_sections:
            section_key = section_map.get("key")
            section_type = section_map.get("type", Section)
            section_label = self.get_section(section_key).get("label", None)
            section_type(
                section_map, section_label
            ).validate(section_dict=self.get_section(section_key, None), pcluster_dict=self, fail_on_error=fail_on_error)

    def get_master_avail_zone(self):
        """
        Get the Availability zone of the Master Subnet, by searching in pcluster_config dictionary

        :return: master avail zone
        """
        master_subnet_id = self.get_section("cluster").get("vpc")[0].get("master_subnet_id")
        master_avail_zone = (
            boto3.client("ec2").describe_subnets(SubnetIds=[master_subnet_id]).get("Subnets")[0].get("AvailabilityZone")
        )
        return master_avail_zone
