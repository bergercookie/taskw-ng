import datetime
import os
import shutil
import tempfile

import dateutil.tz
import pytest

from taskw_ng.warrior import TaskWarrior

TASK = {
    "description": "task 2 http://www.google.com/",
    "entry": "1325011643",
    "project": "work",
    "start": "1326079920",
    "status": "pending",
    "uuid": "c1c431ea-f0dc-4683-9a20-e64fcfa65fd1",
}


# fixtures ------------------------------------------------------------------------------------
@pytest.fixture
def empty_taskrc():
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

    yield fname

    # cleanup
    os.remove(fname)
    shutil.rmtree(dname)


@pytest.fixture
def tw(empty_taskrc: str) -> TaskWarrior:
    tw = TaskWarrior(config_filename=empty_taskrc)
    return tw


@pytest.fixture
def tw_marshal(empty_taskrc: str) -> TaskWarrior:
    tw_marshal = TaskWarrior(config_filename=empty_taskrc, marshal=True)
    return tw_marshal


# tests ---------------------------------------------------------------------------------------


def test_has_two_categories(tw: TaskWarrior):
    tasks = tw.load_tasks()
    assert len(tasks) == 2
    assert "pending" in tasks
    assert "completed" in tasks


def test_empty_db(tw: TaskWarrior):
    tasks = tw.load_tasks()
    assert len(sum(tasks.values(), [])) == 0


def test_add(tw: TaskWarrior):
    tw.task_add("foobar")
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1


def test_unchanging_load_tasks(tw: TaskWarrior):
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0


def test_completion_raising_unspecified(tw: TaskWarrior):
    with pytest.raises(KeyError):
        tw.task_done()


def test_completing_task_by_id_unspecified(tw: TaskWarrior):
    tw.task_add("foobar")
    tw.task_done(id=1)
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0
    assert len(tasks["completed"]) == 1
    assert len(sum(tasks.values(), [])) == 1
    assert tasks["completed"][0]["end"] is not None
    assert tasks["completed"][0]["status"] == "completed"


def test_completing_task_by_id_specified(tw: TaskWarrior):
    tw.task_add("foobar")
    tw.task_done(id=1)
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0
    assert len(tasks["completed"]) == 1
    assert len(sum(tasks.values(), [])) == 1
    assert tasks["completed"][0]["status"] == "completed"


def test_completing_task_by_id_retrieved(tw: TaskWarrior):
    task = tw.task_add("foobar")
    tw.task_done(id=task["id"])
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0
    assert len(tasks["completed"]) == 1
    assert len(sum(tasks.values(), [])) == 1
    assert tasks["completed"][0]["status"] == "completed"


def test_completing_task_by_uuid(tw: TaskWarrior):
    tw.task_add("foobar")
    uuid = tw.load_tasks()["pending"][0]["uuid"]
    tw.task_done(uuid=uuid)
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0
    assert len(tasks["completed"]) == 1
    assert len(sum(tasks.values(), [])) == 1
    assert tasks["completed"][0]["status"] == "completed"


def test_get_task_mismatch(tw: TaskWarrior):
    tw.task_add("foobar")
    tw.task_add("bazbar")
    uuid = tw.load_tasks()["pending"][0]["uuid"]
    with pytest.raises(KeyError):
        tw.get_task(id=2, uuid=uuid)  # which one?


def test_updating_task(tw: TaskWarrior):
    tw.task_add("foobar")

    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1

    task = tasks["pending"][0]
    task["priority"] = "L"
    tw.task_update(task)

    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    assert tasks["pending"][0]["priority"] == "L"

    try:
        # Shellout mode returns the correct urgency, so,
        # let's just not compare for now.
        del tasks["pending"][0]["urgency"]
        del task["urgency"]

        # Also, experimental mode returns the id.  So, avoid comparing.
        del tasks["pending"][0]["id"]
    except Exception:
        pass

    # But Task 2.4.0 puts the modified field in earlier
    if "modified" in task:
        del task["modified"]

    assert tasks["pending"][0] == task


def test_update_exc(tw: TaskWarrior):
    task = dict(description="lol")
    with pytest.raises(KeyError):
        tw.task_update(task)


def test_add_complicated(tw: TaskWarrior):
    tw.task_add("foobar", uuid="1234-1234", project="some_project")
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1


def test_add_timestamp(tw: TaskWarrior):
    tw.task_add(
        "foobar",
        uuid="1234-1234",
        project="some_project",
        entry="20110101T000000Z",
    )
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    assert tasks["pending"][0]["entry"] == "20110101T000000Z"


