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

from pcluster.config.mapping import AWS, GLOBAL, CLUSTER
from pcluster.config.pcluster_config import PclusterConfig
from tests.pcluster.config.defaults import DefaultCfnParams
from tests.pcluster.config.utils import merge_dicts

from assertpy import assert_that


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
                fail_on_config_file_absence=True,
            )
    else:
        pcluster_config = PclusterConfig(
            config_file=pcluster_config_reader(efs_settings=efs_settings),
            file_sections=[AWS, GLOBAL, CLUSTER],
            cluster_label="default",
            fail_on_config_file_absence=True,
        )

        pcluster_config.get_master_avail_zone = mocker.MagicMock(return_value="fake_avail_zone")
        _, _, cfn_params, _ = pcluster_config.to_cfn()

        for param_key, param_value in expected_cfn_params.items():
            assert_that(cfn_params.get(param_key)).is_equal_to(expected_cfn_params.get(param_key))


@pytest.mark.parametrize(
    "cluster_settings, expected_cfn_params, expected_message",
    [
        #("wrong_label", None, "Section .* not found in the config file"),
        #("test1,test2", None, "It can only contains a single .* section label"),
        #("default", DefaultCfnParams["cluster"].value, None),
        (
                "efs",
                merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {"EFSOptions": "efs,NONE,generalPurpose,NONE,NONE,false,bursting,Valid"}
                ),
                None,
        ),
        (
                "ebs",
                merge_dicts(
                    DefaultCfnParams["cluster"].value,
                    {"SharedDir": "NONE,NONE,NONE,NONE,NONE"}
                ),
                None,
        ),
    ]
)
def test_cluster_params(mocker, pcluster_config_reader, test_datadir, cluster_settings, expected_cfn_params, expected_message):
    """Unit tests for parsing Cluster related options."""

    if expected_message:
        with pytest.raises(SystemExit, match=expected_message):
            _ = PclusterConfig(
                config_file=pcluster_config_reader(cluster_settings=cluster_settings),
                file_sections=[AWS, GLOBAL, CLUSTER],
                fail_on_config_file_absence=True,
            )
    else:
        pcluster_config = PclusterConfig(
            config_file=pcluster_config_reader(cluster_settings=cluster_settings),
            file_sections=[AWS, GLOBAL, CLUSTER],
            fail_on_config_file_absence=True,
        )

        pcluster_config.get_master_avail_zone = mocker.MagicMock(return_value="mocked_avail_zone")
        _, _, cfn_params, _ = pcluster_config.to_cfn()

        assert_that(len(expected_cfn_params)).is_equal_to(52)

        for param_key, param_value in expected_cfn_params.items():
            assert_that(cfn_params.get(param_key)).is_equal_to(expected_cfn_params.get(param_key))


