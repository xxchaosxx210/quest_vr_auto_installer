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
        stdout = result.stdout.decode()
        stderr = result.stderr.decode()
        if not stderr:
            # use stdout instead for message
            self.message = stdout
        else:
            self.message = stderr
        self.code = result.returncode

    def __str__(self) -> str:
        return f"RemoteDeviceError: message={self.message}, code={self.code}"
