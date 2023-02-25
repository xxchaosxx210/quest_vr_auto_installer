from unittest.mock import Mock, MagicMock
import asyncio

import lib.tasks as tasks


def task_factory(done: bool, cancelled: bool) -> asyncio.Task:
    mock_task = MagicMock(asyncio.Task)
    mock_task.done = Mock(return_value=done)
    mock_task.cancelled = Mock(return_value=cancelled)
    return mock_task


def test_task_is_running():
    mock_task = task_factory(False, False)
    assert tasks.is_task_running(mock_task) == True


def test_task_is_not_running():
    mock_task = task_factory(False, True)
    assert tasks.is_task_running(mock_task) == False


def test_task_is_none():
    mock_task = None
    assert tasks.is_task_running(mock_task) == False
