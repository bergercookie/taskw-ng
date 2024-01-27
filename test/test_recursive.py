import os
import shutil
import tempfile
from typing import Iterator

import pytest

from taskw_ng import TaskWarrior
from taskw_ng.warrior import TaskWarrior

TASK = {
    "description": "task 2 http://www.google.com/",
    "entry": "1325011643",
    "project": "work",
    "start": "1326079920",
    "status": "pending",
    "uuid": "c1c431ea-f0dc-4683-9a20-e64fcfa65fd1",
}


@pytest.fixture
def tw() -> Iterator[TaskWarrior]:
    # Create some temporary config stuff
    _, fname = tempfile.mkstemp(prefix="taskw_ng-testsrc")
    dname = tempfile.mkdtemp(prefix="taskw_ng-tests-data")

    with open(fname, "w") as f:
        f.writelines(
            [
                "data.location=%s\n" % dname,
                "uda.somestring.label=Testing String\n",
                "uda.somestring.type=string\n",
                "uda.somedate.label=Testing Date\n",
                "uda.somedate.type=date\n",
                "uda.somenumber.label=Testing Number\n",
                "uda.somenumber.type=numeric\n",
            ]
        )

    # Create empty .data files
    for piece in ["completed", "pending", "undo"]:
        with open(os.path.sep.join([dname, piece + ".data"]), "w"):
            pass

    # Create the taskwarrior db object that each test will use.
    tw = TaskWarrior(config_filename=fname, marshal=True)
    yield tw

    # cleanup
    os.remove(fname)
    shutil.rmtree(dname)


def test_set_dep_on_one_uuid(tw: TaskWarrior):
    task1 = tw.task_add("task1")
    task2 = tw.task_add("task2", depends=[task1["uuid"]])
    assert task2["depends"][0] == task1["uuid"]


def test_set_dep_on_two_uuid(tw: TaskWarrior):
    task1 = tw.task_add("task1")
    task2 = tw.task_add("task2")
    depends = [task1["uuid"], task2["uuid"]]
    task3 = tw.task_add("task3", depends=depends)
    assert set(task3["depends"]) == set([task1["uuid"], task2["uuid"]])
