import fnmatch
import shlex
import os
from typing import Optional, Tuple
from llm import StructuredLLM
from questionary import select, text, Choice
from shell.security_context import SecurityContext
from shell.shell_security_guard.constants import (
    HandleForbiddenPatternChoices,
    FORBIDDEN_PATHS,
)
from shell.shell_security_guard.security_guard_types import (
    SecurityVerdict,
    SecurityVerdictAction,
)
from config import Config


class ShellSecurityGuard:
    """Guards shell execution by validating commands against security protocols.

    This class intercepts shell commands, checks them against a list of forbidden
    patterns (e.g., sensitive file paths), and manages user intervention if a
    command is flagged as potentially unsafe. It utilizes a whitelist system to
    allow known safe paths.

    Attributes:
        security_context (SecurityContext): The context managing whitelists and
            security state.
        llm (StructuredLLM): The structured LLM instance (retained for potential
            future intent verification).
        _project_root (str): The absolute path to the project root directory,
            used for resolving relative paths.
    """

    def __init__(self, security_context: SecurityContext, llm: StructuredLLM):
        """Initializes the ShellSecurityGuard.

        Args:
            security_context (SecurityContext): The context object for security settings.
            llm (StructuredLLM): The structured LLM instance.
        """
        self.security_context = security_context
        self.llm = llm
        self._project_root = Config.get().project_root

    def review_command(self, command: str) -> SecurityVerdict:
        """Validates a command and returns a verdict on how to proceed.

        This is the main entry point for the security guard. It performs the
        following checks:
        1. Parses the command to identify sensitive file paths based on forbidden patterns.
        2. If a match is found, checks if the path is explicitly whitelisted.
        3. If not whitelisted, triggers the user intervention workflow.

        Args:
            command (str): The shell command string to be executed.

        Returns:
            SecurityVerdict: A data class containing the action (PROCEED, SKIPPED,
            COMPLETED_MANUALLY) and the reasoning or output.
        """
        result = self._extract_sensitive_path(command)
        if result is None:
            return SecurityVerdict(
                action=SecurityVerdictAction.PROCEED,
                reason="No forbidden pattern found in the command",
            )
        forbidden_file, pattern = result

        if self._is_path_whitelisted(forbidden_file):
            return SecurityVerdict(
                action=SecurityVerdictAction.PROCEED,
                reason=f"Pattern '{pattern}' discovered in the command, but it's whitelisted.",
            )

        return self._handle_intervention(
            command=command, forbidden_file=forbidden_file, pattern=pattern
        )

    def _handle_intervention(
        self, command: str, forbidden_file: str, pattern: str
    ) -> SecurityVerdict:
        """Handles user interaction when a potentially unsafe command is detected.

        Prompts the user to choose an action via a CLI selection menu. The user can
        allow the command once, allow and whitelist the path, execute manually in a
        separate terminal, or skip the command entirely.

        Args:
            command (str): The command that triggered the alert.
            forbidden_file (str): The extracted file path that caused the alert.
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
                    title=f"{HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value} ({os.path.relpath(self._resolve_path(forbidden_file), self._project_root)})",
                    value=HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value,
                ),
                HandleForbiddenPatternChoices.EXECUTE_MANUALLY.value,
                HandleForbiddenPatternChoices.SKIP.value,
            ],
            default=HandleForbiddenPatternChoices.ALLOW_ONCE.value,
        ).unsafe_ask()

        if action == HandleForbiddenPatternChoices.SKIP.value:
            return SecurityVerdict(
                action=SecurityVerdictAction.SKIPPED,
                reason=f"Blocked by user: {pattern}",
            )

        if action == HandleForbiddenPatternChoices.EXECUTE_MANUALLY.value:
            print(f"\n{'-' * 40}")
            print("MANUAL EXECUTION INSTRUCTIONS")
            print("1. Open a new terminal window.")
            print(f"2. Run this command:\n\n   {command}\n")
            print("3. Once done, copy the output (if any) and paste it below.")
            print(f"{'-' * 40}")

            user_output: str = text(
                "Paste command output here (press Enter if no output):", multiline=True
            ).unsafe_ask()

            return SecurityVerdict(
                action=SecurityVerdictAction.COMPLETED_MANUALLY,
                reason="User executed the command manually",
                output=user_output + "\n",
            )

        if action == HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value:
            self.security_context.add_to_whitelist(self._resolve_path(forbidden_file))

        return SecurityVerdict(
            action=SecurityVerdictAction.PROCEED,
            reason="User allowed to proceed with the command execution.",
        )

    def _is_path_whitelisted(self, path: str) -> bool:
        """Checks if the given path is present in the whitelist.

        This method resolves the provided path to an absolute path (relative to the
        project root) before querying the security context.

        Args:
            path (str): The file path to check.

        Returns:
            bool: True if the resolved absolute path is whitelisted, False otherwise.
        """
        abs_path = self._resolve_path(path)
        return self.security_context.is_whitelisted(path=abs_path)

    def _resolve_path(self, path: str) -> str:
        """Resolves a given path to an absolute path against the project root.

        If the input path is already absolute, the project root is ignored.
        If the input path is relative, it is joined with the project root.

        Args:
            path (str): The file path to resolve.

        Returns:
            str: The normalized absolute path.
        """
        return os.path.abspath(os.path.join(self._project_root, path))

    def _extract_sensitive_path(self, command: str) -> Optional[Tuple[str, str]]:
        """Extracts the specific file path or token that triggered the security alert.

        Uses `shlex` to parse the command arguments safely. It employs a hybrid
        validation strategy:
        1. Checks if a token matches a forbidden pattern (ignoring pure strings
           like environment keys).
        2. If matched, it validates if the token represents a file by:
           a) Checking if the file explicitly exists on disk.
           b) Checking if it structurally resembles a path (contains separators,
              starts with a dot, or has an extension) to catch file creation.

        Args:
            command (str): The shell command to parse.

        Returns:
            Optional[Tuple[str, str]]: A tuple containing the specific token
            (file path) and the matching pattern, or None if no match is found.
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

                    if (
                        os.sep in candidate
                        or "/" in candidate
                        or "\\" in candidate
                        or candidate.startswith(".")
                        or "." in candidate[1:]
                    ):
                        return candidate, pattern
        except ValueError:
            pass
        return None

    def _is_forbidden_pattern(self, sequence: str) -> Optional[str]:
        """Checks if the sequence contains any globally forbidden patterns.

        This performs a case-insensitive wildcard match against the list of
        forbidden paths defined in constants.

        Args:
            sequence (str): The text sequence (filename/path) to check.

        Returns:
            Optional[str]: The matching pattern (lowercased and wrapped in wildcards)
            if found, otherwise None.
        """
        sequence_lower = sequence.lower()
        for pattern in FORBIDDEN_PATHS:
            if fnmatch.fnmatch(sequence_lower, f"*{pattern.lower()}*"):
                return f"*{pattern.lower()}*"
        return None
