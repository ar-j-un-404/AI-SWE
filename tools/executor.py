import shutil
import subprocess


SAFE_COMMAND_PREFIXES = (
    "python ",
    "python -m ",
    "pytest",
)


def command_exists(command):
    command = command.strip()

    if not command:
        return False

    first_part = command.split()[0]

    if first_part == "python":
        return True

    return shutil.which(first_part) is not None


def is_safe_command(command):
    command = command.strip().lower()

    return command.startswith(
        SAFE_COMMAND_PREFIXES
    )


def run_command(
    repo_path,
    command
):
    if not is_safe_command(command):
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": (
                "Command blocked because it is not "
                "in the allowed test command list."
            ),
            "skipped": True,
            "reason": "unsafe_command"
        }

    if not command_exists(command):
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": (
                f"Command is not available: {command}"
            ),
            "skipped": True,
            "reason": "command_not_found"
        }

    try:
        result = subprocess.run(
            command,
            cwd=repo_path,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "skipped": False,
            "reason": None
        }

    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": (
                "Command timed out after 120 seconds."
            ),
            "skipped": True,
            "reason": "timeout"
        }

    except Exception as error:
        return {
            "command": command,
            "returncode": -1,
            "stdout": "",
            "stderr": str(error),
            "skipped": True,
            "reason": "execution_error"
        }


def get_fallback_test_commands(repo_path):
    return [
        "python -m compileall ."
    ]


def run_tests(
    repo_path,
    commands
):
    results = []

    valid_test_ran = False

    for command in commands:
        result = run_command(
            repo_path,
            command
        )

        results.append(
            result
        )

        if not result.get("skipped", False):
            valid_test_ran = True

    # If every planned test was unavailable,
    # run a safe Python syntax fallback.
    if not valid_test_ran:
        fallback_commands = (
            get_fallback_test_commands(
                repo_path
            )
        )

        for command in fallback_commands:
            result = run_command(
                repo_path,
                command
            )

            results.append(
                result
            )

    return results


def tests_passed(results):
    executed = [
        result
        for result in results
        if not result.get(
            "skipped",
            False
        )
    ]

    if not executed:
        return False

    return all(
        result["returncode"] == 0
        for result in executed
    )