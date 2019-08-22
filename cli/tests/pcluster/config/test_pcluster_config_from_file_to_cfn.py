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

from pcluster.config.mapping import AWS, GLOBAL, CLUSTER
from pcluster.config.pcluster_config import PclusterConfig
from tests.pcluster.config.defaults import DefaultCfnParams
from tests.pcluster.config.utils import merge_dicts


CFN_PARAMS_NUMBER = 53


@pytest.mark.parametrize(
    "efs_settings, expected_cfn_params",
    [
        ("test1", DefaultCfnParams["efs"].value),
        ("test2", {"EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid"}),
        ("test3", {"EFSOptions": "efs,fs-12345,maxIO,key1,1020.0,false,provisioned,Valid"}),
        ("test4", {"EFSOptions": "/efs,NONE,generalPurpose,NONE,NONE,true,bursting,Valid"}),
        ("test1,test2", SystemExit()),
    ]
)
def test_efs_params(mocker, pcluster_config_reader, test_datadir, efs_settings, expected_cfn_params):
    """Unit tests for parsing EFS related options."""
    mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="mount_target_id")

    if isinstance(expected_cfn_params, SystemExit):
        with pytest.raises(SystemExit):
            _ = PclusterConfig(
                config_file=pcluster_config_reader(efs_settings=efs_settings),
                file_sections=[AWS, GLOBAL, CLUSTER],
                cluster_label="default",
                fail_on_file_absence=True,
            )
    else:
        pcluster_config = PclusterConfig(
            config_file=pcluster_config_reader(efs_settings=efs_settings),
            file_sections=[AWS, GLOBAL, CLUSTER],
            cluster_label="default",
            fail_on_file_absence=True,
        )

        pcluster_config.get_master_avail_zone = mocker.MagicMock(return_value="fake_avail_zone")
        _, _, cfn_params, _ = pcluster_config.to_cfn()

        for param_key, param_value in expected_cfn_params.items():
            assert_that(cfn_params.get(param_key)).is_equal_to(expected_cfn_params.get(param_key))


@pytest.mark.parametrize(
    "cluster_settings, expected_cfn_params, expected_message",
    [
        #("wrong_label", None, "Section .* not found in the config file"), # TODO convert cluster_template in SettingsParam
        #("test1,test2", None, "It can only contains a single .* section label"),
        ("default", DefaultCfnParams["cluster"].value, None),
        (
                "custom1",
                merge_dicts(
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
                None,
        ),
        (
                "batch",
                merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "batch",
                        "Scheduler": "awsbatch",
                        "DesiredSize": "2",
                        "MaxSize": "10",
                        "MinSize": "0",
                        "SpotPrice": "0.00",
                    }
                ),
                None,
        ),
        (
                "batch-custom1",
                merge_dicts(
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
                None,
        ),
        (
                "wrong_mix_traditional",
                merge_dicts(
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
                None,
        ),
        (
                "wrong_mix_batch",
                merge_dicts(
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
                None,
        ),
        (
                "efs",
                merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {
                        "CLITemplate": "efs",
                        "VPCId": "vpc-12345678",
                        "MasterSubnetId": "subnet-12345678",
                        "EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid",
                    }
                ),
                None,
        ),
        (
                "ebs1",
                merge_dicts(
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
                None,
        ),
        (
                "ebs2",
                merge_dicts(
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
                None,
        ),
    ]
)
def test_cluster_params(mocker, pcluster_config_reader, test_datadir, cluster_settings, expected_cfn_params, expected_message):
    """Unit tests for parsing Cluster related options."""
    mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="mount_target_id")
    mocker.patch("pcluster.config.validators.get_supported_features", return_value={
        "instances": ["t2.large"],
        "baseos": ["ubuntu1404"],
        "schedulers": ["slurm"],
    })

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _ = PclusterConfig(
                config_file=pcluster_config_reader(cluster_settings=cluster_settings),
                file_sections=[AWS, GLOBAL, CLUSTER],
                fail_on_file_absence=True,
            )
    else:
        pcluster_config = PclusterConfig(
            config_file=pcluster_config_reader(cluster_settings=cluster_settings),
            file_sections=[AWS, GLOBAL, CLUSTER],
            fail_on_file_absence=True,
        )

        pcluster_config.get_master_avail_zone = mocker.MagicMock(return_value="mocked_avail_zone")
        _, _, cfn_params, _ = pcluster_config.to_cfn()

        assert_that(len(expected_cfn_params)).is_equal_to(CFN_PARAMS_NUMBER)

        for param_key, param_value in expected_cfn_params.items():
            print("Testing '{0}'".format(param_key))
            assert_that(cfn_params.get(param_key)).is_equal_to(expected_cfn_params.get(param_key))


