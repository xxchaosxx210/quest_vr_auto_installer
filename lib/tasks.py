"""
tasks.py version 1.0

handles running tasks within the app in a global scope
"""

import asyncio
import threading
from typing import Callable


class TaskIsRunning(BaseException):
    def __init__(self, *args) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return "".join(self.args)


TaskDict: Dict[str, asyncio.Task] = {}


class Tasks:
    """
    stores strong asyncio.Task references
    """

    # Game install task
    install: asyncio.Task | None = None
    # error log task
    log_error: asyncio.Task | None = None
    # obb directory creation task
    obb_create: asyncio.Task | None = None
    # load the installed apps task
    load_installed: asyncio.Task | None = None
    # uninstall a package on a device task
    remove_package: asyncio.Task | None = None
    # user info task
    user_info: asyncio.Task | None = None
    # extra Game magnet information task
    extra_magnet_info: asyncio.Task | None = None
    # loading games task
    load_magnets: asyncio.Task | None = None
    # device selection task
    device_selection: asyncio.Task | None = None


class Threads:
    """the same as Task class but for Threads instead"""

    login_submit: threading.Thread | None = None
    add_game_dlg: threading.Thread | None = None


# These functions below makes sure there is only one instance of each task or thread running at one time


def create_install_task(func: Callable, **kwargs):
    """checks if the task is not running then sets the Tasks.install to the new created install task

    Args:
        func (Callable): _description_

    Raises:
        TaskIsRunning: _description_
    """
    if is_task_running(Tasks.install):
        raise TaskIsRunning(
            "You already have a Game being installed. Please cancel current installation or wait for the Game to be installed"
        )
    Tasks.install = _create_task(func, **kwargs)


def create_log_error_task(func: Callable, **kwargs):
    if is_task_running(Tasks.log_error):
        raise TaskIsRunning(
            "Cannot create multiple Error logs. Wait for current request to end"
        )
    Tasks.log_error = _create_task(func, **kwargs)


def create_device_selection_task(func: Callable, **kwargs):
    if is_task_running(Tasks.device_selection):
        raise TaskIsRunning("Device selection Task is already running.")
    Tasks.device_selection = _create_task(func, **kwargs)


def create_obb_dir_task(func: Callable, **kwargs):
    if is_task_running(Tasks.obb_create):
        raise TaskIsRunning("Cannot create another task for OBB data creation")
    Tasks.obb_create = _create_task(func, **kwargs)


def create_extra_info_task(func: Callable, **kwargs):
    if is_task_running(Tasks.extra_magnet_info):
        raise TaskIsRunning("Extra info is already running")
    Tasks.extra_magnet_info = _create_task(func, **kwargs)


def create_load_magnets_task(func: Callable, **kwargs) -> None:
    if is_task_running(Tasks.load_magnets):
        raise TaskIsRunning("Already loading Games from API. Wait for task to finish")
    Tasks.load_magnets = _create_task(func, **kwargs)


def load_installed_task(func: Callable, **kwargs):
    if is_task_running(Tasks.load_installed):
        raise TaskIsRunning(
            "Cannot reload list as another Coroutine is already running"
        )
    Tasks.load_installed = _create_task(func, **kwargs)


def remove_package_task(func: Callable, **kwargs):
    if is_task_running(Tasks.remove_package):
        raise TaskIsRunning("Cannot Uninstall as already Removing another App")
    Tasks.remove_package = _create_task(func, **kwargs)


def get_user_info(func: Callable, **kwargs):
    if is_task_running(Tasks.user_info):
        raise TaskIsRunning("Already waiting for User Information")
    Tasks.user_info = _create_task(func, **kwargs)


def login_submit_thread(func: Callable, **kwargs):
    """creates a new login submit thread

    this function is blocking and wont exit until whatever running tasks are complete

    Args:
        func (Callable): the function to run the login task

    Raises:
        TaskIsRunning: raises if the thread is still alive
    """
    if is_thread_running(Threads.login_submit):
        raise TaskIsRunning("Please wait for the last login request to be submitted")
    Threads.login_submit = threading.Thread(target=func, kwargs=kwargs)
    Threads.login_submit.start()
    Threads.login_submit.join()


def add_game_dialog_thread(func: Callable, **kwargs):
    if is_thread_running(Threads.add_game_dlg):
        raise TaskIsRunning("Add Game Dialog has a thread already running")
    Threads.add_game_dlg = threading.Thread(target=func, kwargs=kwargs)
    Threads.add_game_dlg.start()


def _create_task(func: Callable, **kwargs) -> asyncio.Task:
    """
    creates a task from the given function and keyword arguments passed. Uses the current event loop
    so if running in seperate thread make sure a new event loop is created

    Args:
        func (Callable): the function to create a task to

    Returns:
        asyncio.Task: the created coroutine
    """
    loop = asyncio.get_event_loop()
    task = loop.create_task(func(**kwargs))
    return task


def is_task_running(task: asyncio.Task | None) -> bool:
    """checks if the Task is active

    Args:
        task (asyncio.Task): the task to check if running

    Returns:
        bool: returns True if task is currently running. False if task is None, not done or cancelled
    """
    if task is None:
        return False
    return not (task.done() or task.cancelled())


def is_thread_running(thread: threading.Thread | None) -> bool:
    """checks if a specified thread is still running

    Args:
        thread (threading.Thread):

    Returns:
        bool: True if it is False if no longer running or None
    """
    if thread is None:
        return False
    return thread.is_alive()
