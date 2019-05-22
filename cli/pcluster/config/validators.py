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
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from pcluster.utils import get_efs_mount_target_id, get_instance_vcpus, get_supported_features


def cluster_validator(section_name, section_dict, pcluster_dict):
    errors = []
    warnings = []

    if section_dict.get("scheduler") == "awsbatch":
        min_size = section_dict.get("min_vcpus")
        desired_size = section_dict.get("desired_vcpus")
        max_size = section_dict.get("max_vcpus")

        if desired_size < min_size:
            errors.append("desired_vcpus must be greater than or equal to min_vcpus")

        if desired_size > max_size:
            errors.append("desired_vcpus must be fewer than or equal to max_vcpus")

        if max_size < min_size:
            errors.append("max_vcpus must be greater than or equal to min_vcpus")
    else:
        min_size = section_dict.get("initial_queue_size") if section_dict.get("maintain_initial_size") else 0
        desired_size = section_dict.get("initial_queue_size")
        max_size = section_dict.get("max_queue_size")

        #if section_dict.get("initial_queue_size") < min_size:
        #    errors.append("initial_queue_size must be greater than or equal to min vcpus")

        if desired_size > max_size:
            errors.append("initial_queue_size must be fewer than or equal to max_queue_size")

        if max_size < min_size:
            errors.append("max_queue_size must be greater than or equal to initial_queue_size")

    return errors, warnings


def not_empty_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if param_value is None or param_value == '':
        errors.append("'{}' parameter must be specified".format(param_key))
    return errors, warnings


def ec2_key_pair_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        ec2 = boto3.client("ec2")
        ec2.describe_key_pairs(KeyNames=[param_value])
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def iam_role_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        iam = boto3.client("iam")
        arn = iam.get_role(RoleName=param_value).get("Role").get("Arn")
        account_id = boto3.client("sts").get_caller_identity().get("Account")

        iam_policy = _get_pcluster_user_policy(_get_partition(), _get_region(), account_id)

        for actions, resource_arn in iam_policy:
            response = iam.simulate_principal_policy(
                PolicySourceArn=arn, ActionNames=actions, ResourceArns=[resource_arn]
            )
            for decision in response.get("EvaluationResults"):
                if decision.get("EvalDecision") != "allowed":
                    errors.append(
                        "IAM role error on user provided role %s: action %s is %s.\n"
                        "See https://aws-parallelcluster.readthedocs.io/en/latest/iam.html"
                        % (param_value, decision.get("EvalActionName"), decision.get("EvalDecision"))
                    )
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def ec2_ami_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        ec2 = boto3.client("ec2")
        ec2.describe_images(ImageIds=[param_value])
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def ec2_ebs_snapshot_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        ec2 = boto3.client("ec2")
        test = ec2.describe_snapshots(SnapshotIds=[param_value]).get("Snapshots")[0]
        if test.get("State") != "completed":
            warnings.append("Snapshot {0} is in state '{1}' not 'completed'".format(param_value, test.get("State")))
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def ec2_volume_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        ec2 = boto3.client("ec2")
        test = ec2.describe_volumes(VolumeIds=[param_value]).get("Volumes")[0]
        if test.get("State") != "available":
            warnings.append("Volume {0} is in state '{1}' not 'available'".format(param_value, test.get("State")))
    except ClientError as e:
        if e.response.get("Error").get("Message").endswith("parameter volumes is invalid. Expected: 'vol-...'."):
            errors.append("Volume {0} does not exist.".format(param_value))
        else:
            errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def compute_instance_type_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if pcluster_dict.cluster.get("scheduler") == "awsbatch":  # FIXME there is cluster

        try:
            supported_instances = get_supported_features(pcluster_dict.region, "batch").get("instances")
            if supported_instances:
                for instance in param_value.split(","):
                    if not instance.strip() in supported_instances:
                        errors.append(
                            "compute_instance_type '{0}' is not supported by awsbatch in region '{1}'".format(
                                instance, pcluster_dict.region
                            )
                        )
            else:
                warnings.append(
                    "Unable to get instance types supported by awsbatch. Skipping compute_instance_type validation"
                )

            if "," not in param_value and "." in param_value:
                # if the type is not a list, and contains dot (nor optimal, nor a family)
                # validate instance type against max_vcpus limit
                vcpus = get_instance_vcpus(pcluster_dict.region, param_value)
                if vcpus <= 0:
                    warnings.append(
                        "Unable to get the number of vcpus for the compute_instance_type '{0}'. "
                        "Skipping instance type against max_vcpus validation".format(param_value)
                    )
                else:
                    if pcluster_dict.cluster.get("max_queue_size") < vcpus:
                        errors.append(
                            "max_vcpus must be greater than or equal to {0}, that is the number of vcpus "
                            "available for the {1} that you selected as compute_instance_type".format(
                                vcpus, param_value
                            )
                        )
        except ClientError as e:
            errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def scheduler_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if param_value is "awsbatch":
        if pcluster_dict.region in [
            "ap-northeast-3",
            "eu-north-1",
            "cn-north-1",
            "cn-northwest-1",
            "us-gov-east-1",
            "us-gov-west-1",
        ]:
            errors.append("'awsbatch' scheduler is not supported in the '{0}' region".format(pcluster_dict.region))

    return errors, warnings


