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

from pcluster.config.mapping import CLUSTER
import tests.pcluster.config.utils as utils
from tests.pcluster.config.defaults import DefaultDict, DefaultCfnParams


@pytest.mark.parametrize(
    "cfn_params_dict, expected_section_dict",
    [
        (
                DefaultCfnParams["cluster"].value,
                utils.merge_dicts(
                    DefaultDict["cluster"].value,
                    {
                        "desired_vcpus": 0,  # value coming from DesiredSize
                        "spot_bid_percentage": 10.0,  # value coming from SpotPrice
                    }
                )
        ),
        ({}, DefaultDict["cluster"].value),
        # TODO test all cluster parameters
    ]
)
def test_cluster_section_from_cfn(cfn_params_dict, expected_section_dict):
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
        (
                {"cluster default": {"invalid_key": "fake_value"}},
                None,
                "'invalid_key' are not allowed in the .* section",
        ),
        (
                {"cluster default": {"invalid_key": "fake_value", "invalid_key2": "fake_value"}},
                None,
                "'invalid_key,invalid_key2' are not allowed in the .* section",
        ),
    ]
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
        ("spot_bid_percentage", "0.0009", 0.0009, None),
        ("spot_bid_percentage", "0.0", 0.0, None),
        ("spot_bid_percentage", "10", 10, None),
        ("spot_bid_percentage", "3", 3, None),
        ("scaling_settings", "test1", None, "Section .* not found in the config file"),
        ("vpc_settings", "test1", None, "Section .* not found in the config file"),
        ("vpc_settings", "test1,test2", None, "is invalid. It can only contains a single .* section label"),
        ("vpc_settings", "test1, test2", None, "is invalid. It can only contains a single .* section label"),
        ("ebs_settings", "test1", None, "Section .* not found in the config file"),
        ("ebs_settings", "test1,test2", None, "Section .* not found in the config file"),
        ("ebs_settings", "test1, test2", None, "Section .* not found in the config file"),
    ]
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
    ]
)
def test_cluster_section_to_file(section_map, section_dict, expected_config_parser_dict, expected_message):
    utils.assert_section_to_file(CLUSTER, section_dict, expected_config_parser_dict, expected_message)


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
    utils.assert_section_to_cfn(CLUSTER, section_dict, expected_cfn_params)


@pytest.mark.parametrize(
    "settings_label, expected_cfn_params",
    [
        #("wrong_label", None, "Section .* not found in the config file"), # TODO convert cluster_template in SettingsParam
        #("test1,test2", None, "It can only contains a single .* section label"),
        ("default", DefaultCfnParams["cluster"].value),
        (
                "custom1",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "custom1",
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
                        "PreInstallArgs": "\"one two\"",
                        "PostInstallScript": "postinstall",
                        "PostInstallArgs": "\"one two\"",
                        "ExtraJson": "{'cluster': {'cfn_scheduler_slots': 'cores'}}",
                        "AdditionalCfnTemplate": "https://test",
                        "CustomChefCookbook": "https://test",
                        "CustomAWSBatchTemplateURL": "https://test",
                        #template_url = template
                        #tags = {"test": "test"}
                    }
                ),
        ),
        (
                "batch",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "batch",
                        "Scheduler": "awsbatch",
                        "DesiredSize": "2",
                        "MaxSize": "10",
                        "MinSize": "0",
                        "SpotPrice": "0.0",
                    }
                ),
        ),
        (
                "batch-custom1",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "batch-custom1",
                        "Scheduler": "awsbatch",
                        "DesiredSize": "3",
                        "MaxSize": "4",
                        "MinSize": "2",
                        "ClusterType": "spot",
                        "SpotPrice": "0.25",
                    }
                ),
        ),
        (
                "wrong_mix_traditional",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "wrong_mix_traditional",
                        "Scheduler": "slurm",
                        "DesiredSize": "1",
                        "MaxSize": "2",
                        "MinSize": "1",
                        "ClusterType": "spot",
                        "SpotPrice": "5",
                    }
                ),
        ),
        (
                "wrong_mix_batch",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "wrong_mix_batch",
                        "Scheduler": "awsbatch",
                        "DesiredSize": "3",
                        "MaxSize": "4",
                        "MinSize": "2",
                        "ClusterType": "spot",
                        "SpotPrice": "0.25",
                    }
                ),
        ),
        (
                "efs",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "efs",
                        "VPCId": "vpc-12345678",
                        "MasterSubnetId": "subnet-12345678",
                        "EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid",
                    }
                ),
        ),
        (
                "ebs1",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "ebs1",
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
                    }
                ),
        ),
        (
                "ebs2",
                utils.merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "ebs2",
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
                    }
                ),
        ),
    ]
)
def test_cluster_params(mocker, pcluster_config_reader, settings_label, expected_cfn_params):
    """Unit tests for parsing Cluster related options."""
    mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="mount_target_id")
    mocker.patch("pcluster.config.validators.get_supported_features", return_value={
        "instances": ["t2.large"],
        "baseos": ["ubuntu1404"],
        "schedulers": ["slurm"],
    })
    utils.assert_section_params(mocker, pcluster_config_reader, settings_label, expected_cfn_params)


