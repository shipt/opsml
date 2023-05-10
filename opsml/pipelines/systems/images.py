# pylint: disable = import-outside-toplevel
"""Module containing code to get docker images"""


class ContainerImageRegistry:
    def __init__(self, container_registry: str):

        """
        Class for storing different docker images used for pipeline training

        Args:
            container_registry:
                Registry address where docker images are stored. Does not include suffix
        """

        self.container_registry = container_registry

    def get_image_uri(self, image_name: str) -> str:
        """
        Gets image uri

        Args:
            image_name:
                Name of image excluding registry path. This will be appended
                to container registry name. If a tag is not provided as part of the image name
                then "latest" will be appended

            Example:
                f"{self.container_registry}/{image_name}" or
                f"{self.container_registry}/{image_name}:latest"


        Returns
            image uri
        """

        if ":" not in image_name:
            image_name = f"{image_name}:latest"

        return f"{self.container_registry}/{image_name}"
