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

from pcluster.config.mapping import CLUSTER, SCALING, RAID, EFS, VPC, EBS, FSX
from tests.pcluster.config.utils import get_param_map
from tests.pcluster.config.defaults import DefaultDict, DefaultCfnParams
from pcluster.config.pcluster_config import PclusterConfig


@pytest.mark.parametrize(
    "section_map, param_key, cfn_value, expected_value",
    [
        # Param
        (CLUSTER, "key_name", "", ""),
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

    param_value = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config)._from_string(cfn_value)
    assert_that(param_value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "section_map, param_key, cfn_params_dict, expected_value",
    [
        # Param
        (CLUSTER, "key_name", {"KeyName": ""}, ""),
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

    assert_that(param.value).is_equal_to(expected_value)


def assert_section_from_cfn(section_map, cfn_params_dict, expected_section_dict):

    cfn_params = []
    for cfn_key, cfn_value in cfn_params_dict.items():
        cfn_params.append({"ParameterKey": cfn_key, "ParameterValue": cfn_value})

    pcluster_config = PclusterConfig(config_file="wrong-file")

    section_type = section_map.get("type")
    section = section_type(section_map, pcluster_config, cfn_params=cfn_params)

    if section.label:
        assert_that(section.label).is_equal_to("default")

    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    expected_dict = default_dict.copy()
    if isinstance(expected_section_dict, dict):
        expected_dict.update(expected_section_dict)

    section_dict = {}
    for param_key, param in section.params.items():
        section_dict.update({param_key: param.value})

    assert_that(section_dict).is_equal_to(expected_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (DefaultCfnParams["scaling"].value, DefaultDict["scaling"].value),
        ({}, DefaultDict["scaling"].value),
        ({"ScaleDownIdleTime": "NONE"}, DefaultDict["scaling"].value),
        ({"ScaleDownIdleTime": "20"}, {"scaledown_idletime": 20}),
    ]
)
def test_scaling_section_from_cfn(cfn_params_dict, expected_section_dict):
    assert_section_from_cfn(SCALING, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (DefaultCfnParams["vpc"].value, DefaultDict["vpc"].value),
        ({}, DefaultDict["vpc"].value),
        ({
             "VPCId": "NONE",
             "MasterSubnetId": "NONE",
             "AccessFrom": "NONE",
             "AdditionalSG": "NONE",
             "ComputeSubnetId": "NONE",
             "ComputeSubnetCidr": "NONE",
             "UsePublicIps": "true",
             "VPCSecurityGroupId": "NONE",
         },
         DefaultDict["vpc"].value),
    ]
)
def test_vpc_section_from_cfn(cfn_params_dict, expected_section_dict):
    assert_section_from_cfn(VPC, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        ({}, DefaultDict["ebs"].value),
        ({
            "SharedDir": "NONE",
            "EBSSnapshotId": "NONE",
            "VolumeType": "NONE",
            "VolumeSize": "NONE",
            "VolumeIOPS": "NONE",
            "EBSEncryption": "NONE",
            "EBSKMSKeyId": "NONE",
            "EBSVolumeId": "NONE",
        }, DefaultDict["ebs"].value),
        ({
            "SharedDir": "/shareddir",
            "EBSSnapshotId": "snap-id",
            "VolumeType": "io1",
            "VolumeSize": "30",
            "VolumeIOPS": "200",
            "EBSEncryption": "true",
            "EBSKMSKeyId": "kms-key",
            "EBSVolumeId": "ebs-id",
        }, {
             "shared_dir": "/shareddir",
             "ebs_snapshot_id": "snap-id",
             "volume_type": "io1",
             "volume_size": 30,
             "volume_iops": 200,
             "encrypted": True,
             "ebs_kms_key_id": "kms-key",
             "ebs_volume_id": "ebs-id",
         }),
    ]
)
def test_ebs_section_from_cfn(cfn_params_dict, expected_section_dict):
    assert_section_from_cfn(EBS, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        ({"EFSOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE"}, DefaultDict["efs"].value),
        ({"EFSOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"}, DefaultDict["efs"].value),
        ({"EFSOptions": "test,NONE,NONE,NONE,NONE,NONE,NONE,NONE"},
         {
             "shared_dir": "test",
             "efs_fs_id": None,
             "performance_mode": "generalPurpose",
             "efs_kms_key_id": None,
             "provisioned_throughput": None,
             "encrypted": False,
             "throughput_mode": "bursting",
         }),
        ({"EFSOptions": "test,test,maxIO,test,1024,true,provisioned"},
         {
             "shared_dir": "test",
             "efs_fs_id": "test",
             "performance_mode": "maxIO",
             "efs_kms_key_id": "test",
             "provisioned_throughput": 1024,
             "encrypted": True,
             "throughput_mode": "provisioned",
         }),
    ]
)
def test_efs_section_from_cfn(cfn_params_dict, expected_section_dict):
    assert_section_from_cfn(EFS, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (DefaultCfnParams["raid"].value, DefaultDict["raid"].value),
        ({}, DefaultDict["raid"].value),
        ({"RAIDOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE"}, DefaultDict["raid"].value),
        ({"RAIDOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"}, DefaultDict["raid"].value),
        ({"RAIDOptions": "test,NONE,NONE,NONE,NONE,NONE,NONE,NONE"},
         {
             "shared_dir": "test",
             "raid_type": None,
             "num_of_raid_volumes": None,
             "volume_type": "gp2",
             "volume_size": 20,
             "volume_iops": 100,
             "encrypted": False,
             "ebs_kms_key_id": None,
         }),
        ({"RAIDOptions": "test,0,3,gp2,30,200,true,test"},
         {
             "shared_dir": "test",
             "raid_type": 0,
             "num_of_raid_volumes": 3,
             "volume_type": "gp2",
             "volume_size": 30,
             "volume_iops": 200,
             "encrypted": True,
             "ebs_kms_key_id": "test",
         }),
    ]
)
def test_raid_section_from_cfn(cfn_params_dict, expected_section_dict):
    assert_section_from_cfn(RAID, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (DefaultCfnParams["fsx"].value, DefaultDict["fsx"].value),
        ({}, DefaultDict["fsx"].value),
        ({"FSXOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE"}, DefaultDict["fsx"].value),
        ({"FSXOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"}, DefaultDict["fsx"].value),
        ({"FSXOptions": "test,NONE,NONE,NONE,NONE,NONE,NONE,NONE"},
         {
             "shared_dir": "test",
             "fsx_fs_id": None,
             "storage_capacity": None,
             "fsx_kms_key_id": None,
             "imported_file_chunk_size": None,
             "export_path": None,
             "import_path": None,
             "weekly_maintenance_start_time": None
         }),
        ({"FSXOptions": "test,test1,10,test2,20,test3,test4,test5"},
         {
             "shared_dir": "test",
             "fsx_fs_id": "test1",
             "storage_capacity": 10,
             "fsx_kms_key_id": "test2",
             "imported_file_chunk_size": 20,
             "export_path": "test3",
             "import_path": "test4",
             "weekly_maintenance_start_time": "test5"
         }),
    ]
)
def test_fsx_section_from_cfn(cfn_params_dict, expected_section_dict):
    assert_section_from_cfn(FSX, cfn_params_dict, expected_section_dict)
