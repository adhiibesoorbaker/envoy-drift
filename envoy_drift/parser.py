"""Parser module for reading and normalizing environment files."""

import os
from typing import Dict, Optional


class EnvFileParser:
    """Parses .env files into key-value dictionaries."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    def parse(self) -> Dict[str, str]:
        """Read and parse an env file, returning a dict of key-value pairs."""
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Env file not found: {self.filepath}")

        env_vars: Dict[str, str] = {}

        with open(self.filepath, "r") as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                if "=" not in line:
                    raise ValueError(
                        f"Invalid format at line {line_number} in {self.filepath}: '{line}'"
                    )

                key, _, value = line.partition("=")
                key = key.strip()
                value = self._strip_quotes(value.strip())

                if not key:
                    raise ValueError(
                        f"Empty key at line {line_number} in {self.filepath}"
                    )

                env_vars[key] = value

        return env_vars

    @staticmethod
    def _strip_quotes(value: str) -> str:
        """Remove surrounding single or double quotes from a value."""
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            return value[1:-1]
        return value


def load_env_file(filepath: str) -> Dict[str, str]:
    """Convenience function to parse an env file."""
    return EnvFileParser(filepath).parse()
