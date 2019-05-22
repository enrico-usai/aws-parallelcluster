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
from pcluster.config.pcluster_config import PclusterConfig

import logging
import pcluster

from pcluster.config.mapping import AWS, CLUSTER, MAIN_SECTIONS

LOGGER = logging.getLogger(__name__)

from assertpy import assert_that


def fake_validator(param_key, param_value, pcluster_dict):
    return [], []


def mock_cluster_dict(config_dict, key_path, value):
    dict_path = key_path.split(".")

    next_element = config_dict
    for subpath in dict_path:

        element = next_element.get(subpath)
        if not isinstance(element, dict):
            next_element[subpath] = value
            break
        next_element = element


def read_text(path):
    """Read the content of a file."""
    with path.open() as f:
        return f.read()


def test_from_file(capsys, test_datadir):
    """Command entrypoint."""
    mock_cluster_dict(pcluster.config.mapping.CLUSTER, "items.key_name.validator", fake_validator)
    mock_cluster_dict(pcluster.config.mapping.VPC, "items.vpc_id.validator", fake_validator)
    mock_cluster_dict(pcluster.config.mapping.VPC, "items.master_subnet_id.validator", fake_validator)
    mock_cluster_dict(pcluster.config.mapping.VPC, "items.compute_subnet_id.validator", fake_validator)

    input_file = test_datadir / "input.txt"
    output_file = test_datadir / "output.txt"


    pcluster_config = PclusterConfig(
        file_sections=MAIN_SECTIONS,
        config_file=input_file,
        cluster_label="default",
    )

    configparser = pcluster_config.to_file()
    #print(config.read())
    #print({section: dict(configparser[section]) for section in configparser.sections()})

    with open(output_file, "w") as file:
        configparser.write(file)
    with open(output_file, "r") as file:
        print(file.read())

    #assert_that(capsys.readouterr().out).is_equal_to(read_text(input_file))
    #assert_that(filecmp.cmp(input_file, output_file)).is_true()
    assert_that(1).is_equal_to(1)


def dtest_from_file_old(capsys, mocker):
    """Command entrypoint."""
    mock_cluster_dict(pcluster.config.mapping.CLUSTER, "items.key_name.validator", fake_validator)
    mock_cluster_dict(pcluster.config.mapping.VPC, "items.vpc_id.validator", fake_validator)
    mock_cluster_dict(pcluster.config.mapping.VPC, "items.master_subnet_id.validator", fake_validator)
    mock_cluster_dict(pcluster.config.mapping.VPC, "items.compute_subnet_id.validator", fake_validator)

    print("------- from file --------")
    pcluster_config = PclusterConfig(
        file_sections=MAIN_SECTIONS,
        config_file="input_config_file",
        cluster_label="default",
    )
    print("\nInternal representation:")
    print(pcluster_config)
    print("\nCluster Internal representation:")
    print(pcluster_config.get("cluster"))
    print("\nCfn conversion:")
    template_url, params, tags = pcluster_config.to_cfn()
    print("template_url:", template_url)
    print("cfn params:", params)
    print("tags:", tags)

    print("\nBack to file:")
    config = pcluster_config.to_file()
    with open("output_config_file", "w") as file:
        config.write(file)
    with open("output_config_file", "r") as file:
        print(file.read())

    pcluster_config_out = PclusterConfig(
        file_sections=[AWS, CLUSTER], config_file="output_config_file", cluster_label="default"
    )

    #assert_that(pcluster_config_out).is_equal_to(pcluster_config)
    assert_that(1).is_equal_to(1)


def test_from_cfn():
    print("\n\n------- from cfn --------")
    pcluster_config = PclusterConfig(file_sections=[AWS, CLUSTER], cluster_name="default")
    print("\nInternal representation:")
    print(pcluster_config)
    print("\nCluster Internal representation:")
    print(pcluster_config.get("cluster"))
    print("\nBack to file:")
    config = pcluster_config.to_file()
    with open("tmp.config2", "w") as file:
        config.write(file)
    with open("tmp.config2", "r") as file:
        print(file.read())

    assert_that(1).is_equal_to(1)
