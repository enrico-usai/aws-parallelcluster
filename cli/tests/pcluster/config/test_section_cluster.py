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

import tests.pcluster.config.utils as utils
from pcluster.config.mapping import CLUSTER
from tests.pcluster.config.defaults import DefaultCfnParams, DefaultDict


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        ({}, DefaultDict["cluster"].value),
        (DefaultCfnParams["cluster"].value, DefaultDict["cluster"].value),
        # awsbatch defaults
        (
            utils.merge_dicts(DefaultCfnParams["cluster"].value, {"Scheduler": "awsbatch"}),
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "scheduler": "awsbatch",
                    "min_vcpus": 0,
                    "desired_vcpus": 0,
                    "max_vcpus": 10,
                    "spot_bid_percentage": 0.0,
                    # verify also not awsbatch values
                    "initial_queue_size": 0,
                    "max_queue_size": 10,
                    "maintain_initial_size": False,
                    "spot_price": 0,
                },
            ),
        ),
        # awsbatch custom
        (
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {"Scheduler": "awsbatch", "MinSize": "2", "DesiredSize": "4", "MaxSize": "8", "SpotPrice": "0.5"},
            ),
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "scheduler": "awsbatch",
                    "min_vcpus": 2,
                    "desired_vcpus": 4,
                    "max_vcpus": 8,
                    "spot_bid_percentage": 0.5,
                    # verify also not awsbatch values
                    "initial_queue_size": 0,
                    "max_queue_size": 10,
                    "maintain_initial_size": False,
                    "spot_price": 0,
                },
            ),
        ),
        # traditional scheduler custom
        (
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {"Scheduler": "slurm", "MinSize": "2", "DesiredSize": "2", "MaxSize": "8", "SpotPrice": "10"},
            ),
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "scheduler": "slurm",
                    "initial_queue_size": 2,
                    "max_queue_size": 8,
                    "maintain_initial_size": True,
                    "spot_price": 10,
                    # verify also awsbatch values
                    "min_vcpus": 0,
                    "desired_vcpus": 4,
                    "max_vcpus": 10,
                    "spot_bid_percentage": 0.0,
                },
            ),
        ),
        # TODO test all cluster parameters
    ],
)
def test_cluster_section_from_241_cfn(cfn_params_dict, expected_section_dict):
    """Test conversion from 2.4.1 CFN input parameters."""
    utils.assert_section_from_cfn(CLUSTER, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (
            {
                "AccessFrom": "0.0.0.0/0",
                "AdditionalCfnTemplate": "NONE",
                "AdditionalSG": "NONE",
                "AvailabilityZone": "eu-west-1a",
                "BaseOS": "alinux",
                "CLITemplate": "default",
                "ClusterType": "ondemand",
                "ComputeInstanceType": "c4.large",
                "ComputeRootVolumeSize": "15",
                "ComputeSubnetCidr": "NONE",
                "ComputeSubnetId": "subnet-0436191fe84fcff4c",
                "ComputeWaitConditionCount": "1",
                "CustomAMI": "NONE",
                "CustomAWSBatchTemplateURL": "NONE",
                "CustomChefCookbook": "NONE",
                "CustomChefRunList": "NONE",
                "DesiredSize": "1",
                "EBSEncryption": "false, false, false, false, false",
                "EBSKMSKeyId": "NONE, NONE, NONE, NONE, NONE",
                "EBSSnapshotId": "NONE, NONE, NONE, NONE, NONE",
                "EBSVolumeId": "NONE, NONE, NONE, NONE, NONE",
                "EC2IAMRoleName": "NONE",
                "EFSOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE",
                "EncryptedEphemeral": "false",
                "EphemeralDir": "/scratch",
                "ExtraJson": "{}",
                "KeyName": "test",
                "MasterInstanceType": "c4.large",
                "MasterRootVolumeSize": "15",
                "MasterSubnetId": "subnet-03bfbc8d4e2e3a8f6",
                "MaxSize": "3",
                "MinSize": "1",
                "NumberOfEBSVol": "1",
                "Placement": "cluster",
                "PlacementGroup": "NONE",
                "PostInstallArgs": "NONE",
                "PostInstallScript": "NONE",
                "PreInstallArgs": "NONE",
                "PreInstallScript": "NONE",
                "ProxyServer": "NONE",
                "RAIDOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE",
                "ResourcesS3Bucket": "NONE",
                "S3ReadResource": "NONE",
                "S3ReadWriteResource": "NONE",
                "ScaleDownIdleTime": "10",
                "Scheduler": "torque",
                "SharedDir": "/shared",
                "SpotPrice": "0.00",
                "Tenancy": "default",
                "UsePublicIps": "true",
                "VPCId": "vpc-004aabeb385513a0d",
                "VPCSecurityGroupId": "NONE",
                "VolumeIOPS": "100, 100, 100, 100, 100",
                "VolumeSize": "20, 20, 20, 20, 20",
                "VolumeType": "gp2, gp2, gp2, gp2, gp2",
            },
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "key_name": "test",
                    "scheduler": "torque",
                    "master_instance_type": "c4.large",
                    "master_root_volume_size": 15,
                    "compute_instance_type": "c4.large",
                    "compute_root_volume_size": 15,
                    "initial_queue_size": 1,
                    "max_queue_size": 3,
                    "placement": "cluster",
                    "maintain_initial_size": True,
                },
            ),
        )
    ],
)
def test_cluster_section_from_240_cfn(cfn_params_dict, expected_section_dict):
    """Test conversion from 2.4.0 CFN input parameters."""
    utils.assert_section_from_cfn(CLUSTER, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        # 2.3.1 CFN inputs
        (
            {
                "AccessFrom": "0.0.0.0/0",
                "AdditionalCfnTemplate": "NONE",
                "AdditionalSG": "NONE",
                "AvailabilityZone": "eu-west-1a",
                "BaseOS": "centos7",
                "CLITemplate": "default",
                "ClusterType": "ondemand",
                "ComputeInstanceType": "t2.micro",
                "ComputeRootVolumeSize": "250",
                "ComputeSubnetCidr": "NONE",
                "ComputeSubnetId": "subnet-0436191fe84fcff4c",
                "ComputeWaitConditionCount": "2",
                "CustomAMI": "NONE",
                "CustomAWSBatchTemplateURL": "NONE",
                "CustomChefCookbook": "NONE",
                "CustomChefRunList": "NONE",
                "DesiredSize": "2",
                "EBSEncryption": "NONE,NONE,NONE,NONE,NONE",
                "EBSKMSKeyId": "NONE,NONE,NONE,NONE,NONE",
                "EBSSnapshotId": "NONE,NONE,NONE,NONE,NONE",
                "EBSVolumeId": "NONE,NONE,NONE,NONE,NONE",
                "EC2IAMRoleName": "NONE",
                "EFSOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE",
                "EncryptedEphemeral": "false",
                "EphemeralDir": "/scratch",
                "ExtraJson": "{}",
                "FSXOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE",
                "KeyName": "test",
                "MasterInstanceType": "t2.micro",
                "MasterRootVolumeSize": "250",
                "MasterSubnetId": "subnet-03bfbc8d4e2e3a8f6",
                "MaxSize": "2",
                "MinSize": "0",
                "NumberOfEBSVol": "1",
                "Placement": "compute",
                "PlacementGroup": "NONE",
                "PostInstallArgs": "NONE",
                "PostInstallScript": "NONE",
                "PreInstallArgs": "NONE",
                "PreInstallScript": "NONE",
                "ProxyServer": "NONE",
                "RAIDOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE",
                "ResourcesS3Bucket": "NONE",
                "S3ReadResource": "NONE",
                "S3ReadWriteResource": "NONE",
                "ScaleDownIdleTime": "10",
                "Scheduler": "slurm",
                "SharedDir": "/shared",
                "SpotPrice": "0.00",
                "Tenancy": "default",
                "UsePublicIps": "true",
                "VPCId": "vpc-004aabeb385513a0d",
                "VPCSecurityGroupId": "NONE",
                "VolumeIOPS": "NONE,NONE,NONE,NONE,NONE",
                "VolumeSize": "20,NONE,NONE,NONE,NONE",
                "VolumeType": "gp2,NONE,NONE,NONE,NONE",
            },
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "key_name": "test",
                    "scheduler": "slurm",
                    "master_instance_type": "t2.micro",
                    "master_root_volume_size": 250,
                    "compute_instance_type": "t2.micro",
                    "compute_root_volume_size": 250,
                    "initial_queue_size": 2,
                    "max_queue_size": 2,
                    "placement": "compute",
                    "base_os": "centos7",
                },
            ),
        )
    ],
)
def test_cluster_section_from_231_cfn(cfn_params_dict, expected_section_dict):
    """Test conversion from 2.3.1 CFN input parameters."""
    utils.assert_section_from_cfn(CLUSTER, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (
            {
                "AccessFrom": "0.0.0.0/0",
                "AdditionalCfnTemplate": "NONE",
                "AdditionalSG": "NONE",
                "AvailabilityZone": "eu-west-1a",
                "BaseOS": "alinux",
                "CLITemplate": "default",
                "ClusterType": "ondemand",
                "ComputeInstanceType": "c4.large",
                "ComputeRootVolumeSize": "15",
                "ComputeSubnetCidr": "NONE",
                "ComputeSubnetId": "subnet-0436191fe84fcff4c",
                "ComputeWaitConditionCount": "0",
                "CustomAMI": "NONE",
                "CustomAWSBatchTemplateURL": "NONE",
                "CustomChefCookbook": "NONE",
                "CustomChefRunList": "NONE",
                "DesiredSize": "0",
                "EBSEncryption": "false, false, false, false, false",
                "EBSKMSKeyId": "NONE, NONE, NONE, NONE, NONE",
                "EBSSnapshotId": "NONE, NONE, NONE, NONE, NONE",
                "EBSVolumeId": "NONE, NONE, NONE, NONE, NONE",
                "EC2IAMRoleName": "NONE",
                "EFSOptions": "NONE, NONE, NONE, NONE, NONE, NONE, NONE, NONE",
                "EncryptedEphemeral": "false",
                "EphemeralDir": "/scratch",
                "ExtraJson": "{}",
                "KeyName": "test",
                "MasterInstanceType": "c4.large",
                "MasterRootVolumeSize": "15",
                "MasterSubnetId": "subnet-03bfbc8d4e2e3a8f6",
                "MaxSize": "3",
                "MinSize": "0",
                "NumberOfEBSVol": "1",
                "Placement": "cluster",
                "PlacementGroup": "NONE",
                "PostInstallArgs": "NONE",
                "PostInstallScript": "NONE",
                "PreInstallArgs": "NONE",
                "PreInstallScript": "NONE",
                "ProxyServer": "NONE",
                "RAIDOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE",
                "ResourcesS3Bucket": "NONE",
                "S3ReadResource": "NONE",
                "S3ReadWriteResource": "NONE",
                "ScaleDownIdleTime": "10",
                "Scheduler": "torque",
                "SharedDir": "/shared",
                "SpotPrice": "0.00",
                "Tenancy": "default",
                "UsePublicIps": "true",
                "VPCId": "vpc-004aabeb385513a0d",
                "VPCSecurityGroupId": "NONE",
                "VolumeIOPS": "100, 100, 100, 100, 100",
                "VolumeSize": "20, 20, 20, 20, 20",
                "VolumeType": "gp2, gp2, gp2, gp2, gp2",
            },
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "key_name": "test",
                    "scheduler": "torque",
                    "master_instance_type": "c4.large",
                    "master_root_volume_size": 15,
                    "compute_instance_type": "c4.large",
                    "compute_root_volume_size": 15,
                    "initial_queue_size": 0,
                    "max_queue_size": 3,
                    "placement": "cluster",
                },
            ),
        )
    ],
)
def test_cluster_section_from_210_cfn(cfn_params_dict, expected_section_dict):
    """Test conversion from 2.1.0 CFN input parameters."""
    utils.assert_section_from_cfn(CLUSTER, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (
            {
                "AccessFrom": "0.0.0.0/0",
                "AdditionalCfnTemplate": "NONE",
                "AdditionalSG": "NONE",
                "AvailabilityZone": "eu-west-1a",
                "BaseOS": "alinux",
                "CLITemplate": "default",
                "ClusterReadyScript": "NONE",
                "ClusterType": "ondemand",
                "ComputeInstanceType": "c4.large",
                "ComputeRootVolumeSize": "15",
                "ComputeSubnetCidr": "NONE",
                "ComputeSubnetId": "subnet-0436191fe84fcff4c",
                "ComputeWaitConditionCount": "2",
                "CustomAMI": "NONE",
                "CustomAWSBatchTemplateURL": "NONE",
                "CustomChefCookbook": "NONE",
                "CustomChefRunList": "NONE",
                "DesiredSize": "0",
                "EBSEncryption": "false, false, false, false, false",
                "EBSKMSKeyId": "NONE, NONE, NONE, NONE, NONE",
                "EBSSnapshotId": "NONE, NONE, NONE, NONE, NONE",
                "EBSVolumeId": "NONE, NONE, NONE, NONE, NONE",
                "EC2IAMRoleName": "NONE",
                "EncryptedEphemeral": "false",
                "EphemeralDir": "/scratch",
                "EphemeralKMSKeyId": "NONE",
                "ExtraJson": "{}",
                "KeyName": "test",
                "MasterInstanceType": "c5.large",
                "MasterRootVolumeSize": "15",
                "MasterSubnetId": "subnet-03bfbc8d4e2e3a8f6",
                "MaxSize": "10",
                "MinSize": "0",
                "NumberOfEBSVol": "1",
                "Placement": "cluster",
                "PlacementGroup": "NONE",
                "PostInstallArgs": "NONE",
                "PostInstallScript": "NONE",
                "PreInstallArgs": "NONE",
                "PreInstallScript": "NONE",
                "ProxyServer": "NONE",
                "ResourcesS3Bucket": "NONE",
                "S3ReadResource": "NONE",
                "S3ReadWriteResource": "NONE",
                "ScaleDownIdleTime": "10",
                "Scheduler": "torque",
                "SharedDir": "/shared",
                "SpotPrice": "0.00",
                "Tenancy": "default",
                "UsePublicIps": "true",
                "VPCId": "vpc-004aabeb385513a0d",
                "VPCSecurityGroupId": "NONE",
                "VolumeIOPS": "100, 100, 100, 100, 100",
                "VolumeSize": "20, 20, 20, 20, 20",
                "VolumeType": "gp2, gp2, gp2, gp2, gp2",
            },
            utils.merge_dicts(
                DefaultDict["cluster"].value,
                {
                    "key_name": "test",
                    "scheduler": "torque",
                    "master_instance_type": "c5.large",
                    "master_root_volume_size": 15,
                    "compute_instance_type": "c4.large",
                    "compute_root_volume_size": 15,
                    "initial_queue_size": 0,
                    "max_queue_size": 10,
                    "placement": "cluster",
                },
            ),
        )
    ],
)
def test_cluster_section_from_200_cfn(cfn_params_dict, expected_section_dict):
    """Test conversion from 2.0.0 CFN input parameters."""
    utils.assert_section_from_cfn(CLUSTER, cfn_params_dict, expected_section_dict)


