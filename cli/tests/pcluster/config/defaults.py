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

from enum import Enum


DEFAULT_SCALING_DICT = {
    "label": "default",
    "scaledown_idletime": 10,
}

DEFAULT_VPC_DICT = {
    "label": "default",
    "vpc_id": None,
    "master_subnet_id": None,
    "ssh_from": "0.0.0.0/0",
    "additional_sg": None,
    "compute_subnet_id": None,
    "compute_subnet_cidr": None,
    "use_public_ips": True,
    "vpc_security_group_id": None,
}

DEFAULT_EBS_DICT = {
    "label": "default",
    "shared_dir": None,
    "ebs_snapshot_id": None,
    "volume_type": "gp2",
    "volume_size": 20,
    "volume_iops": 100,
    "encrypted": False,
    "ebs_kms_key_id": None,
    "ebs_volume_id": None,
}

DEFAULT_EFS_DICT = {
    "label": "default",
    "shared_dir": None,
    "efs_fs_id": None,
    "performance_mode": "generalPurpose",
    "efs_kms_key_id": None,
    "provisioned_throughput": None,
    "encrypted": False,
    "throughput_mode": "bursting",
}

DEFAULT_RAID_DICT = {
    "label": "default",
    "shared_dir": None,
    "raid_type": None,
    "num_of_raid_volumes": None,
    "volume_type": "gp2",
    "volume_size": 20,
    "volume_iops": 100,
    "encrypted": False,
    "ebs_kms_key_id": None
}

DEFAULT_FSX_DICT = {
    "label": "default",
    "shared_dir": None,
    "fsx_fs_id": None,
    "storage_capacity": None,
    "fsx_kms_key_id": None,
    "imported_file_chunk_size": None,
    "export_path": None,
    "import_path": None,
    "weekly_maintenance_start_time": None
}

DEFAULT_CLUSTER_DICT = {
    "label": "default",
    "key_name": None,
    "template_url": None,
    "base_os": "alinux",
    "scheduler": "sge",
    "shared_dir": "/shared",
    "placement_group": None,
    "placement": "compute",
    "master_instance_type": "t2.micro",
    "master_root_volume_size": 17,
    "compute_instance_type": "t2.micro",
    "compute_root_volume_size": 17,
    "initial_queue_size": 0,
    "max_queue_size": 10,
    "maintain_initial_size": False,
    "min_vcpus": 0,
    "desired_vcpus": 2,
    "max_vcpus": 10,
    "cluster_type": "ondemand",
    "spot_price": 10,
    "spot_bid_percentage": 0.0,
    "proxy_server": None,
    "ec2_iam_role": None,
    "s3_read_resource": None,
    "s3_read_write_resource": None,
    "enable_efa": None,
    "ephemeral_dir": "/scratch",
    "encrypted_ephemeral": False,
    "custom_ami": None,
    "pre_install": None,
    "pre_install_args": None,
    "post_install": None,
    "post_install_args": None,
    "extra_json": {},
    "additional_cfn_template": None,
    "tags": {},
    "custom_chef_cookbook": None,
    "custom_awsbatch_template_url": None,
    "scaling": [
        DEFAULT_SCALING_DICT
    ],
    "vpc": [
        DEFAULT_VPC_DICT
    ],
    "ebs": [],
    "efs": [],
    "raid": [],
    "fsx": [],
}

DEFAULT_PCLUSTER_DICT = {
    "cluster": DEFAULT_CLUSTER_DICT,
}


class DefaultDict(Enum):
    cluster = DEFAULT_CLUSTER_DICT
    scaling = DEFAULT_SCALING_DICT
    vpc = DEFAULT_VPC_DICT
    ebs = DEFAULT_EBS_DICT
    efs = DEFAULT_EFS_DICT
    raid = DEFAULT_RAID_DICT
    fsx = DEFAULT_FSX_DICT
    pcluster = DEFAULT_PCLUSTER_DICT


DEFAULT_SCALING_CFN_PARAMS = {
    "ScaleDownIdleTime": "10",
}

DEFAULT_VPC_CFN_PARAMS = {
    "VPCId": "NONE",
    "MasterSubnetId": "NONE",
    "AccessFrom": "0.0.0.0/0",
    "AdditionalSG": "NONE",
    "ComputeSubnetId": "NONE",
    "ComputeSubnetCidr": "NONE",
    "UsePublicIps": "true",
    "VPCSecurityGroupId": "NONE",
}

DEFAULT_EBS_CFN_PARAMS = {
    "SharedDir": "NONE",
    "EBSSnapshotId": "NONE",
    "VolumeType": "gp2",
    "VolumeSize": "20",
    "VolumeIOPS": "100",
    "EBSEncryption": "false", #should be NONE?
    "EBSKMSKeyId": "NONE",
    "EBSVolumeId": "NONE",
}

DEFAULT_EFS_CFN_PARAMS = {
    "EFSOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"
}

DEFAULT_RAID_CFN_PARAMS = {
    "RAIDOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"
}

DEFAULT_FSX_CFN_PARAMS = {
    "FSXOptions": "NONE,NONE,NONE,NONE,NONE,NONE,NONE,NONE"
}


class DefaultCfnParams(Enum):
    scaling = DEFAULT_SCALING_CFN_PARAMS
    vpc = DEFAULT_VPC_CFN_PARAMS
    ebs = DEFAULT_EBS_CFN_PARAMS
    efs = DEFAULT_EFS_CFN_PARAMS
    raid = DEFAULT_RAID_CFN_PARAMS
    fsx = DEFAULT_FSX_CFN_PARAMS