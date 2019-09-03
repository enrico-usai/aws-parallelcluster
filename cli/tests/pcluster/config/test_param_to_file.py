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
from pcluster.config.mapping import CLUSTER, EBS, EFS, FSX, RAID, SCALING, VPC
from pcluster.config.pcluster_config import PclusterConfig
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
        # JsonParam
        (CLUSTER, "extra_json", None, None),
        (CLUSTER, "extra_json", {}, {}),
        (
                CLUSTER,
                "extra_json",
                {"cluster": {"cfn_scheduler_slots": "cores"}},
                "{'cluster': {'cfn_scheduler_slots': 'cores'}}",
        ),
    ],
)
def test_param_to_file(section_map, param_key, param_value, expected_value):
    section_label = "default"
    section_name = section_map.get("key") + " " + section_label
    config_parser = configparser.ConfigParser()
    config_parser.add_section(section_name)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    param_map, param_type = get_param_map(section_map, param_key)
    param = param_type(section_map.get("key"), section_label, param_key, param_map, pcluster_config)
    param.value = param_value or param_map.get("default")
    param.to_file(config_parser)

    if expected_value:
        assert_that(config_parser.has_option(section_name, param_key))
        assert_that(config_parser.get(section_name, param_key)).is_equal_to(expected_value)
    else:
        assert_that(config_parser.has_option(section_name, param_key)).is_false()