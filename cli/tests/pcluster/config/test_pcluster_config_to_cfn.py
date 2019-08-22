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

from pcluster.config.mapping import CLUSTER, SCALING
from pcluster.config.pcluster_config import PclusterConfig
from tests.pcluster.config.utils import get_param_map


@pytest.mark.parametrize(
    "section_map, param_key, param_value, expected_value",
    [
        # Param
        (CLUSTER, "key_name", None, "NONE"),
        (CLUSTER, "key_name", "test", "test"),
        (CLUSTER, "key_name", "NONE", "NONE"),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", None, "false"),
        (CLUSTER, "encrypted_ephemeral", True, "true"),
        (CLUSTER, "encrypted_ephemeral", False, "false"),
        # IntParam
        (SCALING, "scaledown_idletime", 10, "10"),
        (SCALING, "scaledown_idletime", 10, "10"),
        (SCALING, "scaledown_idletime", 3, "3"),
        # SpotBidPercentageParam --> FloatParam
        (CLUSTER, "spot_bid_percentage", None, "0.0"),
        (CLUSTER, "spot_bid_percentage", 0.0009, "0.0009"),
        (CLUSTER, "spot_bid_percentage", 0.0, "0.0"),
        (CLUSTER, "spot_bid_percentage", 10, "10"),
        (CLUSTER, "spot_bid_percentage", 3, "3"),
        # SharedDirParam
        (CLUSTER, "shared_dir", "test", "test"),
        (CLUSTER, "shared_dir", None, "/shared"),
    ]
)
def test_param_to_cfn_value(section_map, param_key, param_value, expected_value):
    pcluster_config = PclusterConfig(config_file="wrong-file")

    param_map, param_type = get_param_map(section_map, param_key)
    param = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config)
    param.value = param_value
    cfn_value = param.to_cfn_value()
    assert_that(cfn_value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "section_map, param_key, param_value, expected_cfn_params",
    [
        # Param
        (CLUSTER, "key_name", None, {"KeyName": "NONE"}),
        (CLUSTER, "key_name", "NONE", {"KeyName": "NONE"}),
        (CLUSTER, "key_name", "test", {"KeyName": "test"}),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", None, {"EncryptedEphemeral": "false"}),
        (CLUSTER, "encrypted_ephemeral", True, {"EncryptedEphemeral": "true"}),
        (CLUSTER, "encrypted_ephemeral", False, {"EncryptedEphemeral": "false"}),
        # IntParam
        (SCALING, "scaledown_idletime", None, {"ScaleDownIdleTime": "10"}),
        (SCALING, "scaledown_idletime", 10, {"ScaleDownIdleTime": "10"}),
        (SCALING, "scaledown_idletime", 3, {"ScaleDownIdleTime": "3"}),
        # SharedDirParam
        (CLUSTER, "shared_dir", "test", {"SharedDir": "test"}),
        #(CLUSTER, "shared_dir", {"ebs": [], "shared_dir": "test"}, {"SharedDir": "test"}),
        #(CLUSTER, "shared_dir", {"ebs": [{"label": "fake_ebs"}], "shared_dir": "unused_value"}, {}),
    ]
)
def test_param_to_cfn(section_map, param_key, param_value, expected_cfn_params):
    pcluster_config = PclusterConfig(config_file="wrong-file")

    param_map, param_type = get_param_map(section_map, param_key)
    param = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config)
    param.value = param_value
    cfn_params = param.to_cfn()
    assert_that(cfn_params).is_equal_to(expected_cfn_params)

























