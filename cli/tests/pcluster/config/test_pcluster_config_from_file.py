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

import pytest
from assertpy import assert_that

from pcluster.config.mapping import CLUSTER, EBS, EFS, FSX, SCALING, RAID, VPC
from tests.pcluster.config.utils import get_param_map
from tests.pcluster.config.defaults import DefaultDict
from pcluster.config.pcluster_config import PclusterConfig


def _assert_param_from_file(section_map, param_key, param_value, expected_value, expected_message):
    section_label = section_map.get("label")
    section_name = "{0} {1}".format(section_map.get("key"), section_label)
    config_parser = configparser.ConfigParser()
    config_parser.add_section(section_name)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    if param_value:
        config_parser.set(section_name, param_key, param_value)

    param_map, param_type = get_param_map(section_map, param_key)

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            param_type(section_map.get("key"), section_label, param_key, param_map, pcluster_config, config_parser=config_parser)
    else:
        param = param_type(section_map.get("key"), section_label, param_key, param_map, pcluster_config, config_parser=config_parser)
        assert_that(param.value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "param_key, param_value, expected_value, expected_message",
    [
        ("scaledown_idletime", None, 10, None),
        ("scaledown_idletime", "", 10, None),
        ("scaledown_idletime", "NONE", None, "must be an Integer"),
        ("scaledown_idletime", "wrong_value", None, "must be an Integer"),
        ("scaledown_idletime", "10", 10, None),
        ("scaledown_idletime", "3", 3, None),
    ]
)
def test_scaling_param_from_file(param_key, param_value, expected_value, expected_message):
    _assert_param_from_file(SCALING, param_key, param_value, expected_value, expected_message)


@pytest.mark.parametrize(
    "param_key, param_value, expected_value, expected_message",
    [
        ("vpc_id", None, None, None),
        ("vpc_id", "", None, None),
        ("vpc_id", "wrong_value", None, "has an invalid value"),
        ("vpc_id", "vpc-12345", None, "has an invalid value"),
        ("vpc_id", "vpc-123456789", None, "has an invalid value"),
        ("vpc_id", "wrong_value", None, "has an invalid value"),
        ("vpc_id", "NONE", None, "has an invalid value"),
        ("vpc_id", "vpc-12345678", "vpc-12345678", None),
        ("vpc_id", "vpc-12345678901234567", "vpc-12345678901234567", None),
        ("master_subnet_id", None, None, None),
        ("master_subnet_id", "", None, None),
        ("master_subnet_id", "wrong_value", None, "has an invalid value"),
        ("master_subnet_id", "subnet-12345", None, "has an invalid value"),
        ("master_subnet_id", "subnet-123456789", None, "has an invalid value"),
        ("master_subnet_id", "wrong_value", None, "has an invalid value"),
        ("master_subnet_id", "NONE", None, "has an invalid value"),
        ("master_subnet_id", "subnet-12345678", "subnet-12345678", None),
        ("master_subnet_id", "subnet-12345678901234567", "subnet-12345678901234567", None),
        ("compute_subnet_id", None, None, None),
        ("compute_subnet_id", "", None, None),
        ("compute_subnet_id", "wrong_value", None, "has an invalid value"),
        ("compute_subnet_id", "subnet-12345", None, "has an invalid value"),
        ("compute_subnet_id", "subnet-123456789", None, "has an invalid value"),
        ("compute_subnet_id", "wrong_value", None, "has an invalid value"),
        ("compute_subnet_id", "NONE", None, "has an invalid value"),
        ("compute_subnet_id", "subnet-12345678", "subnet-12345678", None),
        ("compute_subnet_id", "subnet-12345678901234567", "subnet-12345678901234567", None),
    ]
)
def test_vpc_param_from_file(param_key, param_value, expected_value, expected_message):
    _assert_param_from_file(VPC, param_key, param_value, expected_value, expected_message)


@pytest.mark.parametrize(
    "param_key, param_value, expected_value, expected_message",
    [
        ("provisioned_throughput", "0.1", 0.1, None),
        ("provisioned_throughput", "3", 3, None),
        ("provisioned_throughput", "1024.9", 1024.9, None),
        ("provisioned_throughput", "102000", None, "has an invalid value"),
        ("provisioned_throughput", "0.01", None, "has an invalid value"),
        ("provisioned_throughput", "1025", None, "has an invalid value"),
        ("provisioned_throughput", "wrong_value", None, "must be a Float"),
    ]
)
def test_efs_param_from_file(param_key, param_value, expected_value, expected_message):
    _assert_param_from_file(EFS, param_key, param_value, expected_value, expected_message)


