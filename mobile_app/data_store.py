"""
File-based data store for project persistence.
Enables session continuity across process restarts.
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import threading

DATA_DIR = "/workspace/project/polkiuy1/.project_data"
os.makedirs(DATA_DIR, exist_ok=True)

_lock = threading.Lock()


def _project_path(project_id: str) -> str:
    return os.path.join(DATA_DIR, f"{project_id}.json")


def save_project(project_id: str, project: Dict[str, Any]) -> None:
    """Persist project to disk."""
    with _lock:
        project['updated_at'] = datetime.now().isoformat()
        with open(_project_path(project_id), 'w') as f:
            json.dump(project, f, default=str)


def load_project(project_id: str) -> Optional[Dict[str, Any]]:
    """Load project from disk."""
    path = _project_path(project_id)
    if not os.path.exists(path):
        return None
    with _lock:
        with open(path, 'r') as f:
            return json.load(f)


def load_all_projects() -> Dict[str, Dict[str, Any]]:
    """Load all projects from disk."""
    projects = {}
    with _lock:
        for fname in os.listdir(DATA_DIR):
            if fname.endswith('.json'):
                pid = fname[:-5]
                with open(os.path.join(DATA_DIR, fname), 'r') as f:
                    projects[pid] = json.load(f)
    return projects


def delete_project(project_id: str) -> None:
    """Delete project from disk."""
    path = _project_path(project_id)
    if os.path.exists(path):
        with _lock:
            os.remove(path)


def project_exists(project_id: str) -> bool:
    """Check if project exists on disk."""
    return os.path.exists(_project_path(project_id))
