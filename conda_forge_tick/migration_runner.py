import logging
import os

from conda_forge_tick.contexts import FeedstockContext

logger = logging.getLogger(__name__)


def run_migration(
    *,
    migrator,
    feedstock_dir,
    package_name,
    feedstock_name,
    node_attrs,
    default_branch,
    use_container=False,
    **kwargs,
):
    in_container = os.environ.get("CF_TICK_IN_CONTAINER", "false") == "true"
    if use_container is None:
        use_container = not in_container

    if use_container and not in_container:
        return run_migration_containerized(
            migrator=migrator,
            feedstock_dir=feedstock_dir,
            package_name=package_name,
            feedstock_name=feedstock_name,
            node_attrs=node_attrs,
            default_branch=default_branch,
            **kwargs,
        )
    else:
        return run_migration_local(
            migrator=migrator,
            feedstock_dir=feedstock_dir,
            package_name=package_name,
            feedstock_name=feedstock_name,
            node_attrs=node_attrs,
            default_branch=default_branch,
            **kwargs,
        )


def run_migration_containerized(
    *,
    migrator,
    feedstock_dir,
    package_name,
    feedstock_name,
    node_attrs,
    default_branch,
    **kwargs,
):
    # args = []

    # if timeout is not None:
    #     args += ["--timeout", str(timeout)]

    # with tempfile.TemporaryDirectory() as tmpdir:
    #     tmp_feedstock_dir = os.path.join(tmpdir, os.path.basename(feedstock_dir))
    #     sync_dirs(
    #         feedstock_dir, tmp_feedstock_dir, ignore_dot_git=True, update_git=False
    #     )

    #     perms = get_user_execute_permissions(feedstock_dir)
    #     with open(
    #         os.path.join(tmpdir, f"permissions-{os.path.basename(feedstock_dir)}.json"),
    #         "w",
    #     ) as f:
    #         json.dump(perms, f)

    #     chmod_plus_rwX(tmpdir, recursive=True)

    #     logger.debug(f"host feedstock dir {feedstock_dir}: {os.listdir(feedstock_dir)}")
    #     logger.debug(
    #         f"copied host feedstock dir {tmp_feedstock_dir}: {os.listdir(tmp_feedstock_dir)}"
    #     )

    #     data = run_container_task(
    #         "rerender-feedstock",
    #         args,
    #         mount_readonly=False,
    #         mount_dir=tmpdir,
    #     )

    #     if data["commit_message"] is not None:
    #         sync_dirs(
    #             tmp_feedstock_dir,
    #             feedstock_dir,
    #             ignore_dot_git=True,
    #             update_git=True,
    #         )
    #         reset_permissions_with_user_execute(feedstock_dir, data["permissions"])

    #     # When tempfile removes tempdir, it tries to reset permissions on subdirs.
    #     # This causes a permission error since the subdirs were made by the user
    #     # in the container. So we remove the subdir we made before cleaning up.
    #     shutil.rmtree(tmp_feedstock_dir)

    # return data["commit_message"]
    raise NotImplementedError("Containerized migrations are not yet implemented!")
    pass


def run_migration_local(
    *,
    migrator,
    feedstock_dir,
    package_name,
    feedstock_name,
    node_attrs,
    default_branch,
    **kwargs,
):
    feedstock_ctx = FeedstockContext(
        package_name=package_name,
        feedstock_name=feedstock_name,
        attrs=node_attrs,
    )
    feedstock_ctx.default_branch = default_branch
    recipe_dir = os.path.join(feedstock_dir, "recipe")

    data = {
        "migrate_return_value": None,
        "commit_message": None,
        "pr_title": None,
        "pr_body": None,
    }

    migrator.run_pre_piggyback_migrations(recipe_dir, feedstock_ctx.attrs, **kwargs)

    data["migrate_return_value"] = migrator.migrate(
        recipe_dir, feedstock_ctx.attrs, **kwargs
    )
    if not data["migrate_return_value"]:
        return data

    migrator.run_post_piggyback_migrations(recipe_dir, feedstock_ctx.attrs, **kwargs)

    data["commit_message"] = migrator.commit_message(feedstock_ctx)
    data["pr_body"] = migrator.pr_body(feedstock_ctx)
    data["pr_title"] = migrator.pr_title(feedstock_ctx)

    return data
