from pcluster.config.pcluster_config import PclusterConfig
from pcluster.config.mapping import MAIN_SECTIONS, AWS, CLUSTER

import logging

LOGGER = logging.getLogger(__name__)

def main():
    """Command entrypoint."""
    print("------- from file --------")
    pcluster_config = PclusterConfig(file_sections=MAIN_SECTIONS, cluster_label="default")
    print("\nInternal representation:")
    print(pcluster_config)
    print("\nCluster Internal representation:")
    print(pcluster_config.get_section("cluster"))
    print("\nBack to file:")
    config = pcluster_config.to_file()
    with open("tmp.config", "w") as file:
        config.write(file)
    with open("tmp.config", "r") as file:
        print(file.read())
    print("\nCfn conversion:")
    for item in pcluster_config.to_cfn():
        print(item)

    print("\n\n------- from cfn --------")
    pcluster_config = PclusterConfig(file_sections=[AWS, CLUSTER], cluster_name="default")
    print("\nInternal representation:")
    print(pcluster_config)
    print("\nCluster Internal representation:")
    print(pcluster_config.get_section("cluster"))
    print("\nBack to file:")
    config = pcluster_config.to_file()
    with open("tmp.config2", "w") as file:
        config.write(file)
    with open("tmp.config2", "r") as file:
        print(file.read())


if __name__ == "__main__":
    main()