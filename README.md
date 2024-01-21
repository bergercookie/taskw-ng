# `taskw-ng` - Python API for the Taskwarrior DB

> This project is a continuation of the [taskw python
wrapper](https://github.com/ralphbean/taskw).

This is a python API for the [Taskwarrior](http://taskwarrior.org) command line
task manager.

It mainly contains the `taskw_ng.TaskWarrior` class.

## Getting `taskw-ng`

### Installing

Using `taskw-ng` requires that you first install [Taskwarrior](http://taskwarrior.org).

Installing it from http://pypi.org/project/taskw-ng is easy with `pip`:

```sh
pip install taskw-ng
```

## Examples

### Looking at tasks

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
tasks = w.load_tasks()
tasks.keys()
# ['completed', 'pending']
type(tasks['pending'])
# <type 'list'>
type(tasks['pending'][0])
# <type 'dict'>
```

### Adding tasks

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
w.task_add("Eat food")
w.task_add("Take a nap", priority="H", project="life", due="1359090000")
```

### Retrieving tasks

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
w.get_task(id=5)
```

### Updating tasks

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
id, task = w.get_task(id=14)
task['project'] = 'Updated project name'
w.task_update(task)
```

### Deleting tasks

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
w.task_delete(id=3)
```

### Completing tasks

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
w.task_done(id=46)
```

### Being Flexible

You can point `taskw-ng` at different Taskwarrior databases.

```python
from taskw_ng import TaskWarrior
w = TaskWarrior(config_filename="~/some_project/.taskrc")
w.task_add("Use taskw_ng.")
```

### Looking at the config

```python
from taskw_ng import TaskWarrior
w = TaskWarrior()
config = w.load_config()
config['data']['location']
# '/home/threebean/.task'
config['_forcecolor']
# 'yes'
```

### Using python-appropriate types (dates, UUIDs, etc)

```python
from taskw_ng import TaskWarrior
w = TaskWarrior(marshal=True)
w.get_task(id=10)
# should give the following:
# (10,
#  {
#   'description': 'Hello there!',
#   'entry': datetime.datetime(2014, 3, 14, 14, 18, 40, tzinfo=tzutc())
#   'id': 10,
#   'project': 'Saying Hello',
#   'status': 'pending',
#   'uuid': UUID('4882751a-3966-4439-9675-948b1152895c')
#  }
# )
```
