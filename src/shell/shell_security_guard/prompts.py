from enum import Enum

class ShellSecurityGuardPrompts(str, Enum):
    VERIFY_COMMAND_INTENT = (
        "You are a shell security auditor. Your goal is to protect sensitive files.\n"
        "Analyze the shell command provided by the user.\n\n"
        "1. The command triggered the forbidden pattern: '{pattern}'\n"
        "2. The user has explicitly WHITELISTED these paths: [{whitelist_str}]\n\n"
        "Decision Rules:\n"
        "- ALLOW (True) if the command ONLY reads/accesses files found in the WHITELIST.\n"
        "- ALLOW (True) if the command is a pure 'Blind Write' (overwriting without reading), even if not whitelisted.\n"
        "- DENY (False) if the command reads, prints, or exposes a non-whitelisted sensitive file.\n"
    )