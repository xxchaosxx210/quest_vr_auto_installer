"""
adb_interface.py

interfaces with the Android Debugging Bridge
"""

import subprocess
import asyncio
from typing import List

from adblib.errors import RemoteDeviceError

# global adb path to use
ADB_PATH_DEFAULT: str = ""


class Code:
    """status code errors"""

    SUCCESS = 0
    FAILURE = 1
    INVALID_COMMAND = 2


def _remove_showwindow_flag() -> subprocess.STARTUPINFO:
    """removes the show window flag so the terminal isnt shown when executing the adb commands

    Returns:
        int: new flag for startupinfo parameter
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


async def get_device_names() -> List[str]:
    """gets all Android devices found using ADB and returns a list of device names

    Raises:
        RemoteDeviceError: will be raised if error is not None

    Returns:
        List[str]: list of device names
    """
    commands = [ADB_PATH_DEFAULT, "devices"]
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
    result: subprocess.CompletedProcess = subprocess.run(
        [ADB_PATH_DEFAULT, "-s", device_name, "shell", "test", "-d", path],
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
    commands = [ADB_PATH_DEFAULT, "-s", device_name, "shell", "mkdir", path]
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
    commands = [ADB_PATH_DEFAULT, "-s", device_name, "install", apk_path]
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
    """
    commands = [ADB_PATH_DEFAULT, "-s", device_name, "uninstall"]
    if options:
        commands.extend(options)
    commands.append(package_name)
    await execute_subprocess(commands)


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
    commands = [ADB_PATH_DEFAULT, "-s", device_name, "shell", "pm", "list", "packages"]
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


async def get_package_generator(device_name: str, options: List[str] = []) -> str:
    commands = [ADB_PATH_DEFAULT, "-s", device_name, "shell", "pm", "list", "packages"]
    if options:
        commands.extend(options)
    line_offset = 0
    async for byte_line in execute_subprocess_by_line(commands=commands):
        line = byte_line.decode("utf-8")
        if line.startswith("package:"):
            line = line.replace("package:", "")
        line = line.strip()
        yield line_offset, line
        line_offset += 1


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
        ADB_PATH_DEFAULT,
        "-s",
        device_name,
        "push",
        local_path,
        destination_path,
    ]
    stdout = await execute_subprocess(command)
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


async def execute_subprocess_by_line(commands: List[str]) -> bytes:
    """generator function for reading by line from a command subprocess

    Args:
        commands (List[str]): the array of commands to send to the process

    Returns:
        bytes: the line of bytes to return
    """
    process = await asyncio.create_subprocess_exec(
        *commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        yield line
    if process.returncode != 0:
        stdout = await process.stdout.read()
        stderr = await process.stderr.read()
        raise RemoteDeviceError(
            subprocess.CompletedProcess(
                args=None, returncode=process.returncode, stdout=stdout, stderr=stderr
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
    )
    stdout, stderr = await process.communicate()
    await process.wait()
    if process.returncode != 0:
        stdout = await process.stdout.read()
        stderr = await process.stderr.read()
        raise RemoteDeviceError(
            subprocess.CompletedProcess(
                args=None, returncode=process.returncode, stdout=stdout, stderr=stderr
            )
        )
    decoded_output = stdout.decode()
    return decoded_output