@pytest.mark.parametrize(
    "param_key, param_value, expected_value, expected_message",
    [
        # Param
        ("key_name", None, None, None),
        ("key_name", "", None, None),
        ("key_name", "test", "test", None),
        ("key_name", "NONE", "NONE", None),
        ("key_name", "fake_value", "fake_value", None),
        ("base_os", None, "alinux", None),
        ("base_os", "", "alinux", None),
        ("base_os", "wrong_value", None, "has an invalid value"),
        ("base_os", "NONE", None, "has an invalid value"),
        ("base_os", "alinux", "alinux", None),
        ("encrypted_ephemeral", None, False, None),
        ("encrypted_ephemeral", "", False, None),
        ("encrypted_ephemeral", "NONE", None, "must be a Boolean"),
        ("encrypted_ephemeral", "true", True, None),
        ("encrypted_ephemeral", "false", False, None),
        ("spot_bid_percentage", None, 0.0, None),
        ("spot_bid_percentage", "", 0.0, None),
        ("spot_bid_percentage", "NONE", None, "must be a Float"),
        ("spot_bid_percentage", "wrong_value", None, "must be a Float"),
        ("spot_bid_percentage", "0.0009", 0.0009, None),
        ("spot_bid_percentage", "0.0", 0.0, None),
        ("spot_bid_percentage", "10", 10, None),
        ("spot_bid_percentage", "3", 3, None),
        ("scaling_settings", "test1", None, "Section .* not found in the config file"),
        ("vpc_settings", "test1", None, "Section .* not found in the config file"),
        ("vpc_settings", "test1,test2", None, "is invalid. It can only contains a single .* section label"),
        ("vpc_settings", "test1, test2", None, "is invalid. It can only contains a single .* section label"),
        ("ebs_settings", "test1", None, "Section .* not found in the config file"),
        ("ebs_settings", "test1,test2", None, "Section .* not found in the config file"),
        ("ebs_settings", "test1, test2", None, "Section .* not found in the config file"),
    ]
)
def test_cluster_param_from_file(param_key, param_value, expected_value, expected_message):
    _assert_param_from_file(CLUSTER, param_key, param_value, expected_value, expected_message)


@pytest.mark.parametrize(
    "section_map, config_parser_dict, expected_dict_params, expected_message",
    [
        # default
        (CLUSTER, {"cluster default": {}}, {}, None),
        (SCALING, {"scaling default": {}}, {}, None),
        (VPC, {"vpc default": {}}, {}, None),
        (EBS, {"ebs default": {}}, {}, None),
        (EFS, {"efs default": {}}, {}, None),
        (RAID, {"raid default": {}}, {}, None),
        (FSX, {"fsx default": {}}, {}, None),
        # right value
        (CLUSTER, {"cluster default": {"key_name": "test"}}, {"key_name": "test"}, None),
        (CLUSTER, {"cluster default": {"base_os": "alinux"}}, {"base_os": "alinux"}, None),
        # invalid value
        (CLUSTER, {"cluster default": {"base_os": "wrong_value"}}, None, "has an invalid value"),
        # invalid key
        (
                CLUSTER,
                {"cluster default": {"invalid_key": "fake_value"}},
                None,
                "'invalid_key' are not allowed in the .* section"
        ),
        (CLUSTER, {"cluster default": {"invalid_key": "fake_value", "invalid_key2": "fake_value"}}, None,
         "'invalid_key,invalid_key2' are not allowed in the .* section"),
        (
                SCALING,
                {"scaling default": {"invalid_key": "fake_value"}},
                None,
                "'invalid_key' are not allowed in the .* section"
        ),
        (VPC, {"vpc default": {"invalid_key": "fake_value"}}, None, "'invalid_key' are not allowed in the .* section"),
        (EBS, {"ebs default": {"invalid_key": "fake_value"}}, None, "'invalid_key' are not allowed in the .* section"),
        (EFS, {"efs default": {"invalid_key": "fake_value"}}, None, "'invalid_key' are not allowed in the .* section"),
        (
                RAID,
                {"raid default": {"invalid_key": "fake_value"}},
                None,
                "'invalid_key' are not allowed in the .* section"
        ),
        (FSX, {"fsx default": {"invalid_key": "fake_value"}}, None, "'invalid_key' are not allowed in the .* section"),
    ]
)
def test_section_from_file(section_map, config_parser_dict, expected_dict_params, expected_message):
    config_parser = configparser.ConfigParser()
    config_parser.read_dict(config_parser_dict)

    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    expected_dict = default_dict.copy()
    if isinstance(expected_dict_params, dict):
        expected_dict.update(expected_dict_params)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    section_type = section_map.get("type")
    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _ = section_type(section_map, pcluster_config, config_parser=config_parser)
    else:
        section = section_type(section_map, pcluster_config, config_parser=config_parser)
        section_dict = {}
        for param_key, param in section.params.items():
            section_dict.update({param_key: param.value})

        assert_that(section_dict).is_equal_to(expected_dict)
