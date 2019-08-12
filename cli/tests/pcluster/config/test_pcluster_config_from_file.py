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


@pytest.mark.parametrize(
    "section_map, param_key, param_value, expected_value, expected_message",
    [
        # Param
        (CLUSTER, "key_name", None, None, None),
        (CLUSTER, "key_name", "", None, None),
        (CLUSTER, "key_name", "test", "test", None),
        (CLUSTER, "key_name", "NONE", "NONE", None),
        (CLUSTER, "key_name", "fake_value", "fake_value", None),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", None, False, None),
        (CLUSTER, "encrypted_ephemeral", "", False, None),
        (CLUSTER, "encrypted_ephemeral", "NONE", None, "must be a Boolean"),
        (CLUSTER, "encrypted_ephemeral", "true", True, None),
        (CLUSTER, "encrypted_ephemeral", "false", False, None),
        # IntParam
        (SCALING, "scaledown_idletime", None, 10, None),
        (SCALING, "scaledown_idletime", "", 10, None),
        (SCALING, "scaledown_idletime", "NONE", None, "must be an Integer"),
        (SCALING, "scaledown_idletime", "wrong_value", None, "must be an Integer"),
        (SCALING, "scaledown_idletime", "10", 10, None),
        (SCALING, "scaledown_idletime", "3", 3, None),
        # SpotBidPercentageParam --> FloatParam
        (CLUSTER, "spot_bid_percentage", None, 0.0, None),
        (CLUSTER, "spot_bid_percentage", "", 0.0, None),
        (CLUSTER, "spot_bid_percentage", "NONE", None, "must be a Float"),
        (CLUSTER, "spot_bid_percentage", "wrong_value", None, "must be a Float"),
        (CLUSTER, "spot_bid_percentage", "0.0009", 0.0009, None),
        (CLUSTER, "spot_bid_percentage", "0.0", 0.0, None),
        (CLUSTER, "spot_bid_percentage", "10", 10, None),
        (CLUSTER, "spot_bid_percentage", "3", 3, None),
        # SettingsParam
        (CLUSTER, "vpc_settings", "test1", None, "Section .* not found in the config file"),
        (CLUSTER, "vpc_settings", "test1,test2", None, "is invalid. It can only contains a single .* section label"),
        (CLUSTER, "vpc_settings", "test1, test2", None, "is invalid. It can only contains a single .* section label"),
    ]
)
def test_param_from_file(section_map, param_key, param_value, expected_value, expected_message):
    section_name = section_map.get("key")
    config_parser = configparser.ConfigParser()
    config_parser.add_section(section_name)

    if param_value:
        config_parser.set(section_name, param_key, param_value)

    param_map, param_type = get_param_map(section_map, param_key)

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _, param_value = param_type(param_key, param_map).from_file(config_parser, section_name)
    else:
        _, param_value = param_type(param_key, param_map).from_file(config_parser, section_name)
        assert_that(param_value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "section_map, config_parser_dict, expected_dict_keys, expected_message",
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
def test_section_from_file(section_map, config_parser_dict, expected_dict_keys, expected_message):
    config_parser = configparser.ConfigParser()
    config_parser.read_dict(config_parser_dict)

    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    expected_dict = default_dict.copy()
    if isinstance(expected_dict_keys, dict):
        expected_dict.update(expected_dict_keys)

    section_type = section_map.get("type")
    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _, section_dict = section_type(section_map).from_file(config_parser)
    else:
        _, section_dict = section_type(section_map).from_file(config_parser)
        assert_that(section_dict).is_equal_to(expected_dict)