def placement_group_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if param_value == "DYNAMIC":
        pass
    else:
        try:
            ec2 = boto3.client("ec2")
            ec2.describe_placement_groups(GroupNames=[param_value])
        except ClientError as e:
            errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def url_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if urlparse(param_value).scheme == "s3":
        pass
    else:
        try:
            urllib.request.urlopen(param_value)
        except urllib.error.HTTPError as e:
            warnings.append("{0} {1} {2}".format(param_value, e.code, e.reason))
        except urllib.error.URLError as e:
            warnings.append("{0} {1}".format(param_value, e.reason))

    return errors, warnings


def ec2_vpc_id_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        ec2 = boto3.client("ec2")
        ec2.describe_vpcs(VpcIds=[param_value])

        # Check for DNS support in the VPC
        if (
                not ec2.describe_vpc_attribute(VpcId=param_value, Attribute="enableDnsSupport")
                    .get("EnableDnsSupport")
                    .get("Value")
        ):
            errors.append("DNS Support is not enabled in the VPC %s" % param_value)
        if (
                not ec2.describe_vpc_attribute(VpcId=param_value, Attribute="enableDnsHostnames")
                    .get("EnableDnsHostnames")
                    .get("Value")
        ):
            errors.append("DNS Hostnames not enabled in the VPC %s" % param_value)

    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def ec2_subnet_id_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        boto3.client("ec2").describe_subnets(SubnetIds=[param_value])
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def ec2_security_group_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        boto3.client("ec2").describe_security_groups(GroupIds=[param_value])
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def efs_id_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []
    try:
        # Get master availability zone
        master_avail_zone = pcluster_dict.get_master_avail_zone()
        mount_target_id = get_efs_mount_target_id(efs_fs_id=param_value, avail_zone=master_avail_zone)
        # If there is an existing mt in the az, need to check the inbound and outbound rules of the security groups
        if mount_target_id:
            nfs_access = False
            in_access = False
            out_access = False
            # Get list of security group IDs of the mount target
            sg_ids = boto3.client("efs").describe_mount_target_security_groups(
                MountTargetId=mount_target_id
            ).get("SecurityGroups")
            for sg in boto3.client("ec2").describe_security_groups(GroupIds=sg_ids).get("SecurityGroups"):
                # Check all inbound rules
                in_rules = sg.get("IpPermissions")
                for rule in in_rules:
                    if _check_sg_rules_for_port(rule, 2049):
                        in_access = True
                        break
                out_rules = sg.get("IpPermissionsEgress")
                for rule in out_rules:
                    if _check_sg_rules_for_port(rule, 2049):
                        out_access = True
                        break
                if in_access and out_access:
                    nfs_access = True
                    break
            if not nfs_access:
                warnings.append(
                    "There is an existing Mount Target %s in the Availability Zone %s for EFS %s, "
                    "but it does not have a security group that allows inbound and outbound rules to support NFS. "
                    "Please modify the Mount Target's security group, to allow traffic on port 2049."
                    % (mount_target_id, master_avail_zone, param_value),
                    )
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))

    return errors, warnings


