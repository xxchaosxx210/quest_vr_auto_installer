from subprocess import CompletedProcess


class RemoteDeviceError(Exception):
    """takes in result from the run function in subprocess and checks for the error string
    either in stdout or stderror

    message: str
    code: int

    Args:
        Exception (_type_): inherits from
    """

    def __init__(self, result: CompletedProcess, *args: object) -> None:
        super().__init__(*args)
        self.message: str = ""
        self.code: int = 0
        if result.stdout is not None:
            self.message += result.stdout.decode()
        if result.stderr is not None:
            self.message += result.stderr.decode()

        if result.returncode is None:
            self.code = -1
        else:
            self.code = result.returncode

    def __str__(self) -> str:
        return f"RemoteDeviceError: message={self.message}, code={self.code}"


class UnInstallError(Exception):
    def __init__(self, package_name: str, result: str, *args: object) -> None:
        super().__init__(*args)
        self.result = result
        self.package_name = package_name

    def __str__(self) -> str:
        return f"{self.package_name} could not be uninstalled. {self.result}"
