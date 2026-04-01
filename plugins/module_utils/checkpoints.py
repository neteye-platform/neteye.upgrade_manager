from pathlib import Path
from typing import List, Optional


def validate_checkpoint_path(checkpoint_folder: Path, name: str) -> None:
    requested_path = checkpoint_folder / name

    requested_path.resolve().relative_to(checkpoint_folder)


def load_checkpoints(checkpoint_folder: Path, name: Optional[str] = None) -> List[str]:
    checkpoints: List[str] = []

    if not checkpoint_folder.is_dir():
        return checkpoints

    if name:
        if (checkpoint_folder / name).is_file():
            checkpoints.append(name)
        return checkpoints

    checkpoints.extend([checkpoint.name for checkpoint in checkpoint_folder.iterdir()])

    return checkpoints


def delete_checkpoint(checkpoint_folder: Path, name: str) -> None:
    checkpoint_file = checkpoint_folder / name

    if not checkpoint_file.exists():
        return

    checkpoint_file.unlink()