def efs_validator(section_name, section_dict, pcluster_dict):
    errors = []
    warnings = []

    throughput_mode = section_dict.get("throughput_mode")
    provisioned_throughput = section_dict.get("provisioned_throughput")

    if throughput_mode != "provisioned" and provisioned_throughput:
        errors.append("When specifying 'provisioned_throughput', the 'throughput_mode' must be set to 'provisioned'")

    if throughput_mode == "provisioned" and not provisioned_throughput:
        errors.append(
            "When specifying 'throughput_mode' to 'provisioned', the 'provisioned_throughput' option must be specified"
        )

    return errors, warnings


def raid_volume_iops_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    raid_iops = float(param_value) # pcluster_dict.cluster.get("raid")[0].get("volume_iops")
    raid_vol_size = float(pcluster_dict.cluster.get("raid")[0].get("volume_size"))
    if raid_iops > raid_vol_size * 50:
        errors.append("IOPS to volume size ratio of %s is too high; maximum is 50." % (raid_iops / raid_vol_size))

    return errors, warnings


def fsx_validator(section_name, section_dict, pcluster_dict):
    errors = []
    warnings = []

    fsx_import_path = pcluster_dict.cluster.get("fsx")[0].get("import_path")

    fsx_imported_file_chunk_size = pcluster_dict.cluster.get("fsx")[0].get("imported_file_chunk_size")
    if fsx_imported_file_chunk_size and not fsx_import_path:
        errors.append("When specifying 'imported_file_chunk_size', the 'import_path' option must be specified")

    fsx_export_path = pcluster_dict.cluster.get("fsx")[0].get("export_path")
    if fsx_export_path and not fsx_import_path:
        errors.append("When specifying 'export_path', the 'import_path' option must be specified")

    return errors, warnings



def fsx_id_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    try:
        ec2 = boto3.client("ec2")

        # Check to see if there is any existing mt on the fs
        fsx = boto3.client("fsx")
        fs = fsx.describe_file_systems(FileSystemIds=[param_value]).get("FileSystems")[0]

        subnet_id = pcluster_dict.cluster.get("vpc")[0].get("master_subnet_id")
        vpc_id = ec2.describe_subnets(SubnetIds=[subnet_id]).get("Subnets")[0].get("VpcId")

        # Check to see if fs is in the same VPC as the stack
        if fs.get("VpcId") != vpc_id:
            errors.append(
                "Currently only support using FSx file system that is in the same VPC as the stack. "
                "The file system provided is in %s" % fs.get("VpcId"),
            )
        # If there is an existing mt in the az, need to check the inbound and outbound rules of the security groups
        network_interface_ids = fs.get("NetworkInterfaceIds")
        network_interface_responses = ec2.describe_network_interfaces(
            NetworkInterfaceIds=network_interface_ids
        ).get("NetworkInterfaces")
        network_interfaces = [i for i in network_interface_responses if i.get("VpcId") == vpc_id]
        if not _check_nfs_access(ec2, network_interfaces):
            errors.append(
                "The current security group settings on file system %s does not satisfy "
                "mounting requirement. The file system must be associated to a security group that allows "
                "inbound and outbound TCP traffic through port 988." % param_value,
            )
    except ClientError as e:
        errors.append(e.response.get("Error").get("Message"))


