"""
adb_interface.py

interfaces with the Android Debugging Bridge
"""
import subprocess
import asyncio
from typing import AsyncGenerator, List

from adblib.errors import RemoteDeviceError, UnInstallError

# global adb path to use
ADB_DEFAULT_PATH: str = ""

ADB_DEFAULT_PORT: int = 5037


class Code:
    """status code errors"""

    SUCCESS = 0
    FAILURE = 1
    INVALID_COMMAND = 2


async def _get_bytes_from_stream(stream_reader: asyncio.StreamReader | None) -> bytes:
    """gets the bytes if stream_reader not None

    Args:
        stream_reader (asyncio.StreamReader|None): the IO buffer from subprocess

    Returns:
        bytes: returns the byte string from the IO buffer
    """
    if stream_reader is None:
        bstr = b""
    else:
        bstr = await stream_reader.read()
    return bstr


def _remove_showwindow_flag() -> subprocess.STARTUPINFO:
    """removes the show window flag so the terminal isnt shown when executing the adb commands

    Returns:
        int: new flag for startupinfo parameter
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


def close_adb() -> str:
    """kills the adb daemon on the global port

    Returns:
        str: stdout from the process
    """
    stdout = execute([ADB_DEFAULT_PATH, "kill-server"])
    return stdout


# def check_port_avalibility(port: int = ADB_DEFAULT_PORT) -> bool:
#     """checks if the port is available

#     Args:
#         port (int, optional): port to check. Defaults to ADB_DEFAULT_PORT.

#     Returns:
#         bool: true if port is available
#     """
#     try:
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
#             sock.bind(("localhost", port))
#             return True
#     except Exception:
#         return False


async def start_adb() -> str:
    """
    checks for port availability and starts the adb daemon on the first available port

    if another process has the default port then unexpected behavior may occur

    Returns:
        str: decoded string from the stdout stream
    """
    # global adb_port
    # for port in range(ADB_DEFAULT_PORT, 65534):
    #     if check_port_avalibility(port=port):
    #         adb_port = port
    #         break
    # stdout = await execute_subprocess(
    #     [ADB_DEFAULT_PATH, "-P", f"{port}", "start-server"]
    # )
    stdout = await execute_subprocess([ADB_DEFAULT_PATH, "start-server"])
    return stdout


def get_device_names() -> List[str]:
    """get a list of device names from the adb daemon

    Raises:
        RemoteDeviceError: will be raised if error is not None

    Returns:
        List[str]: device names. empty list if no devices found
    """
    commands = [ADB_DEFAULT_PATH, "devices"]
    output = execute(commands)
    devices = output.strip().split("\n")[1:]
    connected_devices = []
    for device in devices:
        if "device" in device:
            connected_device = device.split("\t")[0]
            connected_devices.append(connected_device)
    return connected_devices


async def async_get_device_names() -> List[str]:
    """same as get_device_names but async"""
    commands = [ADB_DEFAULT_PATH, "devices"]
    output = await execute_subprocess(commands)
    devices = output.strip().split("\n")[1:]
    connected_devices = []
    for device in devices:
        if "device" in device:
            connected_device = device.split("\t")[0]
            connected_devices.append(connected_device)
    return connected_devices


def path_exists(device_name: str, path: str) -> bool:
    """checks if the path exists on the remote device

    Args:
        device_name (str): name of the android device
        path (str): path to check if exists

    Raises:
        RemoteDeviceError: gets raised if error

    Returns:
        bool: true if path exists
    """
    "adb -s 1WMHHB62832202 shell test -d /sdcard/Android/obb/com.fitxr.boxvr"
    result: subprocess.CompletedProcess = subprocess.run(
        [ADB_DEFAULT_PATH, "-s", device_name, "shell", "test", "-d", path],
        capture_output=True,
        startupinfo=_remove_showwindow_flag(),
        check=False,
    )
    if result.returncode == Code.FAILURE:
        # path doesnt exist but no errors
        return False
    elif result.returncode == Code.SUCCESS:
        # path exists
        return True
    # some kind of error raise exception
    raise RemoteDeviceError(result=result)