@pytest.mark.parametrize(
    "config_parser_dict, expected_dict_params, expected_message",
    [
        # default
        ({"cluster default": {}}, {}, None),
        # right value
        ({"cluster default": {"key_name": "test"}}, {"key_name": "test"}, None),
        ({"cluster default": {"base_os": "alinux"}}, {"base_os": "alinux"}, None),
        # invalid value
        ({"cluster default": {"base_os": "wrong_value"}}, None, "has an invalid value"),
        # invalid key
        ({"cluster default": {"invalid_key": "fake_value"}}, None, "'invalid_key' is not allowed in the .* section"),
        (
            {"cluster default": {"invalid_key": "fake_value", "invalid_key2": "fake_value"}},
            None,
            "'invalid_key.*,invalid_key.*' are not allowed in the .* section",
        ),
    ],
)
def test_cluster_section_from_file(config_parser_dict, expected_dict_params, expected_message):
    utils.assert_section_from_file(CLUSTER, config_parser_dict, expected_dict_params, expected_message)


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
        ("spot_bid_percentage", "0.09", 0.09, None),
        ("spot_bid_percentage", "0.0", 0.0, None),
        ("spot_bid_percentage", "0.1", 0.1, None),
        ("spot_bid_percentage", "1", 1, None),
        ("spot_bid_percentage", "100", 100, None),
        ("spot_bid_percentage", "100.0", 100.0, None),
        ("spot_bid_percentage", "100.1", 100.1, "has an invalid value"),
        ("spot_bid_percentage", "101", 101, "has an invalid value"),
        ("scaling_settings", "test1", None, "Section .* not found in the config file"),
        ("vpc_settings", "test1", None, "Section .* not found in the config file"),
        ("vpc_settings", "test1,test2", None, "is invalid. It can only contains a single .* section label"),
        ("vpc_settings", "test1, test2", None, "is invalid. It can only contains a single .* section label"),
        ("ebs_settings", "test1", None, "Section .* not found in the config file"),
        ("ebs_settings", "test1,test2", None, "Section .* not found in the config file"),
        ("ebs_settings", "test1, test2", None, "Section .* not found in the config file"),
    ],
)
def test_cluster_param_from_file(param_key, param_value, expected_value, expected_message):
    utils.assert_param_from_file(CLUSTER, param_key, param_value, expected_value, expected_message)


