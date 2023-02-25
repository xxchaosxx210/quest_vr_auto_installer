"""
tasks.py version 1.0

handles running tasks within the app in a global scope
"""

import asyncio
import threading


class TaskIsRunning(BaseException):
    def __init__(self, *args) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return "".join(self.args)


class Tasks:
    install: asyncio.Task = None
    log_error: asyncio.Task = None
    obb_create: asyncio.Task = None
    load_installed: asyncio.Task = None
    remove_package: asyncio.Task = None
    user_info: asyncio.Task = None
    extra_magnet_info: asyncio.Task = None


class Threads:
    login_submit: threading.Thread = None
    add_game_dlg: threading.Thread = None


def create_install_task(func: callable, **kwargs):
    """checks if the task is not running then sets the Tasks.install to the new created install task

    Args:
        func (callable): _description_

    Raises:
        TaskIsRunning: _description_
    """
    if is_task_running(Tasks.install):
        raise TaskIsRunning(
            "You already have a Game being installed. Please cancel current installation or wait for the Game to be installed"
        )
    Tasks.install = _create_task(func, **kwargs)


def create_log_error_task(func: callable, **kwargs):
    if is_task_running(Tasks.log_error):
        raise TaskIsRunning(
            "Cannot create multiple Error logs. Wait for current request to end"
        )
    Tasks.log_error = _create_task(func, **kwargs)


def create_obb_dir_task(func: callable, **kwargs):
    if is_task_running(Tasks.obb_create):
        raise TaskIsRunning("Cannot create another task for OBB data creation")
    Tasks.obb_create = _create_task(func, **kwargs)


def create_extra_info_task(func: callable, **kwargs):
    if is_task_running(Tasks.extra_magnet_info):
        raise TaskIsRunning("Extra info is already running")
    Tasks.extra_magnet_info = _create_task(func, **kwargs)


def load_installed_task(func: callable, **kwargs):
    if is_task_running(Tasks.load_installed):
        raise TaskIsRunning(
            "Cannot reload list as another Coroutine is already running"
        )
    Tasks.load_installed = _create_task(func, **kwargs)


def remove_package_task(func: callable, **kwargs):
    if is_task_running(Tasks.remove_package):
        raise TaskIsRunning("Cannot Uninstall as already Removing another App")
    Tasks.remove_package = _create_task(func, **kwargs)


def get_user_info(func: callable, **kwargs):
    if is_task_running(Tasks.user_info):
        raise TaskIsRunning("Already waiting for User Information")
    Tasks.user_info = _create_task(func, **kwargs)


def login_submit_thread(func: callable, **kwargs):
    """creates a new login submit thread

    this function is blocking and wont exit until whatever running tasks are complete

    Args:
        func (callable): the function to run the login task

    Raises:
        TaskIsRunning: raises if the thread is still alive
    """
    if is_thread_running(Threads.login_submit):
        raise TaskIsRunning("Please wait for the last login request to be submitted")
    Threads.login_submit = threading.Thread(target=func, kwargs=kwargs)
    Threads.login_submit.start()
    Threads.login_submit.join()


def add_game_dialog_thread(func: callable, **kwargs):
    if is_thread_running(Threads.add_game_dlg):
        raise TaskIsRunning("Add Game Dialog has a thread already running")
    Threads.add_game_dlg = threading.Thread(target=func, kwargs=kwargs)
    Threads.add_game_dlg.start()


def _create_task(func: callable, **kwargs) -> asyncio.Task:
    loop = asyncio.get_event_loop()
    task = loop.create_task(func(**kwargs))
    return task


def is_task_running(task: asyncio.Task) -> bool:
    """checks if the Task is active

    Args:
        task (asyncio.Task): the task to check if running

    Returns:
        bool: returns True if task is currently running. False if task is None, not done or cancelled
    """
    if not isinstance(task, asyncio.Task):
        return False
    return not (task.done() or task.cancelled())


def is_thread_running(thread: threading.Thread) -> bool:
    """checks if a specified thread is still running

    Args:
        thread (threading.Thread):

    Returns:
        bool: True if it is False if no longer running or None
    """
    if not isinstance(thread, threading.Thread):
        return False
    return thread.is_alive()
