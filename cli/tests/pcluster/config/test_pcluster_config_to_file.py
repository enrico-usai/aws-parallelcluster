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
from configparser import NoOptionError

import pytest
from assertpy import assert_that

from pcluster.config.mapping import CLUSTER, EBS, EFS, FSX, SCALING, RAID, VPC
from tests.pcluster.config.defaults import DefaultDict
from tests.pcluster.config.utils import get_param_map


@pytest.mark.parametrize(
    "section_map, param_key, param_value, expected_value",
    [
        # Param
        (CLUSTER, "key_name", None, None),
        (CLUSTER, "key_name", "test", "test"),
        (CLUSTER, "key_name", "NONE", "NONE"),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", None, None),
        (CLUSTER, "encrypted_ephemeral", False, None),
        (CLUSTER, "encrypted_ephemeral", True, "true"),
        # IntParam
        (SCALING, "scaledown_idletime", None, None),
        (SCALING, "scaledown_idletime", 10, None),
        (SCALING, "scaledown_idletime", 3, "3"),
    ]
)
def test_param_to_file(section_map, param_key, param_value, expected_value):
    section_name = section_map.get("key")
    config_parser = configparser.ConfigParser()
    config_parser.add_section(section_name)

    param_map, param_type = get_param_map(section_map, param_key)
    param_value = param_value or param_map.get("default")
    section_dict = {section_name: {param_key: param_value}}
    param_type(param_key, param_map).to_file(config_parser, section_dict, section_name, param_value)

    if expected_value:
        assert_that(config_parser.has_option(section_name, param_key))
        assert_that(config_parser.get(section_name, param_key)).is_equal_to(expected_value)
    else:
        assert_that(config_parser.has_option(section_name, param_key)).is_false()


@pytest.mark.parametrize(
    "section_map, section_dict, expected_config_parser_dict, expected_message",
    [
        # default
        (CLUSTER, {}, {"cluster default": {}}, None),
        (SCALING, {}, {"scaling default": {}}, None),
        (VPC, {}, {"vpc default": {}}, None),
        (EBS, {}, {"ebs default": {}}, None),
        (EFS, {}, {"efs default": {}}, None),
        (RAID, {}, {"raid default": {}}, None),
        (FSX, {}, {"fsx default": {}}, None),
        # default values
        (CLUSTER, {"base_os": "alinux"}, {"cluster default": {"base_os": "alinux"}}, "No option .* in section: .*"),
        # other values
        (CLUSTER, {"key_name": "test"}, {"cluster default": {"key_name": "test"}}, None),
        (CLUSTER, {"base_os": "centos7"}, {"cluster default": {"base_os": "centos7"}}, None),
    ]
)
def test_section_to_file(section_map, section_dict, expected_config_parser_dict, expected_message):
    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    input_section_dict = default_dict.copy()
    if isinstance(section_dict, dict):
        input_section_dict.update(section_dict)

    expected_config_parser = configparser.ConfigParser()
    expected_config_parser.read_dict(expected_config_parser_dict)

    output_config_parser = configparser.ConfigParser()
    section_type = section_map.get("type")
    section_type(section_map).to_file(input_section_dict, output_config_parser)

    for section_key, section_params in expected_config_parser_dict.items():
        for param_key, param_value in section_params.items():

            assert_that(output_config_parser.has_option(section_key, param_key))
            if expected_message is not None:
                with pytest.raises(NoOptionError, match=expected_message):
                    assert_that(output_config_parser.get(section_key, param_key)).is_equal_to(param_value)
            else:
                assert_that(output_config_parser.get(section_key, param_key)).is_equal_to(param_value)
