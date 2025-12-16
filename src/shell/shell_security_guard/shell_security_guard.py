import fnmatch
import shlex
from typing import Optional, Tuple
from llm import StructuredLLM
from questionary import select, text
from shell.interactive_shell.shell_types import SecurityCheckLLMResponse
from shell.security_context import SecurityContext
from shell.shell_security_guard.constants import HandleForbiddenPatternChoices, FORBIDDEN_PATHS
from shell.shell_security_guard.security_guard_types import SecurityVerdict, SecurityVerdictAction
from shell.shell_security_guard.prompts import ShellSecurityGuardPrompts
from pathvalidate import is_valid_filepath

class ShellSecurityGuard:
    """Guards shell execution by validating commands against security protocols.

    This class intercepts shell commands, checks them against a list of forbidden
    patterns (e.g., sensitive file paths), and uses an LLM to determine the 
    intent of the command. It handles user intervention if a command is flagged
    as potentially unsafe.

    Attributes:
        security_context (SecurityContext): The context managing whitelists and security state.
        llm (StructuredLLM): The language model interface used for intent verification.
    """

    def __init__(self, security_context: SecurityContext, llm: StructuredLLM):
        """Initializes the ShellSecurityGuard.

        Args:
            security_context (SecurityContext): The context object for security settings.
            llm (StructuredLLM): The structured LLM instance for processing prompts.
        """
        self.security_context = security_context
        self.llm = llm

    def review_command(self, command: str) -> SecurityVerdict:
        """Validates a command and returns a verdict on how to proceed.

        This is the main entry point for the security guard. It performs the following checks:
        1. Checks if the command matches any forbidden string patterns.
        2. If matched, asks the LLM to verify the intent against the whitelist.
        3. If the LLM deems it unsafe, initiates user intervention.

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
                reason="No forbidden pattern found in the command"
            )
        forbidden_file, pattern = result
        
        command_intent = self._check_command_intent(
            command=command,
            forbidden_file=forbidden_file,
            pattern=pattern
        )
        if command_intent.is_safe:
            return SecurityVerdict(
                action=SecurityVerdictAction.PROCEED,
                reason=f"Pattern '{pattern}' discoverd in the command, but LLM allowed it. Reason: {command_intent.reason}"
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
                HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST.value.format(file=forbidden_file),
                HandleForbiddenPatternChoices.EXECUTE_MANUALLY.value,
                HandleForbiddenPatternChoices.SKIP.value,
            ],
            default=HandleForbiddenPatternChoices.ALLOW_ONCE.value,
        ).unsafe_ask()

        if action == HandleForbiddenPatternChoices.SKIP:
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

        if action == HandleForbiddenPatternChoices.ALLOW_AND_WHITELIST:
            self.security_context.add_to_whitelist(forbidden_file)

        return SecurityVerdict(action=SecurityVerdictAction.PROCEED, reason="User allowed to proceed with the command execution.")

    def _check_command_intent(
            self,
            command: str,
            forbidden_file: str,
            pattern: str
        ) -> SecurityCheckLLMResponse:
        """Consults the LLM to determine if the flagged command is actually safe.

        Constructs a prompt containing the current whitelist and the specific pattern,
        then invokes the StructuredLLM to get a structured boolean assessment of safety.

        Args:
            command (str): The shell command being analyzed.
            forbidden_file (str): The  considered unsafe.

        Returns:
            SecurityCheckLLMResponse: The structured response from the LLM indicating 
            safety status and reasoning.
        """
        whitelist_str = self.security_context.get_whitelist_str()
        
        system_prompt = ShellSecurityGuardPrompts.VERIFY_COMMAND_INTENT.format(
            pattern=pattern,
            forbidden_file=forbidden_file,
            whitelist_str=whitelist_str
        )
        
        return self.llm.invoke(
            schema=SecurityCheckLLMResponse,
            system_message=system_prompt,
            input_text=command,
        )

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
                    if pattern and is_valid_filepath(candidate):
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