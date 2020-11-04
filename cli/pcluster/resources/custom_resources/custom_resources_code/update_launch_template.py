# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with
#  the License. A copy of the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "LICENSE.txt" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and
# limitations under the License.
import logging

import boto3
from botocore.config import Config
from crhelper import CfnResource

helper = CfnResource(json_logging=False, log_level="INFO", boto_level="ERROR", sleep_on_delete=0)
logger = logging.getLogger(__name__)
boto3_config = Config(retries={"max_attempts": 60})


@helper.delete
def no_op(_, __):
    pass


@helper.create
@helper.update
def update_launch_template(event, _):
    """
    Workaround for missing CloudFormation support of NetworkCardIndex attribute in Launch Templates.

    Due to this temporary condition, Launch templates are created without the NetworkCardIndex attribute, and then
    updated using this function called via lambda.

    :param launch_template_id: The id of the Launch Template to update
    :param region: The region where the cluster is created
    """
    launch_template_id = event["ResourceProperties"]["LaunchTemplateId"]
    client = boto3.client("ec2")

    # Retrieve the current version of the Launch Template
    current_lt_version = (
        client.describe_launch_templates(LaunchTemplateIds=[launch_template_id])
        .get("LaunchTemplates")[0]
        .get("DefaultVersionNumber")
    )

    # Get the Launch Template Data of the current version
    launch_template_data = (
        client.describe_launch_template_versions(
            LaunchTemplateId=launch_template_id, Versions=[str(current_lt_version)]
        )
        .get("LaunchTemplateVersions")[0]
        .get("LaunchTemplateData")
    )

    # Get the network interfaces
    network_interfaces = launch_template_data.get("NetworkInterfaces")

    # NetworkCardIndex is needed only in case of multiple Network Interfaces
    if len(network_interfaces) > 1:
        # Add NetworkCardIndex attribute to all nw interfaces
        for interface in network_interfaces:
            interface["NetworkCardIndex"] = interface["DeviceIndex"]

        # Create new Launch Template version
        new_lt_version = (
            client.create_launch_template_version(
                LaunchTemplateId=launch_template_id, LaunchTemplateData=launch_template_data
            )
            .get("LaunchTemplateVersion")
            .get("VersionNumber")
        )

        # Update Launch Template
        client.modify_launch_template(LaunchTemplateId=launch_template_id, DefaultVersion=str(new_lt_version))


def handler(event, context):
    helper(event, context)


if __name__ == "__main__":
    event = {"ResourceProperties": {"LaunchTemplateId": "lt-******"}}
    update_launch_template(event, "")
