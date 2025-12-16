import fnmatch
import shlex
import os
from typing import Optional, Tuple
from llm import StructuredLLM
from questionary import select, text, Choice
from shell.security_context import SecurityContext
from shell.shell_security_guard.constants import HandleForbiddenPatternChoices, FORBIDDEN_PATHS
from shell.shell_security_guard.security_guard_types import SecurityVerdict, SecurityVerdictAction
from config import Config

class ShellSecurityGuard:
    """Guards shell execution by validating commands against security protocols."""

    def __init__(self, security_context: SecurityContext, llm: StructuredLLM):
        self.security_context = security_context
        self.llm = llm
        self._project_root = Config.get().project_root

    def review_command(self, command: str) -> SecurityVerdict:
        """Validates a command and returns a verdict on how to proceed."""
        result = self._extract_sensitive_path(command)
        if result is None:
            return SecurityVerdict(
                action=SecurityVerdictAction.PROCEED,
                reason="No forbidden pattern found in the command"
            )
        forbidden_file, pattern = result
        
        if self._is_path_whitelisted(forbidden_file):
            return SecurityVerdict(
                action=SecurityVerdictAction.PROCEED,
                reason=f"Pattern '{pattern}' discovered in the command, but it's whitelisted."
            )

        return self._handle_intervention(
            command=command,
            forbidden_file=forbidden_file,
            pattern=pattern
        )

    def _handle_intervention(
            self,
            command: str,
            forbidden_file: str,
            pattern: str
        ) -> SecurityVerdict:
        """Handles user interaction when a potentially unsafe command is detected.

        Prompts the user to choose an action via a CLI selection menu. The user can
        allow the command once, allow and whitelist the path, execute manually in a 
        separate terminal, or skip the command entirely.

        Args:
            command (str): The command that triggered the alert.
            pattern (str): The specific forbidden pattern detected in the command.

        Returns:
            SecurityVerdict: The result of the user's decision, including manual 
            execution output if applicable.
        """
        print(f"\nSecurity Alert: Command matches forbidden pattern '{pattern}'")
        print(f"Command: {command}")

        action: str = select(
            message="Choose an action:",
            choices=[
                HandleForbiddenPatternChoices.ALLOW_ONCE.value,
                Choice(
                    title=HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value.format(
                        file=os.path.relpath(self._resolve_path(forbidden_file), self._project_root)
                    ),
                    value=HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value
                ),
                HandleForbiddenPatternChoices.EXECUTE_MANUALLY.value,
                HandleForbiddenPatternChoices.SKIP.value,
            ],
            default=HandleForbiddenPatternChoices.ALLOW_ONCE.value,
        ).unsafe_ask()

        if action == HandleForbiddenPatternChoices.SKIP.value:
            return SecurityVerdict(action=SecurityVerdictAction.SKIPPED, reason=f"Blocked by user: {pattern}")

        if action == HandleForbiddenPatternChoices.EXECUTE_MANUALLY.value:
            print(f"\n{'-'*40}")
            print("MANUAL EXECUTION INSTRUCTIONS")
            print("1. Open a new terminal window.")
            print(f"2. Run this command:\n\n   {command}\n")
            print("3. Once done, copy the output (if any) and paste it below.")
            print(f"{'-'*40}")
            
            user_output: str = text("Paste command output here (press Enter if no output):", multiline=True).unsafe_ask()
            
            return SecurityVerdict(
                action=SecurityVerdictAction.COMPLETED_MANUALLY,
                reason="User executed the command manually",
                output=user_output + "\n"
            )

        if action == HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value:
            self.security_context.add_to_whitelist(self._resolve_path(forbidden_file))

        return SecurityVerdict(action=SecurityVerdictAction.PROCEED, reason="User allowed to proceed with the command execution.")
    
    def _is_path_whitelisted(self, path: str) -> bool:
        abs_path = self._resolve_path(path)
        return self.security_context.is_whitelisted(path=abs_path)

    def _resolve_path(self, path: str) -> str:
        return os.path.abspath(os.path.join(self._project_root, path))
            
    def _extract_sensitive_path(self, command: str) -> Optional[Tuple[str, str]]:
        """Extracts the specific file path or token that triggered the security alert.
        
        Uses `shlex` to parse the command arguments safely, ignoring flags/options 
        (tokens starting with '-').

        Args:
            command (str): The shell command to parse.

        Returns:
            Optional[str]: The specific token matching the forbidden pattern, 
            or None if parsing fails or no match is found.
        """
        try:
            tokens = shlex.split(command)
            for token in tokens:
                if "=" in token and token.startswith("-"):
                    _, value = token.split("=", 1)
                    check_candidates = [token, value]
                else:
                    check_candidates = [token]

                for candidate in check_candidates:
                    pattern = self._is_forbidden_pattern(candidate)
                    if not pattern:
                        continue

                    abs_path = self._resolve_path(candidate)
                    if os.path.exists(abs_path):
                        return candidate, pattern

                    if (os.sep in candidate or 
                        "/" in candidate or 
                        "\\" in candidate or 
                        candidate.startswith(".") or
                        "." in candidate[1:]):
                        
                        return candidate, pattern
        except ValueError:
            pass
        return None

    def _is_forbidden_pattern(self, sequence: str) -> Optional[str]:
        """Checks if the sequence contains any globally forbidden patterns.

        Args:
            sequence (str): The sequence to check.

        Returns:
            Optional[str]: The matching pattern (lowercased and wrapped in wildcards) 
            if found, otherwise None.
        """
        sequence_lower = sequence.lower()
        for pattern in FORBIDDEN_PATHS:
            if fnmatch.fnmatch(sequence_lower, f"*{pattern.lower()}*"):
                return f"*{pattern.lower()}*"
        return None