from pathlib import Path


MODEL_NAME = "qwen3:4b"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

TOP_K = 8
MAX_DEBUG_RETRIES = 3

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "dist",
    "build"
}

ALLOWED_EXTENSIONS = {
    ".py"
}

BACKUP_DIR = Path("backups")