def test_add_datetime(tw: TaskWarrior):
    tw.task_add(
        "foobar",
        uuid="1234-1234",
        project="some_project",
        entry=datetime.datetime(2011, 1, 1, tzinfo=dateutil.tz.tzutc()),
    )
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    # The exact string we get back is dependent on your current TZ
    # ... we'll just "roughly" test it instead of mocking.
    assert tasks["pending"][0]["entry"].startswith("20110101T")


def test_add_with_uda_string(tw: TaskWarrior):
    tw.task_add(
        "foobar",
        somestring="this is a uda",
    )
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    task = tasks["pending"][0]

    assert task["somestring"] == "this is a uda"


def test_add_with_uda_date(tw: TaskWarrior):
    tw.task_add(
        "foobar",
        somedate=datetime.datetime(2011, 1, 1, tzinfo=dateutil.tz.tzutc()),
    )
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    task = tasks["pending"][0]

    assert task["somedate"].startswith("20110101T")


def test_remove_uda_string(tw: TaskWarrior):
    # Check that a string UDA is removed from a task when its
    # value is set to None
    task = tw.task_add(
        "foobar",
        somestring="this is a uda",
    )
    task["somestring"] = None
    id, task = tw.task_update(task)
    with pytest.raises(KeyError):
        task["somestring"]


def test_remove_uda_date(tw: TaskWarrior):
    # Check that a date UDA is removed from a task when its
    # value is set to None
    task = tw.task_add(
        "foobar",
        somedate=datetime.datetime(2011, 1, 1),
    )
    task["somedate"] = None
    id, task = tw.task_update(task)
    with pytest.raises(KeyError):
        task["somedate"]


def test_remove_uda_numeric(tw: TaskWarrior):
    # Check that a numeric UDA is removed from a task when its
    # value is set to None
    task = tw.task_add(
        "foobar",
        somenumber=15,
    )
    task["somenumber"] = None
    id, task = tw.task_update(task)
    with pytest.raises(KeyError):
        task["somenumber"]


def test_completing_completed_task(tw: TaskWarrior):
    task = tw.task_add("foobar")
    tw.task_done(uuid=task["uuid"])
    with pytest.raises(ValueError):
        tw.task_done(uuid=task["uuid"])


def test_updating_completed_task(tw: TaskWarrior):
    task = tw.task_add("foobar")
    task = tw.task_done(uuid=task["uuid"])
    task["priority"] = "L"
    id, task = tw.task_update(task)
    assert task["priority"] == "L"


def test_get_task_completed(tw: TaskWarrior):
    task = tw.task_add("foobar")
    task = tw.task_done(uuid=task["uuid"])

    id, _task = tw.get_task(uuid=task["uuid"])
    assert id is None
    assert _task["uuid"] == task["uuid"]


def test_load_task_pending_command(tw: TaskWarrior):
    tasks = tw.load_tasks(command="pending")
    assert len(tasks) == 1
    assert "pending" in tasks


def test_load_task_completed_command(tw: TaskWarrior):
    tasks = tw.load_tasks(command="completed")
    assert len(tasks) == 1
    assert "completed" in tasks


def test_load_task_with_unknown_command(tw: TaskWarrior):
    with pytest.raises(ValueError):
        tw.load_tasks(command="foobar")


def test_updating_deleted_task(tw: TaskWarrior):
    task = tw.task_add("foobar")
    task = tw.task_delete(uuid=task["uuid"])
    task["priority"] = "L"
    id, task = tw.task_update(task)
    assert task["priority"] == "L"


def test_delete(tw: TaskWarrior):
    task = tw.task_add("foobar")
    tw.task_delete(uuid=task["uuid"])
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 0


def test_delete_already_deleted(tw: TaskWarrior):
    task = tw.task_add("foobar")
    tw.task_delete(uuid=task["uuid"])
    with pytest.raises(ValueError):
        tw.task_delete(uuid=task["uuid"])


def test_load_tasks_with_one_each(tw: TaskWarrior):
    tw.task_add("foobar1")
    task2 = tw.task_add("foobar2")
    task2 = tw.task_done(uuid=task2["uuid"])
    tasks = tw.load_tasks()
    assert len(tasks["pending"]) == 1
    assert len(tasks["completed"]) == 1

    # For issue #26, I thought this would raise an exception...
    tw.get_task(description="foobar1")


