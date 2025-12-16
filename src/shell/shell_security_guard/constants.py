from enum import Enum
from typing import List

FORBIDDEN_PATHS: List[str] = [
    "/home/*/.ssh/*",
    "/home/*/.gnupg/*",
    "/home/*/.aws/*",
    "/home/*/.config/*",
    "*.env",
    ".*env*",
    "*secret*",
    "*password*",
    "*token*",
    "*credential*",
]

class HandleForbiddenPatternChoices(str, Enum):
    ALLOW_ONCE = "Allow once"
    ALLOW_AND_WHITELIST = "Allow and add the file to session's whitelist ({file})"
    EXECUTE_MANUALLY = "Execute manually in separate terminal"
    SKIP = "Skip command"
