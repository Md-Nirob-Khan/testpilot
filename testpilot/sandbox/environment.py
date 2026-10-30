"""Build a minimal environment for executing untrusted code in subprocesses."""

import os


_INHERITED_VARIABLES = {
    "COMSPEC",
    "HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "PATHEXT",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TERM",
    "TMP",
    "TMPDIR",
    "WINDIR",
}


def isolated_subprocess_environment() -> dict[str, str]:
    """Keep process basics while excluding inherited credentials and app config."""
    return {
        key: value
        for key, value in os.environ.items()
        if key.upper() in _INHERITED_VARIABLES
    }
