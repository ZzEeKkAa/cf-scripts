import copy
import json
import subprocess

import conda_smithy

from conda_forge_tick.lazy_json_backends import (
    LazyJson,
    dumps,
    lazy_json_override_backends,
)
from conda_forge_tick.update_upstream_versions import (
    all_version_sources,
    get_latest_version_containerized,
)


def test_container_tasks_version():
    res = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-t",
            "conda-forge-tick:test",
            "python",
            "/opt/autotick-bot/docker/run_bot_task.py",
            "update-version",
            "--existing-feedstock-node-attrs=conda-smithy",
        ],
        capture_output=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout.decode("utf-8"))
    assert data["new_version"] == conda_smithy.__version__


def test_container_tasks_version_json():
    with lazy_json_override_backends(["github"], use_file_cache=False):
        with LazyJson("node_attrs/conda-smithy.json") as lzj:
            existing_feedstock_node_attrs = dumps(lzj.data)

    res = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-t",
            "conda-forge-tick:test",
            "python",
            "/opt/autotick-bot/docker/run_bot_task.py",
            "update-version",
            "--existing-feedstock-node-attrs",
            existing_feedstock_node_attrs,
        ],
        capture_output=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout.decode("utf-8"))
    assert data["new_version"] == conda_smithy.__version__


def test_get_latest_version_containerized():
    with lazy_json_override_backends(["github"], use_file_cache=False):
        with LazyJson("node_attrs/conda-smithy.json") as lzj:
            attrs = copy.deepcopy(lzj.data)

    data = get_latest_version_containerized(
        "conda-smithy", attrs, all_version_sources()
    )
    assert data["new_version"] == conda_smithy.__version__