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

from pcluster.config.mapping import CLUSTER, SCALING, VPC, RAID, EBS, EFS, FSX
from pcluster.config.pcluster_config import PclusterConfig
from tests.pcluster.config.utils import get_param_map
from tests.pcluster.config.defaults import DefaultDict, DefaultCfnParams


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
    param_map, param_type = get_param_map(section_map, param_key)
    param_value = param_type(param_key, param_map).to_cfn_value(param_value)
    assert_that(param_value).is_equal_to(expected_value)


@pytest.mark.parametrize(
    "section_map, param_key, section_dict, expected_cfn_params",
    [
        # Param
        (CLUSTER, "key_name", {"key_name": None}, {"KeyName": "NONE"}),
        (CLUSTER, "key_name", {"key_name": "NONE"}, {"KeyName": "NONE"}),
        (CLUSTER, "key_name", {"key_name": "test"}, {"KeyName": "test"}),
        # BoolParam
        (CLUSTER, "encrypted_ephemeral", {"encrypted_ephemeral": None}, {"EncryptedEphemeral": "false"}),
        (CLUSTER, "encrypted_ephemeral", {"encrypted_ephemeral": True}, {"EncryptedEphemeral": "true"}),
        (CLUSTER, "encrypted_ephemeral", {"encrypted_ephemeral": False}, {"EncryptedEphemeral": "false"}),
        # IntParam
        (SCALING, "scaledown_idletime", {"scaledown_idletime": None}, {"ScaleDownIdleTime": "10"}),
        (SCALING, "scaledown_idletime", {"scaledown_idletime": 10}, {"ScaleDownIdleTime": "10"}),
        (SCALING, "scaledown_idletime", {"scaledown_idletime": 3}, {"ScaleDownIdleTime": "3"}),
        # SharedDirParam
        (CLUSTER, "shared_dir", {"shared_dir": "test"}, {"SharedDir": "test"}),
        (CLUSTER, "shared_dir", {"ebs": [], "shared_dir": "test"}, {"SharedDir": "test"}),
        (CLUSTER, "shared_dir", {"ebs": [{"label": "fake_ebs"}], "shared_dir": "unused_value"}, {}),
    ]
)
def test_param_to_cfn(section_map, param_key, section_dict, expected_cfn_params):
    param_map, param_type = get_param_map(section_map, param_key)

    cfn_params = param_type(param_key, param_map).to_cfn(section_dict, PclusterConfig())
    assert_that(cfn_params).is_equal_to(expected_cfn_params)


@pytest.mark.parametrize(
    "section_map, section_dict, expected_cfn_params",
    [
        # Section
        (SCALING, DefaultDict["scaling"].value, DefaultCfnParams["scaling"].value),
        (SCALING, {"scaledown_idletime": 20}, {"ScaleDownIdleTime": "20"}),
        (VPC, DefaultDict["vpc"].value, DefaultCfnParams["vpc"].value),
        (VPC, {"vpc_id": "test"}, {"VPCId": "test"}),
        (VPC, {"master_subnet_id": "test"}, {"MasterSubnetId": "test"}),
        (VPC, {"ssh_from": "test"}, {"AccessFrom": "test"}),
        (VPC, {"additional_sg": "test"}, {"AdditionalSG": "test"}),
        (VPC, {"compute_subnet_id": "test"}, {"ComputeSubnetId": "test"}),
        (VPC, {"compute_subnet_cidr": "test"}, {"ComputeSubnetCidr": "test"}),
        (VPC, {"use_public_ips": False}, {"UsePublicIps": "false"}),
        (VPC, {"vpc_security_group_id": "test"}, {"VPCSecurityGroupId": "test"}),
        (EBS, DefaultDict["ebs"].value, DefaultCfnParams["ebs"].value),
        (EBS, {"shared_dir": "test"}, {"SharedDir": "test"}),
        (EBS, {"ebs_snapshot_id": "test"}, {"EBSSnapshotId": "test"}),
        (EBS, {"volume_type": "test"}, {"VolumeType": "test"}),
        (EBS, {"volume_size": 30}, {"VolumeSize": "30"}),
        (EBS, {"volume_iops": 200}, {"VolumeIOPS": "200"}),
        (EBS, {"encrypted": True}, {"EBSEncryption": "true"}),
        (EBS, {"ebs_kms_key_id": "test"}, {"EBSKMSKeyId": "test"}),
        (EBS, {"ebs_volume_id": "test"}, {"EBSVolumeId": "test"}),
        (RAID, DefaultDict["raid"].value, DefaultCfnParams["raid"].value),
        (FSX, DefaultDict["fsx"].value, DefaultCfnParams["fsx"].value),
        # EFSSection
        (EFS, DefaultDict["efs"].value, DefaultCfnParams["efs"].value),
        (EFS, {"shared_dir": "NONE"}, DefaultCfnParams["efs"].value),
        (EFS, {"shared_dir": "test"}, {"EFSOptions": "test,NONE,generalPurpose,NONE,NONE,false,bursting,Valid"}),
        (EFS, {
            "shared_dir": "test",
            "efs_fs_id": "test2",
            "performance_mode": "test3",
            "efs_kms_key_id": "test4",
            "provisioned_throughput": 10,
            "encrypted": True,
            "throughput_mode": "test5",
        }, {"EFSOptions": "test,test2,test3,test4,10,true,test5,Valid"}),
        (EFS, {
            "shared_dir": "test",
            "efs_fs_id": None,
            "performance_mode": "test1",
            "efs_kms_key_id": "test2",
            "provisioned_throughput": 1024,
            "encrypted": False,
            "throughput_mode": "test3",
        }, {"EFSOptions": "test,NONE,test1,test2,1024,false,test3,Valid"}),
    ]
)
def test_section_to_cfn(mocker, section_map, section_dict, expected_cfn_params):
    # update expected dictionary
    default_params = DefaultCfnParams[section_map.get("key")].value
    expected_params = default_params.copy()
    if isinstance(expected_cfn_params, dict):
        expected_params.update(expected_cfn_params)

    section_type = section_map.get("type")
    if section_map == EFS:
        mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="valid_mount_target_id")
        mocker.patch("pcluster.config.pcluster_config.PclusterConfig.get_master_avail_zone")

    cfn_params = section_type(section_map).to_cfn(section_dict, PclusterConfig())
    assert_that(cfn_params).is_equal_to(expected_params)

