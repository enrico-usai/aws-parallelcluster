import argparse
import os

from pcluster.config.mapping import AWS, GLOBAL, CLUSTER
from pcluster.config.pcluster_config import PclusterConfig

from assertpy import assert_that

args = argparse.Namespace()
args.config_file = os.path.abspath("pcluster/input.txt")
args.cluster_template = "unittest"


def test_efs_params(mocker):
    """Unit tests for parsing EFS related options."""
    global args
    mocker.patch("pcluster.config.params_types.get_efs_mount_target_id", return_value="mount_target_id")

    pcluster_config = PclusterConfig(
        config_file=args.config_file,
        file_sections=[AWS, GLOBAL, CLUSTER],
        cluster_label=args.cluster_template,
        fail_on_config_file_absence=True,
    )
    pcluster_config.get_master_avail_zone = mocker.MagicMock(return_value="fake_avail_zone")
    _, cfn_params, _ = pcluster_config.to_cfn()

    efs_options = [opt.strip() for opt in cfn_params.get("EFSOptions").split(",")]
    assert_that(efs_options[0]).is_equal_to("efs_shared")
    assert_that(efs_options[1]).is_equal_to("fs-12345")
    assert_that(efs_options[2]).is_equal_to("maxIO")
    assert_that(efs_options[3]).is_equal_to("key1")
    assert_that(efs_options[4]).is_equal_to("1020")
    assert_that(efs_options[5]).is_equal_to("true")
    assert_that(efs_options[6]).is_equal_to("provisioned")
    assert_that(len(efs_options)).is_equal_to(8)

