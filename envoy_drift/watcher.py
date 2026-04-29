"""File watcher module for detecting env file changes and triggering drift checks."""

import os
import time
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional


@dataclass
class WatchedFile:
    path: str
    last_hash: Optional[str] = None
    last_modified: float = 0.0

    def current_hash(self) -> Optional[str]:
        """Compute MD5 hash of file contents, or None if file is missing."""
        try:
            with open(self.path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except FileNotFoundError:
            return None

    def has_changed(self) -> bool:
        """Return True if the file has changed since last check."""
        current = self.current_hash()
        return current != self.last_hash

    def update(self) -> None:
        """Update stored hash to reflect current file state."""
        self.last_hash = self.current_hash()
        self.last_modified = time.time()


class EnvFileWatcher:
    """Watches one or more env files and triggers a callback on change."""

    def __init__(
        self,
        source_path: str,
        target_path: str,
        on_change: Callable[[str, str], None],
        poll_interval: float = 2.0,
    ) -> None:
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._files: Dict[str, WatchedFile] = {
            "source": WatchedFile(path=source_path),
            "target": WatchedFile(path=target_path),
        }
        for watched in self._files.values():
            watched.update()

    def check_once(self) -> bool:
        """Perform a single check. Returns True if any file changed."""
        changed = False
        for watched in self._files.values():
            if watched.has_changed():
                watched.update()
                changed = True
        if changed:
            self.on_change(
                self._files["source"].path,
                self._files["target"].path,
            )
        return changed

    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Poll files in a loop, calling on_change when drift is detected."""
        iteration = 0
        while max_iterations is None or iteration < max_iterations:
            self.check_once()
            time.sleep(self.poll_interval)
            iteration += 1
