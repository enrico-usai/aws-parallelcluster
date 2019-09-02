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
from tests.common import MockedBoto3Request


@pytest.mark.parametrize(
    "section_dict, expected_message",
    [
        # traditional scheduler
        ({"scheduler": "sge", "initial_queue_size": 1, "max_queue_size": 2, "maintain_initial_size": True}, None),
        (
                {"scheduler": "sge", "initial_queue_size": 3, "max_queue_size": 2, "maintain_initial_size": True},
                "initial_queue_size must be fewer than or equal to max_queue_size",
        ),
        (
                {"scheduler": "sge", "initial_queue_size": 3, "max_queue_size": 2, "maintain_initial_size": False},
                "initial_queue_size must be fewer than or equal to max_queue_size",
        ),
        # awsbatch
        ({"scheduler": "awsbatch", "min_vcpus": 1, "desired_vcpus": 2, "max_vcpus": 3}, None),
        (
                {"scheduler": "awsbatch", "min_vcpus": 3, "desired_vcpus": 2, "max_vcpus": 3},
                "desired_vcpus must be greater than or equal to min_vcpus",
        ),
        (
                {"scheduler": "awsbatch", "min_vcpus": 1, "desired_vcpus": 4, "max_vcpus": 3},
                "desired_vcpus must be fewer than or equal to max_vcpus",
        ),
        (
                {"scheduler": "awsbatch", "min_vcpus": 4, "desired_vcpus": 4, "max_vcpus": 3},
                "max_vcpus must be greater than or equal to min_vcpus",
        ),
    ],
)
def test_cluster_validator(mocker, section_dict, expected_message):
    mocker.patch(
        "pcluster.config.validators.get_supported_features",
        return_value={"instances": ["t2.micro"], "baseos": ["alinux"], "schedulers": ["awsbatch"]},
    )
    config_parser_dict = {"cluster default": section_dict}
    utils.assert_param_validator(config_parser_dict, expected_message)


def test_ec2_key_pair_validator(boto3_stubber):
    mocked_requests = []
    describe_key_pairs_response = {
        "KeyPairs": [
            {
                "KeyFingerprint": "12:bf:7c:56:6c:dd:4f:8c:24:45:75:f1:1b:16:54:89:82:09:a4:26",
                "KeyName": "key1",
            }
        ]
    }
    mocked_requests.append(
        MockedBoto3Request(
            method="describe_key_pairs", response=describe_key_pairs_response, expected_params={"KeyNames": ["key1"]}
        )
    )
    boto3_stubber("ec2", mocked_requests)

    # TODO test with invalid key
    config_parser_dict = {"cluster default": {"key_name": "key1"}}
    utils.assert_param_validator(config_parser_dict, expected_message=None)



def test_ec2_vpc_id_validator(boto3_stubber):
    mocked_requests = []

    # mock describe_vpc boto3 call
    describe_vpc_response = {
        "Vpcs": [
            {
                "VpcId": "vpc-12345678",
                "InstanceTenancy": "default",
                "Tags": [{"Value": "Default VPC", "Key": "Name"}],
                "State": "available",
                "DhcpOptionsId": "dopt-4ef69c2a",
                "CidrBlock": "172.31.0.0/16",
                "IsDefault": True,
            }
        ]
    }
    mocked_requests.append(
        MockedBoto3Request(
            method="describe_vpcs", response=describe_vpc_response, expected_params={"VpcIds": ["vpc-12345678"]}
        )
    )

    # mock describe_vpc_attribute boto3 call
    describe_vpc_attribute_response = {
        "VpcId": "vpc-12345678",
        "EnableDnsSupport": {"Value": True},
        "EnableDnsHostnames": {"Value": True},
    }
    mocked_requests.append(
        MockedBoto3Request(
            method="describe_vpc_attribute",
            response=describe_vpc_attribute_response,
            expected_params={"VpcId": "vpc-12345678", "Attribute": "enableDnsSupport"},
        )
    )
    mocked_requests.append(
        MockedBoto3Request(
            method="describe_vpc_attribute",
            response=describe_vpc_attribute_response,
            expected_params={"VpcId": "vpc-12345678", "Attribute": "enableDnsHostnames"},
        )
    )
    boto3_stubber("ec2", mocked_requests)

    # TODO mock and test invalid vpc-id
    for vpc_id, expected_message in [("vpc-12345678", None)]:
        config_parser_dict = {"cluster default": {"vpc_settings": "default"}, "vpc default": {"vpc_id": vpc_id}}
        utils.assert_param_validator(config_parser_dict, expected_message)



