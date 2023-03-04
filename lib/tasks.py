"""
tasks.py version 1.0

handles running tasks within the app in a global scope
"""

import asyncio
import threading
from typing import Callable, Dict


class TaskIsRunning(BaseException):
    def __init__(self, *args) -> None:
        super().__init__(*args)

    def __str__(self) -> str:
        return "".join(self.args)


# global task and thread instances
GlobalTasks: Dict[str, asyncio.Task] = {}
GlobalThreads: Dict[str, threading.Thread] = {}


def get_task(func: Callable) -> asyncio.Task:
    """gets the task from the global dict. global dict uses function names as keys

    Args:
        func (Callable): the function that the task is running

    Raises:
        KeyError: if no key with function name found

    Returns:
        asyncio.Task: the task instance
    """
    task = GlobalTasks.get(func.__name__)
    if task is None:
        raise KeyError(f"Task with function name: {func.__name__} could not be found")
    return task


def check_task_and_create(async_func: Callable, **kwargs) -> asyncio.Task:
    """checks if there is already a task running with that name.
    if not creates coroutine and stores in global dict
    uses the function name as a key name in the global dictionary

    Args:
        func (Callable): async func to run the task

    Raises:
        TaskIsRunning: if task already running will be raised

    Returns:
        asyncio.Task: _description_
    """
    func_name = async_func.__name__
    if func_name in GlobalTasks and is_task_running(GlobalTasks[func_name]):
        raise TaskIsRunning(
            f"{func_name} is already running. Please wait for task to complete or cancel it"
        )
    task = asyncio.create_task(async_func(**kwargs))
    # store the task reference
    GlobalTasks[func_name] = task
    return task


def check_thread_and_start(func: Callable, **kwargs) -> threading.Thread:
    """the same as check_task_and_create but for threads

    Args:
        func (Callable): the thread to execute

    Raises:
        TaskIsRunning: raises if thread is already running

    Returns:
        threading.Thread: returns the newly started thread
    """
    func_name = func.__name__
    if func_name in GlobalThreads and is_thread_running(GlobalThreads[func_name]):
        raise TaskIsRunning(
            f"{func_name} is already running. Please wait for the Thread to finish"
        )
    th = threading.Thread(target=func, kwargs=kwargs)
    th.start()
    return th


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
