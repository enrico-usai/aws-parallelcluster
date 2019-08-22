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

from pcluster.config.mapping import CLUSTER, SCALING, VPC, RAID, EBS, EFS, FSX
from pcluster.config.pcluster_config import PclusterConfig
from tests.pcluster.config.defaults import DefaultDict, DefaultCfnParams
from tests.pcluster.config.utils import get_param_map, merge_dicts


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


def assert_section_to_cfn(section_map, section_dict, expected_cfn_params):

    pcluster_config = PclusterConfig(config_file="wrong-file")

    section_type = section_map.get("type")
    section = section_type(section_map, pcluster_config)
    for param_key, param_value in section_dict.items():
        param_map, param_type = get_param_map(section_map, param_key)
        param = param_type(section_map.get("key"), "default", param_key, param_map, pcluster_config)
        param.value = param_value
        section.add_param(param)
    pcluster_config.add_section(section)

    cfn_params = section.to_cfn()
    assert_that(cfn_params).is_equal_to(expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (DefaultDict["scaling"].value, DefaultCfnParams["scaling"].value),
        ({"scaledown_idletime": 20}, merge_dicts(DefaultCfnParams["scaling"].value, {"ScaleDownIdleTime": "20"})),
    ]
)
def test_scaling_section_to_cfn(section_dict, expected_cfn_params):
    assert_section_to_cfn(SCALING, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (DefaultDict["vpc"].value, DefaultCfnParams["vpc"].value),
        (
                {
                    "vpc_id": "test",
                    "master_subnet_id": "test",
                    "ssh_from": "test",
                    "additional_sg": "test",
                    "compute_subnet_id": "test",
                    "compute_subnet_cidr": "test",
                    "use_public_ips": False,
                    "vpc_security_group_id": "test",
                },
                {
                    "VPCId": "test",
                    "MasterSubnetId": "test",
                    "AccessFrom": "test",
                    "AdditionalSG": "test",
                    "ComputeSubnetId": "test",
                    "ComputeSubnetCidr": "test",
                    "UsePublicIps": "false",
                    "VPCSecurityGroupId": "test"
                },
        )
    ]
)
def test_vpc_section_to_cfn(section_dict, expected_cfn_params):
    assert_section_to_cfn(VPC, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (
                DefaultDict["ebs"].value,
                {
                    "SharedDir": "NONE",
                    "EBSSnapshotId": "NONE",
                    "VolumeType": "gp2",
                    "VolumeSize": "20",
                    "VolumeIOPS": "100",
                    "EBSEncryption": "false",
                    "EBSKMSKeyId": "NONE",
                    "EBSVolumeId": "NONE",
                }
        ),
        (
                {
                    "shared_dir": "test",
                    "ebs_snapshot_id": "test",
                    "volume_type": "test",
                    "volume_size": 30,
                    "volume_iops": 200,
                    "encrypted": True,
                    "ebs_kms_key_id": "test",
                    "ebs_volume_id": "test",
                },
                {
                    "SharedDir": "test",
                    "EBSSnapshotId": "test",
                    "VolumeType": "test",
                    "VolumeSize": "30",
                    "VolumeIOPS": "200",
                    "EBSEncryption": "true",
                    "EBSKMSKeyId": "test",
                    "EBSVolumeId": "test",
                }
        ),
    ]
)
def test_ebs_section_to_cfn(section_dict, expected_cfn_params):
    assert_section_to_cfn(EBS, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (DefaultDict["raid"].value, DefaultCfnParams["raid"].value),
    ]
)
def test_raid_section_to_cfn(section_dict, expected_cfn_params):
    assert_section_to_cfn(RAID, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (DefaultDict["fsx"].value, DefaultCfnParams["fsx"].value),
    ]
)
def test_fsx_section_to_cfn(section_dict, expected_cfn_params):
    assert_section_to_cfn(FSX, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (DefaultDict["efs"].value, DefaultCfnParams["efs"].value),
        ({"shared_dir": "NONE"}, DefaultCfnParams["efs"].value),
        ({"shared_dir": "test"}, {"EFSOptions": "test,NONE,generalPurpose,NONE,NONE,false,bursting,Valid"}),
        ({
            "shared_dir": "test",
            "efs_fs_id": "test2",
            "performance_mode": "test3",
            "efs_kms_key_id": "test4",
            "provisioned_throughput": 10,
            "encrypted": True,
            "throughput_mode": "test5",
        }, {"EFSOptions": "test,test2,test3,test4,10,true,test5,Valid"}),
        ({
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
def test_efs_section_to_cfn(mocker, section_dict, expected_cfn_params):
    mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="valid_mount_target_id")
    mocker.patch(
        "pcluster.config.pcluster_config.PclusterConfig.get_master_avail_zone", return_value="mocked_avail_zone"
    )
    assert_section_to_cfn(EFS, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params",
    [
        (DefaultDict["cluster"].value, DefaultCfnParams["cluster"].value),
    ]
)
def test_cluster_section_to_cfn(mocker, section_dict, expected_cfn_params):
    mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="valid_mount_target_id")
    mocker.patch(
        "pcluster.config.pcluster_config.PclusterConfig.get_master_avail_zone", return_value="mocked_avail_zone"
    )
    assert_section_to_cfn(CLUSTER, section_dict, expected_cfn_params)


