import subprocess


def run_git(repo_path, args):
    result = subprocess.run(
        ["git", *args],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=60,
    )

    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def is_git_repository(repo_path):
    result = run_git(
        repo_path,
        [
            "rev-parse",
            "--is-inside-work-tree",
        ],
    )

    return (
        result["returncode"] == 0
        and result["stdout"].lower() == "true"
    )


def get_git_status(repo_path):
    result = run_git(
        repo_path,
        [
            "status",
            "--short",
        ],
    )

    if result["returncode"] != 0:
        raise RuntimeError(
            result["stderr"]
            or "Failed to read Git status."
        )

    return result["stdout"]


def get_git_diff(repo_path):
    result = run_git(
        repo_path,
        [
            "diff",
        ],
    )

    if result["returncode"] != 0:
        raise RuntimeError(
            result["stderr"]
            or "Failed to generate Git diff."
        )

    return result["stdout"]


def create_commit(
    repo_path,
    message,
):
    if not message.strip():
        return {
            "success": False,
            "message": "Commit message cannot be empty.",
        }

    add_result = run_git(
        repo_path,
        [
            "add",
            "-A",
        ],
    )

    if add_result["returncode"] != 0:
        return {
            "success": False,
            "message": (
                add_result["stderr"]
                or "git add failed."
            ),
        }

    commit_result = run_git(
        repo_path,
        [
            "commit",
            "-m",
            message.strip(),
        ],
    )

    if commit_result["returncode"] != 0:
        return {
            "success": False,
            "message": (
                commit_result["stderr"]
                or commit_result["stdout"]
                or "Git commit failed."
            ),
        }

    return {
        "success": True,
        "message": (
            commit_result["stdout"]
            or "Git commit created successfully."
        ),
    }


def get_current_branch(repo_path):
    result = run_git(
        repo_path,
        [
            "branch",
            "--show-current",
        ],
    )

    if result["returncode"] != 0:
        raise RuntimeError(
            result["stderr"]
            or "Unable to determine current Git branch."
        )

    branch = result["stdout"].strip()

    if not branch:
        raise RuntimeError(
            "Git repository is currently in detached HEAD state."
        )

    return branch


def get_remotes(repo_path):
    result = run_git(
        repo_path,
        [
            "remote",
        ],
    )

    if result["returncode"] != 0:
        raise RuntimeError(
            result["stderr"]
            or "Unable to read Git remotes."
        )

    return [
        remote.strip()
        for remote in result["stdout"].splitlines()
        if remote.strip()
    ]


def get_remote_url(
    repo_path,
    remote="origin",
):
    result = run_git(
        repo_path,
        [
            "remote",
            "get-url",
            remote,
        ],
    )

    if result["returncode"] != 0:
        return None

    return result["stdout"].strip()


def push_current_branch(
    repo_path,
    remote="origin",
):
    if not is_git_repository(
        repo_path
    ):
        return {
            "success": False,
            "message": "The selected folder is not a Git repository.",
        }

    try:
        branch = get_current_branch(
            repo_path
        )

    except Exception as error:
        return {
            "success": False,
            "message": str(error),
        }

    try:
        remotes = get_remotes(
            repo_path
        )

    except Exception as error:
        return {
            "success": False,
            "message": str(error),
        }

    if not remotes:
        return {
            "success": False,
            "message": (
                "No Git remote is configured. "
                "Add a GitHub remote before pushing."
            ),
        }

    if remote not in remotes:
        return {
            "success": False,
            "message": (
                f"Git remote '{remote}' does not exist. "
                f"Available remotes: {', '.join(remotes)}"
            ),
        }

    result = run_git(
        repo_path,
        [
            "push",
            remote,
            branch,
        ],
    )

    if result["returncode"] != 0:
        message = (
            result["stderr"]
            or result["stdout"]
            or "Git push failed."
        )

        return {
            "success": False,
            "message": message,
        }

    message = (
        result["stdout"]
        or result["stderr"]
        or f"Successfully pushed {branch} to {remote}."
    )

    return {
        "success": True,
        "message": message,
    }


if __name__ == "__main__":
    print(
        "git_tools.py loaded successfully"
    )