def make_dir(device_name: str, path: str) -> str:
    """creates a new folder on the remote device

    Args:
        device_name (str): name of the android device
        path (str): path to check if exists

    Raises:
        RemoteDeviceError: gets raised if return code not equal to 0

    Returns:
        str: utf-8 encoded stdout string
    """
    commands = [ADB_DEFAULT_PATH, "-s", device_name, "shell", "mkdir", path]
    stdout = execute(commands)
    return stdout


async def install_apk(device_name, apk_path: str) -> str:
    """installs the apk from the apk path

    Args:
        device_name (_type_): name of the device to communicate with
        apk_path (str): the local path of the apk file

    Raises:
        RemoteDeviceError: gets raised if return code not equal to 0

    Returns:
        str: utf-8 encoded stdout string
    """
    # commands =
    # stdout = await execute_subprocess(commands)
    # return stdout
    commands = [ADB_DEFAULT_PATH, "-s", device_name, "install", apk_path]
    return await execute_subprocess(commands)


async def uninstall(
    device_name: str, package_name: str, options: List[str] = []
) -> None:
    """removes the package from the device

    options:
        -k: This option allows you to keep the data and cache directories of the app you are uninstalling.

        --user: This option allows you to uninstall an app for a specific user. By default, the command uninstalls the app for the current user.

        -r: This option allows you to uninstall the app and its associated data, including all the data that the app has stored in its private directories.

        --versionCode: This option allows you to uninstall a specific version of the app.

    Args:
        device_name (str): the name of the device to remove the package from
        package_name (str): the name of the package to remove
        options (List[str]): see above for options to pass

    Raises:
        RemoteDeviceError: raises if return code is not 0
        UninstallError: raises if the package is not uninstalled
    """
    commands = [ADB_DEFAULT_PATH, "-s", device_name, "uninstall"]
    if options:
        commands.extend(options)
    commands.append(package_name)
    try:
        result = await execute_subprocess(commands)
    except Exception as err:
        raise err
    if "Success" not in result:
        raise UnInstallError(package_name, result.strip())


async def get_installed_packages(
    device_name: str, options: List[str] = []
) -> List[str]:
    """gets all installed packages this function with options.

    List of options:

    -f: This option lists the packages and their associated file path.

    -3: This option lists all third-party packages (i.e., packages that are not part of the system image).

    -u: This option lists packages that are updated but not enabled.

    -i: This option lists packages that are installed but not enabled.

    -e: This option lists packages that are enabled.

    -s: This option lists packages that are installed on the SD card.

    Args:
        device_name (str): name of the device to communicate with
        options: List[str]: list of string options see above

    Returns:
        List[str]: a list of package names
    """
    commands = [ADB_DEFAULT_PATH, "-s", device_name, "shell", "pm", "list", "packages"]
    if options:
        commands.extend(options)
    stdout = await execute_subprocess(commands=commands)
    lines = stdout.split("\n")

    def parse_line(line: str) -> str:
        if line.startswith("package:"):
            line = line.replace("package:", "")
        return line.strip()

    package_names = [pkg for pkg in (parse_line(pkg) for pkg in lines) if pkg]
    return package_names


async def get_package_generator(
    device_name: str, options: List[str] = []
) -> AsyncGenerator[str, None]:
    """lazy load the package names from an adb command

    Args:
        device_name (str): the name of the android ie. Quest device
        options (List[str], optional): check the package manager API for list of options to use for this command. Defaults to [].

    Yields:
        Generator[str]: package name on that line
    """
    commands = [ADB_DEFAULT_PATH, "-s", device_name, "shell", "pm", "list", "packages"]
    if options:
        commands.extend(options)
    async for byte_line in execute_subprocess_by_line(commands=commands):
        line: str = byte_line.decode("utf-8")
        if line.startswith("package:"):
            line = line.replace("package:", "")
        line = line.strip()
        yield line