def test_filtering_simple(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tasks = tw.filter_tasks(
        {
            "description.contains": "foobar2",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2


def test_filtering_brace(tw: TaskWarrior):
    tw.task_add("[foobar1]")
    tw.task_add("[foobar2]")
    tasks = tw.filter_tasks(
        {
            "description.contains": "[foobar2]",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2


def test_filtering_quote(tw: TaskWarrior):
    tw.task_add("[foobar1]")
    tw.task_add('"foobar2"')
    tasks = tw.filter_tasks(
        {
            "description.contains": '"foobar2"',
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2


def test_filtering_plus(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foobar+")
    tasks = tw.filter_tasks(
        {
            "description.contains": '"foobar+"',
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filtering_minus(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foobar-")
    tasks = tw.filter_tasks(
        {
            "description.contains": '"foobar-"',
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filtering_colon(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foobar:")
    tasks = tw.filter_tasks(
        {
            "description.contains": "foobar:",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filtering_qmark(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foo?bar")
    tasks = tw.filter_tasks(
        {
            "description.contains": "oo?ba",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2


def test_filtering_qmark_not_contains(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foo?bar")
    tasks = tw.filter_tasks(
        {
            "description": "foo?bar",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 2


def test_filtering_semicolon(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foo;bar")
    tasks = tw.filter_tasks(
        {
            "description.contains": "foo;bar",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filtering_question_mark(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foo?bar")
    tasks = tw.filter_tasks(
        {
            "description.contains": "foo?bar",
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filtering_slash(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foo/bar")
    tasks = tw.filter_tasks(
        {
            "description.contains": '"foo/bar"',
        }
    )
    assert len(tasks) == 1
    assert tasks[0]["id"] == 3


def test_filtering_logic_disjunction(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foobar3")
    tasks = tw.filter_tasks(
        {
            "or": [
                ("description.has", "foobar1"),
                ("description.has", "foobar3"),
            ]
        }
    )
    assert len(tasks) == 2
    assert tasks[0]["id"] == 1
    assert tasks[1]["id"] == 3


def test_filtering_logic_conjunction(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foobar3")
    tasks = tw.filter_tasks(
        {
            "and": [
                ("description.has", "foobar1"),
                ("description.has", "foobar3"),
            ]
        }
    )
    assert len(tasks) == 0


def test_filtering_logic_conjunction_junction_whats_your_function(tw: TaskWarrior):
    tw.task_add("foobar1")
    tw.task_add("foobar2")
    tw.task_add("foobar3")
    tasks = tw.filter_tasks(
        {
            "and": [
                ("description", "foobar1"),
            ],
            "or": [
                ("status", "pending"),
                ("status", "waiting"),
            ],
        }
    )
    assert len(tasks) == 1


def test_annotation_escaping(tw: TaskWarrior):
    original = {"description": "re-opening the issue"}

    tw.task_add("foobar")
    task = tw.load_tasks()["pending"][0]
    task["annotations"] = [original]
    tw.task_update(task)

    task = tw.load_tasks()["pending"][0]
    tw.task_update(task)

    assert len(task["annotations"]) == 1
    assert task["annotations"][0]["description"] == original["description"]


def test_remove_uda_string_marshal(tw_marshal: TaskWarrior):
    # Check that a string UDA is removed from a task when its
    # value is set to None
    task = tw_marshal.task_add(
        "foobar",
        somestring="this is a uda",
    )
    task["somestring"] = None
    id, task = tw_marshal.task_update(task)
    with pytest.raises(KeyError):
        task["somestring"]


def test_remove_uda_date_marshal(tw_marshal: TaskWarrior):
    # Check that a date UDA is removed from a task when its
    # value is set to None
    task = tw_marshal.task_add(
        "foobar",
        somedate=datetime.datetime(2011, 1, 1),
    )
    task["somedate"] = None
    id, task = tw_marshal.task_update(task)
    with pytest.raises(KeyError):
        task["somedate"]


def test_remove_uda_numeric_marshal(tw_marshal: TaskWarrior):
    # Check that a numeric UDA is removed from a task when its
    # value is set to None
    task = tw_marshal.task_add(
        "foobar",
        somenumber=15,
    )
    task["somenumber"] = None
    _, task = tw_marshal.task_update(task)
    with pytest.raises(KeyError):
        task["somenumber"]


def test_add_and_retrieve_uda_string_url(tw: TaskWarrior):
    arbitrary_url = "http://www.someurl.com/1084/"

    tw.config_overrides["uda"] = {"someurl": {"label": "Some URL", "type": "string"}}
    tw.task_add(
        "foobar",
        someurl=arbitrary_url,
    )
    results = tw.filter_tasks({"someurl.is": arbitrary_url})
    assert len(results) == 1
    task = results[0]
    assert task["someurl"] == arbitrary_url


def test_add_and_retrieve_uda_string_url_in_parens(tw: TaskWarrior):
    arbitrary_url = "http://www.someurl.com/1084/"

    tw.config_overrides["uda"] = {"someurl": {"label": "Some URL", "type": "string"}}
    tw.task_add(
        "foobar",
        someurl=arbitrary_url,
    )
    results = tw.filter_tasks(
        {
            "and": [
                ("someurl.is", arbitrary_url),
            ],
        }
    )
    assert len(results) == 1
    task = results[0]
    assert task["someurl"] == arbitrary_url
