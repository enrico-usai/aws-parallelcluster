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

    param_value = param_type(param_key, param_map).from_string(cfn_value)
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

    _, param_value = param_type(param_key, param_map).from_cfn(cfn_params)

    assert_that(param_value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "section_map, cfn_params_dict, expected_section_dict",
    [
        # SCALING
        (SCALING, DefaultCfnParams["scaling"].value, DefaultDict["scaling"].value),
        (SCALING, {}, DefaultDict["scaling"].value),
        (SCALING, {"ScaleDownIdleTime": "NONE"}, DefaultDict["scaling"].value),
        (SCALING, {"ScaleDownIdleTime": "20"}, {"scaledown_idletime": 20}),
        # VPC
        (VPC, DefaultCfnParams["vpc"].value, DefaultDict["vpc"].value),
        (VPC, {}, DefaultDict["vpc"].value),
        (VPC,
         {
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
        # EBS
        (EBS, DefaultCfnParams["ebs"].value, DefaultDict["ebs"].value),
        (EBS, {}, DefaultDict["ebs"].value),
        (EBS, {
            "SharedDir": "NONE",
            "EBSSnapshotId": "NONE",
            "VolumeType": "NONE",
            "VolumeSize": "NONE",
            "VolumeIOPS": "NONE",
            "EBSEncryption": "NONE",
            "EBSKMSKeyId": "NONE",
            "EBSVolumeId": "NONE",
        }, DefaultDict["ebs"].value),
        (EBS, {
            "SharedDir": "test",
            "EBSSnapshotId": "test1",
            "VolumeType": "test2",
            "VolumeSize": "30",
            "VolumeIOPS": "200",
            "EBSEncryption": "true",
            "EBSKMSKeyId": "test3",
            "EBSVolumeId": "test4",
        }, {
            "shared_dir": "test",
            "ebs_snapshot_id": "test1",
            "volume_type": "test2",
            "volume_size": 30,
            "volume_iops": 200,
            "encrypted": True,
            "ebs_kms_key_id": "test3",
            "ebs_volume_id": "test4",
        }),
        # EFS
        (EFS, {"EFSOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE"}, DefaultDict["efs"].value),
        (EFS, {"EFSOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"}, DefaultDict["efs"].value),
        (EFS,
         {"EFSOptions": "test,NONE,NONE,NONE,NONE,NONE,NONE,NONE"},
         {
             "label": "default",
             "shared_dir": "test",
             "efs_fs_id": None,
             "performance_mode": "generalPurpose",
             "efs_kms_key_id": None,
             "provisioned_throughput": None,
             "encrypted": False,
             "throughput_mode": "bursting",
         }),
        (EFS,
         {"EFSOptions": "test,test,maxIO,test,1024,true,provisioned"},
         {
             "label": "default",
             "shared_dir": "test",
             "efs_fs_id": "test",
             "performance_mode": "maxIO",
             "efs_kms_key_id": "test",
             "provisioned_throughput": 1024,
             "encrypted": True,
             "throughput_mode": "provisioned",
         }),
        # RAID
        (RAID, DefaultCfnParams["raid"].value, DefaultDict["raid"].value),
        (RAID, {}, DefaultDict["raid"].value),
        (RAID, {"RAIDOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE"}, DefaultDict["raid"].value),
        (RAID, {"RAIDOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"}, DefaultDict["raid"].value),
        (RAID,
         {"RAIDOptions": "test,NONE,NONE,NONE,NONE,NONE,NONE,NONE"},
         {
             "label": "default",
             "shared_dir": "test",
             "raid_type": None,
             "num_of_raid_volumes": None,
             "volume_type": "gp2",
             "volume_size": 20,
             "volume_iops": 100,
             "encrypted": False,
             "ebs_kms_key_id": None,
         }),
        (RAID,
         {"RAIDOptions": "test,0,3,gp2,30,200,true,test"},
         {
             "label": "default",
             "shared_dir": "test",
             "raid_type": 0,
             "num_of_raid_volumes": 3,
             "volume_type": "gp2",
             "volume_size": 30,
             "volume_iops": 200,
             "encrypted": True,
             "ebs_kms_key_id": "test",
         }),
        # FSX
        (FSX, DefaultCfnParams["fsx"].value, DefaultDict["fsx"].value),
        (FSX, {}, DefaultDict["fsx"].value),
        (FSX, {"FSXOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE"}, DefaultDict["fsx"].value),
        (FSX, {"FSXOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"}, DefaultDict["fsx"].value),
        (FSX,
         {"FSXOptions": "test,NONE,NONE,NONE,NONE,NONE,NONE,NONE"},
         {
             "label": "default",
             "shared_dir": "test",
             "fsx_fs_id": None,
             "storage_capacity": None,
             "fsx_kms_key_id": None,
             "imported_file_chunk_size": None,
             "export_path": None,
             "import_path": None,
             "weekly_maintenance_start_time": None
         }),
        (FSX,
         {"FSXOptions": "test,test1,10,test2,20,test3,test4,test5"},
         {
             "label": "default",
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
def test_section_from_cfn(section_map, cfn_params_dict, expected_section_dict):

    cfn_params = []
    for cfn_key, cfn_value in cfn_params_dict.items():
        cfn_params.append({"ParameterKey": cfn_key, "ParameterValue": cfn_value})

    section_type = section_map.get("type")
    _, section_dict = section_type(section_map).from_cfn(cfn_params)

    # update expected dictionary
    default_dict = DefaultDict[section_map.get("key")].value
    expected_dict = default_dict.copy()
    if isinstance(expected_section_dict, dict):
        expected_dict.update(expected_section_dict)

    assert_that(section_dict).is_equal_to(expected_dict)