from pathlib import Path
import shutil
import time

from config import BACKUP_DIR


def ensure_safe_path(
    repo_path,
    relative_path
):
    repo_path = Path(
        repo_path
    ).resolve()

    target = (
        repo_path
        / relative_path
    ).resolve()

    try:
        target.relative_to(
            repo_path
        )

    except ValueError:
        raise ValueError(
            "Attempted to edit outside repository."
        )

    return target


def create_backup(
    repo_path,
    relative_path
):
    source = ensure_safe_path(
        repo_path,
        relative_path
    )

    if not source.exists():
        return None

    timestamp = int(
        time.time() * 1000
    )

    backup_path = (
        BACKUP_DIR
        / str(timestamp)
        / relative_path
    )

    backup_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    shutil.copy2(
        source,
        backup_path
    )

    return backup_path


def apply_patches(
    repo_path,
    patches
):
    applied = []
    backed_up_files = {}

    for patch in patches:
        relative_path = patch["path"]
        action = patch["action"]

        target = ensure_safe_path(
            repo_path,
            relative_path
        )

        if action == "create":
            if target.exists():
                raise ValueError(
                    f"Cannot create {relative_path}: "
                    "file already exists."
                )

            target.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            target.write_text(
                patch["content"],
                encoding="utf-8"
            )

            applied.append(
                {
                    "path": relative_path,
                    "action": "create",
                    "backup": None
                }
            )

        elif action == "modify":
            if not target.exists():
                raise FileNotFoundError(
                    f"Cannot modify {relative_path}: "
                    "file does not exist."
                )

            if relative_path not in backed_up_files:
                backup = create_backup(
                    repo_path,
                    relative_path
                )

                backed_up_files[
                    relative_path
                ] = backup

            content = target.read_text(
                encoding="utf-8"
            )

            find_text = patch["find"]
            replace_text = patch["replace"]

            count = content.count(
                find_text
            )

            if count == 0:
                raise ValueError(
                    f"Patch failed for {relative_path}: "
                    "FIND text not found."
                )

            if count > 1:
                raise ValueError(
                    f"Patch failed for {relative_path}: "
                    "FIND text matched multiple times."
                )

            new_content = content.replace(
                find_text,
                replace_text,
                1
            )

            target.write_text(
                new_content,
                encoding="utf-8"
            )

            applied.append(
                {
                    "path": relative_path,
                    "action": "modify",
                    "backup": str(
                        backed_up_files[
                            relative_path
                        ]
                    )
                }
            )

        else:
            raise ValueError(
                f"Unknown patch action: {action}"
            )

    return applied


def rollback_changes(
    repo_path,
    applied_changes
):
    restored = set()

    for item in reversed(
        applied_changes
    ):
        relative_path = item["path"]

        target = ensure_safe_path(
            repo_path,
            relative_path
        )

        if item["action"] == "create":
            if target.exists():
                target.unlink()

            continue

        if relative_path in restored:
            continue

        backup = item.get(
            "backup"
        )

        if backup:
            backup_path = Path(
                backup
            )

            if backup_path.exists():
                target.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                shutil.copy2(
                    backup_path,
                    target
                )

        restored.add(
            relative_path
        )