import copy
import glob
import json
import os
import subprocess
import tempfile

import conda_smithy
import pytest
from conda.models.version import VersionOrder

from conda_forge_tick.feedstock_parser import load_feedstock_containerized
from conda_forge_tick.lazy_json_backends import (
    LazyJson,
    dumps,
    lazy_json_override_backends,
)
from conda_forge_tick.os_utils import get_user_execute_permissions, pushd
from conda_forge_tick.provide_source_code import provide_source_code_containerized
from conda_forge_tick.rerender_feedstock import (
    rerender_feedstock_containerized,
    rerender_feedstock_local,
)
from conda_forge_tick.solver_checks import is_recipe_solvable
from conda_forge_tick.update_upstream_versions import (
    all_version_sources,
    get_latest_version_containerized,
)
from conda_forge_tick.utils import parse_meta_yaml_containerized, run_container_task

HAVE_CONTAINERS = (
    subprocess.run(["docker", "--version"], capture_output=True).returncode == 0
)

if HAVE_CONTAINERS:
    HAVE_TEST_IMAGE = False
    try:
        for line in subprocess.run(
            [
                "docker",
                "images",
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines():
            image = json.loads(line)
            if image["Repository"] == "conda-forge-tick" and image["Tag"] == "test":
                HAVE_TEST_IMAGE = True
                break
    except subprocess.CalledProcessError as e:
        print(
            f"Could not list local docker images due "
            f"to error {e}. Skipping container tests!"
        )


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_get_latest_version(use_containers):
    data = run_container_task(
        "get-latest-version",
        ["--existing-feedstock-node-attrs", "conda-smithy"],
    )
    assert VersionOrder(data["new_version"]) >= VersionOrder(conda_smithy.__version__)


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_get_latest_version_json(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/conda-smithy.json") as lzj,
    ):
        existing_feedstock_node_attrs = dumps(lzj.data)

        data = run_container_task(
            "get-latest-version",
            [
                "--existing-feedstock-node-attrs",
                existing_feedstock_node_attrs,
            ],
        )
        assert VersionOrder(data["new_version"]) >= VersionOrder(
            conda_smithy.__version__
        )


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_get_latest_version_containerized(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/conda-smithy.json") as lzj,
    ):
        attrs = copy.deepcopy(lzj.data)

        data = get_latest_version_containerized(
            "conda-smithy", attrs, all_version_sources()
        )
        assert VersionOrder(data["new_version"]) >= VersionOrder(
            conda_smithy.__version__
        )


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_get_latest_version_containerized_mpas_tools(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/mpas_tools.json") as lzj,
    ):
        attrs = copy.deepcopy(lzj.data)

        data = get_latest_version_containerized(
            "mpas_tools", attrs, all_version_sources()
        )
        assert data["new_version"] is not False


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_parse_feedstock(use_containers):
    with tempfile.TemporaryDirectory() as tmpdir, pushd(tmpdir):
        data = run_container_task(
            "parse-feedstock",
            ["--existing-feedstock-node-attrs", "conda-smithy"],
        )

        with (
            lazy_json_override_backends(["github"], use_file_cache=False),
            LazyJson("node_attrs/conda-smithy.json") as lzj,
        ):
            attrs = copy.deepcopy(lzj.data)

        assert data["feedstock_name"] == attrs["feedstock_name"]
        assert not data["parsing_error"]


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_parse_feedstock_json(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/conda-smithy.json") as lzj,
    ):
        attrs = copy.deepcopy(lzj.data)
        existing_feedstock_node_attrs = dumps(lzj.data)

        data = run_container_task(
            "parse-feedstock",
            ["--existing-feedstock-node-attrs", existing_feedstock_node_attrs],
        )
        assert data["feedstock_name"] == attrs["feedstock_name"]
        assert not data["parsing_error"]


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_load_feedstock_containerized(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/conda-smithy.json") as lzj,
    ):
        attrs = copy.deepcopy(lzj.data)

        data = load_feedstock_containerized("conda-smithy", attrs)
        assert data["feedstock_name"] == attrs["feedstock_name"]
        assert not data["parsing_error"]


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_load_feedstock_containerized_mpas_tools(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/mpas_tools.json") as lzj,
    ):
        attrs = copy.deepcopy(lzj.data)

        data = load_feedstock_containerized("mpas_tools", attrs)
        assert data["feedstock_name"] == attrs["feedstock_name"]
        assert not data["parsing_error"]
        assert data["raw_meta_yaml"] == attrs["raw_meta_yaml"]


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_parse_meta_yaml_containerized(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
        lazy_json_override_backends(["github"], use_file_cache=False),
        LazyJson("node_attrs/conda-smithy.json") as lzj,
    ):
        attrs = copy.deepcopy(lzj.data)

        data = parse_meta_yaml_containerized(
            attrs["raw_meta_yaml"],
        )
        assert data["package"]["name"] == "conda-smithy"


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_rerender_feedstock_containerized_same_as_local(
    use_containers, capfd
):
    with (
        tempfile.TemporaryDirectory() as tmpdir_cont,
        tempfile.TemporaryDirectory() as tmpdir_local,
    ):
        assert tmpdir_cont != tmpdir_local

        with pushd(tmpdir_cont):
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/conda-forge/conda-forge-feedstock-check-solvable-feedstock.git",
                ]
            )
            # make sure rerender happens
            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                cmds = [
                    ["git", "rm", "-f", ".gitignore"],
                    ["git", "rm", "-rf", ".scripts"],
                    ["git", "config", "user.email", "conda@conda.conda"],
                    ["git", "config", "user.name", "conda c. conda"],
                    ["git", "commit", "-m", "test commit"],
                ]
                for cmd in cmds:
                    subprocess.run(
                        cmd,
                        check=True,
                    )

            try:
                msg = rerender_feedstock_containerized(
                    os.path.join(
                        tmpdir_cont, "conda-forge-feedstock-check-solvable-feedstock"
                    ),
                )
            finally:
                captured = capfd.readouterr()
                print(f"out: {captured.out}\nerr: {captured.err}")

            if "git commit -m " in captured.err:
                assert (
                    msg is not None
                ), f"msg: {msg}\nout: {captured.out}\nerr: {captured.err}"
                assert msg.startswith(
                    "MNT:"
                ), f"msg: {msg}\nout: {captured.out}\nerr: {captured.err}"
            else:
                assert (
                    msg is None
                ), f"msg: {msg}\nout: {captured.out}\nerr: {captured.err}"

        with pushd(tmpdir_local):
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/conda-forge/conda-forge-feedstock-check-solvable-feedstock.git",
                ]
            )
            # make sure rerender happens
            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                cmds = [
                    ["git", "rm", "-f", ".gitignore"],
                    ["git", "rm", "-rf", ".scripts"],
                    ["git", "config", "user.email", "conda@conda.conda"],
                    ["git", "config", "user.name", "conda c. conda"],
                    ["git", "commit", "-m", "test commit"],
                ]
                for cmd in cmds:
                    subprocess.run(
                        cmd,
                        check=True,
                    )

            try:
                local_msg = rerender_feedstock_local(
                    os.path.join(
                        tmpdir_local, "conda-forge-feedstock-check-solvable-feedstock"
                    ),
                )
            finally:
                local_captured = capfd.readouterr()
                print(f"out: {local_captured.out}\nerr: {local_captured.err}")

        assert msg == local_msg

        # now compare files
        cont_fnames = set(
            glob.glob(os.path.join(tmpdir_cont, "**", "*"), recursive=True)
        )
        local_fnames = set(
            glob.glob(os.path.join(tmpdir_local, "**", "*"), recursive=True)
        )

        rel_cont_fnames = {os.path.relpath(fname, tmpdir_cont) for fname in cont_fnames}
        rel_local_fnames = {
            os.path.relpath(fname, tmpdir_local) for fname in local_fnames
        }
        assert (
            rel_cont_fnames == rel_local_fnames
        ), f"{rel_cont_fnames} != {rel_local_fnames}"

        for cfname in cont_fnames:
            lfname = os.path.join(tmpdir_local, os.path.relpath(cfname, tmpdir_cont))
            if not os.path.isdir(cfname):
                with open(cfname, "rb") as f:
                    cdata = f.read()
                with open(lfname, "rb") as f:
                    ldata = f.read()
                assert cdata == ldata, f"{cfname} not equal to local"


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_rerender_feedstock_containerized_empty(use_containers):
    with tempfile.TemporaryDirectory() as tmpdir_local:
        # first run the rerender locally
        with pushd(tmpdir_local):
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/conda-forge/conda-forge-feedstock-check-solvable-feedstock.git",
                ]
            )
            # make sure rerender happens
            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                cmds = [
                    ["git", "rm", "-f", ".gitignore"],
                    ["git", "rm", "-rf", ".scripts"],
                    ["git", "config", "user.email", "conda@conda.conda"],
                    ["git", "config", "user.name", "conda c. conda"],
                    ["git", "commit", "-m", "test commit"],
                ]
                for cmd in cmds:
                    subprocess.run(
                        cmd,
                        check=True,
                    )

            local_msg = rerender_feedstock_local(
                os.path.join(
                    tmpdir_local, "conda-forge-feedstock-check-solvable-feedstock"
                ),
            )

            assert local_msg is not None
            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                subprocess.run(
                    ["git", "commit", "-am", local_msg],
                    check=True,
                )

        # now run in container and make sure commit message is None
        msg = rerender_feedstock_containerized(
            os.path.join(
                tmpdir_local, "conda-forge-feedstock-check-solvable-feedstock"
            ),
        )

        assert msg is None


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_rerender_feedstock_containerized_permissions(use_containers):
    with tempfile.TemporaryDirectory() as tmpdir:
        with pushd(tmpdir):
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/conda-forge/conda-forge-feedstock-check-solvable-feedstock.git",
                ]
            )

            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                orig_perms_bl = os.stat("build-locally.py").st_mode
                print(
                    f"\n\ncloned permissions for build-locally.py: {orig_perms_bl:#o}\n\n"
                )
                orig_exec = get_user_execute_permissions(".")

            local_msg = rerender_feedstock_local(
                os.path.join(tmpdir, "conda-forge-feedstock-check-solvable-feedstock"),
            )

            if local_msg is not None:
                with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                    cmds = [
                        ["git", "config", "user.email", "conda@conda.conda"],
                        ["git", "config", "user.name", "conda c. conda"],
                        ["git", "commit", "-am", local_msg],
                    ]
                    for cmd in cmds:
                        subprocess.run(cmd, check=True)

            # now change permissions
            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                orig_perms_bl = os.stat("build-locally.py").st_mode
                print(
                    f"\n\ninput permissions for build-locally.py: {orig_perms_bl:#o}\n\n"
                )
                local_rerend_exec = get_user_execute_permissions(".")

                cmds = [
                    ["chmod", "655", "build-locally.py"],
                    ["git", "add", "build-locally.py"],
                    ["git", "config", "user.email", "conda@conda.conda"],
                    ["git", "config", "user.name", "conda c. conda"],
                    ["git", "commit", "-m", "test commit for rerender"],
                ]
                for cmd in cmds:
                    subprocess.run(
                        cmd,
                        check=True,
                    )

            msg = rerender_feedstock_containerized(
                os.path.join(tmpdir, "conda-forge-feedstock-check-solvable-feedstock"),
            )
            assert msg is not None

            with pushd("conda-forge-feedstock-check-solvable-feedstock"):
                perms_bl = os.stat("build-locally.py").st_mode
                print(f"\n\nfinal permissions for build-locally.py: {perms_bl:#o}\n\n")
                cont_rerend_exec = get_user_execute_permissions(".")

            assert orig_exec == local_rerend_exec
            assert orig_exec == cont_rerend_exec


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_provide_source_code_containerized(use_containers):
    with (
        tempfile.TemporaryDirectory() as tmpdir,
        pushd(tmpdir),
    ):
        subprocess.run(
            [
                "git",
                "clone",
                "https://github.com/conda-forge/conda-smithy-feedstock.git",
            ]
        )

        with provide_source_code_containerized(
            "conda-smithy-feedstock/recipe"
        ) as source_dir:
            assert os.path.exists(source_dir)
            assert os.path.isdir(source_dir)
            assert "conda_smithy" in os.listdir(source_dir)
            assert "pyproject.toml" in os.listdir(source_dir)


@pytest.mark.skipif(
    not (HAVE_CONTAINERS and HAVE_TEST_IMAGE), reason="containers not available"
)
def test_container_tasks_is_recipe_solvable_containerized(use_containers):
    with tempfile.TemporaryDirectory() as tmpdir:
        with pushd(tmpdir):
            subprocess.run(
                [
                    "git",
                    "clone",
                    "https://github.com/conda-forge/conda-forge-feedstock-check-solvable-feedstock.git",
                ]
            )

        res_cont = is_recipe_solvable(
            os.path.join(tmpdir, "conda-forge-feedstock-check-solvable-feedstock"),
            use_container=True,
        )
        assert res_cont[0], res_cont

        res_local = is_recipe_solvable(
            os.path.join(tmpdir, "conda-forge-feedstock-check-solvable-feedstock"),
            use_container=False,
        )
        assert res_local[0], res_local

        assert res_cont == res_local