def _check_nfs_access(self, ec2, network_interfaces):
    nfs_access = False
    for network_interface in network_interfaces:
        in_access = False
        out_access = False
        # Get list of security group IDs
        sg_ids = [i.get("GroupId") for i in network_interface.get("Groups")]
        # Check each sg to see if the rules are valid
        for sg in ec2.describe_security_groups(GroupIds=sg_ids).get("SecurityGroups"):
            # Check all inbound rules
            in_rules = sg.get("IpPermissions")
            for rule in in_rules:
                if self.__check_sg_rules_for_port(rule, 988):
                    in_access = True
                    break
            out_rules = sg.get("IpPermissionsEgress")
            for rule in out_rules:
                if self.__check_sg_rules_for_port(rule, 988):
                    out_access = True
                    break
            if in_access and out_access:
                nfs_access = True
                break
        if nfs_access:
            return True

    return nfs_access


def fsx_storage_capacity_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if int(param_value) % 3600 != 0 or int(param_value) < 0:
        errors.append("Capacity for FSx lustre filesystem, minimum of 3,600 GB, increments of 3,600 GB")

    return errors, warnings


def fsx_imported_file_chunk_size_validator(param_key, param_value, pcluster_dict):
    errors = []
    warnings = []

    if not (1 <= int(param_value) <= 512000):
        errors.append("'{0}' has a minimum size of 1 MiB, and max size of 512,000 MiB".format(param_key))

    return errors, warnings


def _check_sg_rules_for_port(rule, port_to_check):
    """
    Verify if the security group rule accepts connections on the given port.

    :param rule: The rule to check
    :param port_to_check: The port to check
    :return: True if the rule accepts connection, False otherwise
    """
    from_port = rule.get("FromPort")
    to_port = rule.get("ToPort")
    ip_protocol = rule.get("IpProtocol")

    # if ip_protocol is -1, all ports are allowed
    if ip_protocol == "-1":
        return True
    # tcp == protocol 6,
    # if the ip_protocol is tcp, from_port and to_port must >= 0 and <= 65535
    if (ip_protocol in ["tcp", "6"]) and (from_port <= port_to_check <= to_port):
        return True

    return False


def _get_partition():
    """Get partition for the AWS_DEFAULT_REGION set in the environment."""
    return "aws-us-gov" if _get_region().startswith("us-gov") else "aws"


def _get_region():
    """Get AWS_DEFAULT_REGION from the environment."""
    return os.environ.get("AWS_DEFAULT_REGION")


def _get_pcluster_user_policy(partition, region, account_id):
    return [
        (
            [
                "ec2:DescribeVolumes",
                "ec2:AttachVolume",
                "ec2:DescribeInstanceAttribute",
                "ec2:DescribeInstanceStatus",
                "ec2:DescribeInstances",
            ],
            "*",
        ),
        (["dynamodb:ListTables"], "*"),
        (
            [
                "sqs:SendMessage",
                "sqs:ReceiveMessage",
                "sqs:ChangeMessageVisibility",
                "sqs:DeleteMessage",
                "sqs:GetQueueUrl",
            ],
            "arn:%s:sqs:%s:%s:parallelcluster-*" % (partition, region, account_id),
        ),
        (
            [
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:TerminateInstanceInAutoScalingGroup",
                "autoscaling:SetDesiredCapacity",
                "autoscaling:DescribeTags",
                "autoScaling:UpdateAutoScalingGroup",
            ],
            "*",
        ),
        (
            [
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:GetItem",
                "dynamodb:DeleteItem",
                "dynamodb:DescribeTable",
            ],
            "arn:%s:dynamodb:%s:%s:table/parallelcluster-*" % (partition, region, account_id),
        ),
        (
            ["cloudformation:DescribeStacks"],
            "arn:%s:cloudformation:%s:%s:stack/parallelcluster-*" % (partition, region, account_id),
        ),
        (["s3:GetObject"], "arn:%s:s3:::%s-aws-parallelcluster/*" % (partition, region)),
        (["sqs:ListQueues"], "*"),
    ]
