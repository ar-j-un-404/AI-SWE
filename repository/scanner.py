from pathlib import Path

from config import (
    IGNORED_DIRECTORIES,
    ALLOWED_EXTENSIONS
)


def should_ignore(path):
    for part in path.parts:
        if part in IGNORED_DIRECTORIES:
            return True

    return False


def scan_repository(repo_path):
    repo_path = Path(repo_path).resolve()

    if not repo_path.exists():
        raise FileNotFoundError(
            f"Repository does not exist: {repo_path}"
        )

    if not repo_path.is_dir():
        raise ValueError(
            "Repository path must be a directory."
        )

    files = []

    for path in repo_path.rglob("*"):

        if not path.is_file():
            continue

        relative_path = path.relative_to(repo_path)

        if should_ignore(relative_path):
            continue

        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        try:
            content = path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:
            content = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

        files.append(
            {
                "path": str(relative_path),
                "absolute_path": str(path),
                "content": content
            }
        )

    return files