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

from assertpy import assert_that

from pcluster.config.mapping import CLUSTER, SCALING
from tests.pcluster.config.utils import get_param_map
from pcluster.config.pcluster_config import PclusterConfig


@pytest.mark.parametrize(
    "section_map, param_key, cfn_value, expected_value",
    [
        # Param
        (CLUSTER, "key_name", "", None),
        (CLUSTER, "key_name", "NONE", None),
        (CLUSTER, "key_name", "fake_value", "fake_value"),
        (CLUSTER, "key_name", "test", "test"),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", "", False),
        (CLUSTER, "encrypted_ephemeral", "NONE", False),
        (CLUSTER, "encrypted_ephemeral", "wrong_value", False),
        (CLUSTER, "encrypted_ephemeral", "true", True),
        (CLUSTER, "encrypted_ephemeral", "false", False),
        # IntParam
        (SCALING, "scaledown_idletime", "", 10),
        (SCALING, "scaledown_idletime", "NONE", 10),
        (SCALING, "scaledown_idletime", "wrong_value", 10),
        (SCALING, "scaledown_idletime", "10", 10),
        (SCALING, "scaledown_idletime", "3", 3),
        # TODO FloatParam
        # JsonParam
        (CLUSTER, "extra_json", "", {}),
        (CLUSTER, "extra_json", "NONE", {}),
        (CLUSTER, "extra_json", "{\"test\": \"test1\"}", {"test": "test1"}),
        # SharedDirParam
        (CLUSTER, "shared_dir", "", "/shared"),
        (CLUSTER, "shared_dir", "NONE", "/shared"),
        (CLUSTER, "shared_dir", "fake_value", "fake_value"),
        (CLUSTER, "shared_dir", "test", "test"),
        # SpotPriceParam --> IntParam
        (CLUSTER, "spot_price", "", 10),
        (CLUSTER, "spot_price", "NONE", 10),
        (CLUSTER, "spot_price", "wrong_value", 10),
        (CLUSTER, "spot_price", "10", 10),
        (CLUSTER, "spot_price", "3", 3),
        # SpotBidPercentageParam --> FloatParam
        (CLUSTER, "spot_bid_percentage", "", 0.0),
        (CLUSTER, "spot_bid_percentage", "NONE", 0.0),
        (CLUSTER, "spot_bid_percentage", "wrong_value", 0.0),
        (CLUSTER, "spot_bid_percentage", "0.0009", 0.0009),
        (CLUSTER, "spot_bid_percentage", "0.0", 0.0),
        (CLUSTER, "spot_bid_percentage", "10", 10),
        (CLUSTER, "spot_bid_percentage", "3", 3),
    ]
)
def test_param_from_cfn_value(section_map, param_key, cfn_value, expected_value):
    param_map, param_type = get_param_map(section_map, param_key)

    pcluster_config = PclusterConfig(config_file="wrong-file")

    param_value = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config).get_value_from_string(cfn_value)
    assert_that(param_value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "section_map, param_key, cfn_params_dict, expected_value",
    [
        # Param
        (CLUSTER, "key_name", {"KeyName": ""}, None),
        (CLUSTER, "key_name", {"KeyName": "NONE"}, None),
        (CLUSTER, "key_name", {"KeyName": "fake_value"}, "fake_value"),
        (CLUSTER, "key_name", {"KeyName": "test"}, "test"),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", {"EncryptedEphemeral": ""}, False),
        (CLUSTER, "encrypted_ephemeral", {"EncryptedEphemeral": "NONE"}, False),
        (CLUSTER, "encrypted_ephemeral", {"EncryptedEphemeral": "wrong_value"}, False),
        (CLUSTER, "encrypted_ephemeral", {"EncryptedEphemeral": "true"}, True),
        (CLUSTER, "encrypted_ephemeral", {"EncryptedEphemeral": "false"}, False),
        # IntParam
        (SCALING, "scaledown_idletime", {"ScaleDownIdleTime": "10"}, 10),
        (SCALING, "scaledown_idletime", {"ScaleDownIdleTime": "NONE"},  10),
        (SCALING, "scaledown_idletime", {"ScaleDownIdleTime": "wrong_value"},  10),
        (SCALING, "scaledown_idletime", {"ScaleDownIdleTime": "10"},  10),
        (SCALING, "scaledown_idletime", {"ScaleDownIdleTime": "3"},  3),
        # SpotBidPercentageParam --> FloatParam
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": ""}, 0.0),
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": "NONE"}, 0.0),
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": "wrong_value"}, 0.0),
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": "0.0009"}, 0.0009),
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": "0.0"}, 0.0),
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": "10"}, 10),
        (CLUSTER, "spot_bid_percentage", {"SpotPrice": "3"}, 3),
    ]
)
def test_param_from_cfn(section_map, param_key, cfn_params_dict, expected_value):
    param_map, param_type = get_param_map(section_map, param_key)
    cfn_params = []
    for cfn_key, cfn_value in cfn_params_dict.items():
        cfn_params.append({"ParameterKey": cfn_key, "ParameterValue": cfn_value})

    pcluster_config = PclusterConfig(config_file="wrong-file")

    param = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config, cfn_params=cfn_params)

    assert_that(param.value, description="param key {0}".format(param_key)).is_equal_to(expected_value)




