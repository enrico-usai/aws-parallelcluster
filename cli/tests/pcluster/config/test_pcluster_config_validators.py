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
import pytest
import configparser

from pcluster.config.mapping import CLUSTER, EBS, EFS, FSX, SCALING, RAID, VPC
from tests.pcluster.config.utils import get_param_map
from tests.pcluster.config.defaults import DefaultDict
from pcluster.config.pcluster_config import PclusterConfig


@pytest.mark.parametrize(
    "section_map, param_key, config_parser_dict, expected_message",
    [
        (VPC, "vpc_id", {"vpc default": {"vpc_id": "wrong_value"}}, ".* has an invalid value .*"),
        (VPC, "master_subnet_id", {"vpc default": {"master_subnet_id": "wrong_value"}}, ".* has an invalid value .*"),
        (VPC, "ssh_from", {"vpc default": {"ssh_from": "wrong_value"}}, ".* has an invalid value .*"),
        (VPC, "additional_sg", {"vpc default": {"additional_sg": "wrong_value"}}, ".* has an invalid value .*"),
        (VPC, "compute_subnet_id", {"vpc default": {"compute_subnet_id": "wrong_value"}}, ".* has an invalid value .*"),
        (VPC, "compute_subnet_cidr", {"vpc default": {"compute_subnet_cidr": "wrong_value"}}, ".* has an invalid value .*"),
        (VPC, "use_public_ips", {"vpc default": {"use_public_ips": "wrong_value"}}, ".* must be a Boolean"),
        (VPC, "vpc_security_group_id", {"vpc default": {"vpc_security_group_id": "wrong_value"}}, ".* has an invalid value .*"),
    ]
)
def test_param_validator(section_map, param_key, config_parser_dict, expected_message):
    param_map, param_type = get_param_map(section_map, param_key)
    pcluster_config = PclusterConfig(config_file="wrong-file")

    config_parser = configparser.ConfigParser()
    config_parser.read_dict(config_parser_dict)

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config, config_parser=config_parser).validate()
    else:
        param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config, config_parser=config_parser).validate()