async def copy_path(device_name: str, local_path: str, destination_path: str) -> str:
    """copies a folder and its subdirectories over to the remote anroid device

    Args:
        device_name (str): name of the device
        local_path (str): the local path of directory
        destination_path (str): the directory remote path to be pushed to

    Raises:
        RemoteDeviceError: raises if return code is not 0

    Returns:
        str: utf-8 encoded stdout string
    """
    # wrap the local apk path in double quotes. ADB will kick up a fuss otherwise
    # local_path = f'\"{local_path}\"'
    command = [
        ADB_DEFAULT_PATH,
        "-s",
        device_name,
        "push",
        local_path,
        destination_path,
    ]
    stdout = await execute_subprocess(command)
    return stdout


async def async_remove_path(device_name: str, path: str) -> str:
    """removes a path from the device

    Args:
        device_name (str): name of the device
        path (str): the path to remove

    Raises:
        RemoteDeviceError: raises if return code is not 0

    Returns:
        str: utf-8 encoded stdout string
    """
    commands = [ADB_DEFAULT_PATH, "-s", device_name, "shell", "rm", "-r", path]
    result = await execute_subprocess(commands)
    return result


def get_device_model(device_name: str) -> str:
    """gets the device model from the device name

    Args:
        device_name (str): the name of the device

    Returns:
        str: the model of the device
    """
    commands = [
        ADB_DEFAULT_PATH,
        "-s",
        device_name,
        "shell",
        "getprop",
        "ro.product.model",
    ]
    stdout = execute(commands)
    return stdout


def execute(commands: List[str]) -> str:
    """sends commands to the ADB, raises any errors and returns the stdout if successful

    Args:
        commands (List[str]): list of commands to send
        options (List[str]): extra options added for the commands

    Returns:
        str: stdout from the command
    """
    startupinfo = _remove_showwindow_flag()
    result = subprocess.run(
        commands, capture_output=True, startupinfo=startupinfo, check=False
    )
    if result.returncode != Code.SUCCESS:
        raise RemoteDeviceError(result)
    stdout = result.stdout.decode("utf-8")
    return stdout


async def execute_subprocess_by_line(
    commands: List[str],
) -> AsyncGenerator[bytes, None]:
    """generator function for reading by line from a command subprocess

    Args:
        commands (List[str]): the array of commands to send to the process

    Returns:
        bytes: the line of bytes to return
    """
    process = await asyncio.create_subprocess_exec(
        *commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=_remove_showwindow_flag(),
    )
    while True:
        if process.stdout is None:
            raise ValueError("process.stdout is None and has no readline method")
        line = await process.stdout.readline()
        if not line:
            break
        yield line
    if process.returncode is None or process.returncode != 0:
        stdout = await _get_bytes_from_stream(process.stdout)
        stderr = await _get_bytes_from_stream(process.stderr)
        if process.returncode is None:
            returncode = -1
        else:
            returncode = process.returncode
        raise RemoteDeviceError(
            subprocess.CompletedProcess(
                args=commands,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            )
        )
    await process.wait()


async def execute_subprocess(commands: List[str]) -> str:
    """sends commands to the ADB, raises any errors and returns the stdout if successful

    Args:
        commands (List[str]): list of commands to send

    Returns:
        str: deocded UTF-8 string from the stdout
    """
    process = await asyncio.create_subprocess_exec(
        *commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        startupinfo=_remove_showwindow_flag(),
    )
    stdout, stderr = await process.communicate()
    await process.wait()
    if process.returncode is None or process.returncode != 0:
        stdout = await _get_bytes_from_stream(process.stdout)
        stderr = await _get_bytes_from_stream(process.stderr)
        if process.returncode is None:
            returncode = -1
        else:
            returncode = process.returncode
        raise RemoteDeviceError(
            subprocess.CompletedProcess(
                args=commands,
                returncode=returncode,
                stdout=stdout,
                stderr=stderr,
            )
        )
    decoded_output = stdout.decode()
    return decoded_output
