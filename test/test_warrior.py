import os
import shutil
import tempfile
from typing import Iterator

import pytest

from taskw_ng.warrior import TaskWarrior


@pytest.fixture
def tw() -> Iterator[TaskWarrior]:
    taskdata = tempfile.mkdtemp()
    taskrc = os.path.join(os.path.dirname(__file__), "data/empty.taskrc")
    tw = TaskWarrior(config_filename=taskrc, config_overrides={"data.location": taskdata})

    # Just a sanity check to make sure that after the setup, the list of
    # tasks is empty, otherwise we are probably using the current user's
    # TASKDATA and we should not continue.
    assert tw.load_tasks() == {"completed": [], "pending": []}, (
        "A fresh taskwarrior instance should have an empty list of tasks. Instead the list"
        " seems to be populated?!"
    )

    yield tw

    # Remove the directory after the test
    shutil.rmtree(taskdata)


def test_add_task_foobar(tw: TaskWarrior):
    """Add a task with description 'foobar' and checks that the task is indeed created."""
    tw.task_add("foobar")
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    assert tasks["pending"][0]["description"] == "foobar"


def test_add_task_null_char(tw: TaskWarrior):
    """
    Try adding a task where the description contains a NULL character (0x00). This should not
    fail but instead simply add a task with the same description minus the NULL character.
    """
    tw.task_add("foo\x00bar")
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    assert tasks["pending"][0]["description"] == "foobar"


def test_add_task_recurs(tw: TaskWarrior):
    """Try adding a task with `recur` to ensure the uuid can be parsed."""
    tw.task_add("foobar weekly", due="tomorrow", recur="weekly")
    tasks = tw.load_tasks()

    assert len(tasks["pending"]) == 1
    assert tasks["pending"][0]["description"] == "foobar weekly"
    assert tasks["pending"][0]["recur"] == "weekly"
    assert tasks["pending"][0]["parent"] is not None
