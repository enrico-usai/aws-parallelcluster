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

from assertpy import assert_that

from pcluster.config.mapping import SECTIONS


def test_mapping_consistency():
    """Verify for typos or wrong keys in the mapping.py file."""
    for section_map in SECTIONS:
        for section_key, _ in section_map.items():
            assert_that(
                section_key,
                description="{0} is not allowed in {1} section map".format(section_key, section_map.get("key")),
            ).is_in("type", "key", "label", "cfn", "params", "validator")

        for param_key, param_map in section_map.get("params").items():
            for param_map_key, _ in param_map.items():
                assert_that(
                    param_map_key, description="{0} is not allowed in {1} param map".format(param_map_key, param_key)
                ).is_in("type", "cfn", "allowed_values", "validator", "default", "referred_section")