@pytest.mark.parametrize(
    "section_map, section_dict, expected_config_parser_dict, expected_message",
    [
        # default
        (CLUSTER, {}, {"cluster default": {}}, None),
        # default values
        (CLUSTER, {"base_os": "alinux"}, {"cluster default": {"base_os": "alinux"}}, "No option .* in section: .*"),
        # other values
        (CLUSTER, {"key_name": "test"}, {"cluster default": {"key_name": "test"}}, None),
        (CLUSTER, {"base_os": "centos7"}, {"cluster default": {"base_os": "centos7"}}, None),
    ],
)
def test_cluster_section_to_file(section_map, section_dict, expected_config_parser_dict, expected_message):
    utils.assert_section_to_file(CLUSTER, section_dict, expected_config_parser_dict, expected_message)


@pytest.mark.parametrize(
    "section_dict, expected_cfn_params", [(DefaultDict["cluster"].value, DefaultCfnParams["cluster"].value)]
)
def test_cluster_section_to_cfn(mocker, section_dict, expected_cfn_params):
    mocker.patch("pcluster.config.param_types.get_efs_mount_target_id", return_value="valid_mount_target_id")
    mocker.patch("pcluster.config.param_types.get_avail_zone", return_value="mocked_avail_zone")
    utils.assert_section_to_cfn(CLUSTER, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "settings_label, expected_cfn_params",
    [
        ("default", DefaultCfnParams["cluster"].value),
        (
            "custom1",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "custom1",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "KeyName": "key",
                    "BaseOS": "ubuntu1404",
                    "Scheduler": "slurm",
                    "SharedDir": "/test",
                    "PlacementGroup": "NONE",
                    "Placement": "cluster",
                    "MasterInstanceType": "t2.large",
                    "MasterRootVolumeSize": "30",
                    "ComputeInstanceType": "t2.large",
                    "ComputeRootVolumeSize": "30",
                    "DesiredSize": "1",
                    "MaxSize": "2",
                    "MinSize": "1",
                    "ClusterType": "spot",
                    "SpotPrice": "5",
                    "ProxyServer": "proxy",
                    "EC2IAMRoleName": "role",
                    "S3ReadResource": "s3://url",
                    "S3ReadWriteResource": "s3://url",
                    "EFA": "compute",
                    "EphemeralDir": "/test2",
                    "EncryptedEphemeral": "true",
                    "CustomAMI": "ami-12345678",
                    "PreInstallScript": "preinstall",
                    "PreInstallArgs": '"one two"',
                    "PostInstallScript": "postinstall",
                    "PostInstallArgs": '"one two"',
                    "ExtraJson": "{'cluster': {'cfn_scheduler_slots': 'cores'}}",
                    "AdditionalCfnTemplate": "https://test",
                    "CustomChefCookbook": "https://test",
                    "CustomAWSBatchTemplateURL": "https://test",
                    # template_url = template
                    # tags = {"test": "test"}
                },
            ),
        ),
        (
            "batch",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "batch",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "Scheduler": "awsbatch",
                    "DesiredSize": "4",
                    "MaxSize": "10",
                    "MinSize": "0",
                    "SpotPrice": "0.0",
                },
            ),
        ),
        (
            "batch-custom1",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "batch-custom1",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "Scheduler": "awsbatch",
                    "DesiredSize": "3",
                    "MaxSize": "4",
                    "MinSize": "2",
                    "ClusterType": "spot",
                    "SpotPrice": "0.25",
                },
            ),
        ),
        (
            "wrong_mix_traditional",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "wrong_mix_traditional",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "Scheduler": "slurm",
                    "DesiredSize": "1",
                    "MaxSize": "2",
                    "MinSize": "1",
                    "ClusterType": "spot",
                    "SpotPrice": "5",
                },
            ),
        ),
        (
            "wrong_mix_batch",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "wrong_mix_batch",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "Scheduler": "awsbatch",
                    "DesiredSize": "3",
                    "MaxSize": "4",
                    "MinSize": "2",
                    "ClusterType": "spot",
                    "SpotPrice": "0.25",
                },
            ),
        ),
        (
            "efs",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "efs",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid",
                },
            ),
        ),
        (
            "ebs",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "ebs",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "NumberOfEBSVol": "1",
                    "SharedDir": "ebs1,NONE,NONE,NONE,NONE",
                    "VolumeType": "io1,gp2,gp2,gp2,gp2",
                    "VolumeSize": "40,20,20,20,20",
                    "VolumeIOPS": "200,100,100,100,100",
                    "EBSEncryption": "true,false,false,false,false",
                    "EBSKMSKeyId": "kms_key,NONE,NONE,NONE,NONE",
                    "EBSVolumeId": "vol-12345678,NONE,NONE,NONE,NONE",
                },
            ),
        ),
        (
            "ebs-multiple",
            utils.merge_dicts(
                DefaultCfnParams["cluster"].value,
                {
                    "CLITemplate": "ebs-multiple",
                    "AvailabilityZone": "mocked_avail_zone",
                    "VPCId": "vpc-12345678",
                    "MasterSubnetId": "subnet-12345678",
                    "NumberOfEBSVol": "2",
                    "SharedDir": "ebs1,ebs2,NONE,NONE,NONE",
                    "VolumeType": "io1,standard,gp2,gp2,gp2",
                    "VolumeSize": "40,30,20,20,20",
                    "VolumeIOPS": "200,300,100,100,100",
                    "EBSEncryption": "true,false,false,false,false",
                    "EBSKMSKeyId": "kms_key,NONE,NONE,NONE,NONE",
                    "EBSVolumeId": "vol-12345678,NONE,NONE,NONE,NONE",
                },
            ),
        ),
        (
                "all-settings",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "all-settings",
                        "AvailabilityZone": "mocked_avail_zone",
                        # scaling
                        "ScaleDownIdleTime": "15",
                        # vpc
                        "VPCId": "vpc-12345678",
                        "MasterSubnetId": "subnet-12345678",
                        # ebs
                        "NumberOfEBSVol": "1",
                        "SharedDir": "ebs1,NONE,NONE,NONE,NONE",
                        "VolumeType": "io1,gp2,gp2,gp2,gp2",
                        "VolumeSize": "40,20,20,20,20",
                        "VolumeIOPS": "200,100,100,100,100",
                        "EBSEncryption": "true,false,false,false,false",
                        "EBSKMSKeyId": "kms_key,NONE,NONE,NONE,NONE",
                        "EBSVolumeId": "vol-12345678,NONE,NONE,NONE,NONE",
                        # efs
                        "EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid",
                        # raid
                        "RAIDOptions": "raid,NONE,NONE,gp2,20,100,false,NONE",
                        # fsx
                        "FSXOptions": "fsx,NONE,NONE,NONE,NONE,NONE,NONE,NONE",
                    },
                ),
        ),
        (
                "random-order",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "random-order",
                        "AvailabilityZone": "mocked_avail_zone",
                        "KeyName": "key",
                        "BaseOS": "ubuntu1404",
                        "Scheduler": "slurm",
                        #"SharedDir": "/test",  # we have ebs volumes, see below
                        "PlacementGroup": "NONE",
                        "Placement": "cluster",
                        "MasterInstanceType": "t2.large",
                        "MasterRootVolumeSize": "30",
                        "ComputeInstanceType": "t2.large",
                        "ComputeRootVolumeSize": "30",
                        "DesiredSize": "1",
                        "MaxSize": "2",
                        "MinSize": "1",
                        "ClusterType": "spot",
                        "SpotPrice": "5",
                        "ProxyServer": "proxy",
                        "EC2IAMRoleName": "role",
                        "S3ReadResource": "s3://url",
                        "S3ReadWriteResource": "s3://url",
                        "EFA": "compute",
                        "EphemeralDir": "/test2",
                        "EncryptedEphemeral": "true",
                        "CustomAMI": "ami-12345678",
                        "PreInstallScript": "preinstall",
                        "PreInstallArgs": '"one two"',
                        "PostInstallScript": "postinstall",
                        "PostInstallArgs": '"one two"',
                        "ExtraJson": "{'cluster': {'cfn_scheduler_slots': 'cores'}}",
                        "AdditionalCfnTemplate": "https://test",
                        "CustomChefCookbook": "https://test",
                        "CustomAWSBatchTemplateURL": "https://test",
                        # scaling
                        "ScaleDownIdleTime": "15",
                        # vpc
                        "VPCId": "vpc-12345678",
                        "MasterSubnetId": "subnet-12345678",
                        # ebs
                        "NumberOfEBSVol": "1",
                        "SharedDir": "ebs1,NONE,NONE,NONE,NONE",
                        "VolumeType": "io1,gp2,gp2,gp2,gp2",
                        "VolumeSize": "40,20,20,20,20",
                        "VolumeIOPS": "200,100,100,100,100",
                        "EBSEncryption": "true,false,false,false,false",
                        "EBSKMSKeyId": "kms_key,NONE,NONE,NONE,NONE",
                        "EBSVolumeId": "vol-12345678,NONE,NONE,NONE,NONE",
                        # efs
                        "EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid",
                        # raid
                        "RAIDOptions": "raid,NONE,NONE,gp2,20,100,false,NONE",
                        # fsx
                        "FSXOptions": "fsx,NONE,NONE,NONE,NONE,NONE,NONE,NONE",
                    },
                ),
        ),
    ],
)
def test_cluster_params(mocker, pcluster_config_reader, settings_label, expected_cfn_params):
    """Unit tests for parsing Cluster related options."""
    mocker.patch("pcluster.config.param_types.get_efs_mount_target_id", return_value="mount_target_id")
    mocker.patch("pcluster.config.param_types.get_avail_zone", return_value="mocked_avail_zone")
    mocker.patch(
        "pcluster.config.validators.get_supported_features",
        return_value={"instances": ["t2.large"], "baseos": ["ubuntu1404"], "schedulers": ["slurm"]},
    )
    utils.assert_section_params(mocker, pcluster_config_reader, settings_label, expected_cfn_params)
