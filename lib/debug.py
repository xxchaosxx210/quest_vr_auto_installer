from typing import List


class Quest:
    def __init__(self, name: str, package_names: List[str]) -> None:
        self.name = name
        self.package_names = package_names


class Debug:
    enabled: bool = False
    devices = [
        Quest("QUEST1", ["com.fake.MarioKart"]),
        Quest("QUEST2", ["com.fake.Zelda", "org.com.F1"]),
    ]

    @staticmethod
    def get_device_names() -> List[str]:
        device_names = list(map(lambda quest: quest.name, Debug.devices))
        return device_names

    @staticmethod
    def get_device(name: str) -> Quest:
        """gets the device related to the device name

        Args:
            name (str): the name of the device to retrieve

        Raises:
            LookupError: if no device found then this gets raised

        Returns:
            Quest: the Quest object
        """
        found_devices = list(filter(lambda device: device.name == name, Debug.devices))
        if not found_devices:
            raise LookupError("Could not find device with that name")
        # return the first element
        return found_devices[0]
