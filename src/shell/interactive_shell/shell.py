import pexpect
import fnmatch
from uuid import UUID
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field
from questionary import select, text

from shell.types import (
    InteractionReviewLLMResponse,
    InteractionReview,
    StreamToShellOutput,
    LongRunningShellInteractionReviewLLMResponse
)
from shell.interactive_shell.prompts import BaseInteractiveShellPrompts
from shell.base_shell import BaseShell
from rich.console import Console
from shell.security_context import SecurityContext

class SecurityCheckLLMResponse(BaseModel):
    is_safe: bool = Field(
        ..., 
        description="True if command is a safe write OR accesses only whitelisted files. False otherwise."
    )
    reason: str = Field(..., description="Reasoning for the decision.")

class FileExtractionResponse(BaseModel):
    file_path: Optional[str] = Field(
        None, 
        description="The specific sensitive file path extracted from the command, or None if unclear."
    )


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

class InteractiveShell(BaseShell):
    """
    A persistent interactive shell interface with streaming output,
    LLM-based detection of user interaction, and global security context.
    """

    def __init__(
        self,
        security_context: SecurityContext,
        id: Optional[UUID] = None,
        log_file: Optional[str] = None,
        init_timeout: int = 10,
        read_buffer_size: int = 65536,
        read_timeout: int = 2,
    ) -> None:
        """
        Initialize the interactive shell.
        """
        super().__init__(id=id, init_timeout=init_timeout)
        self._log_file = log_file
        self._read_buffer_size = read_buffer_size
        self._read_timeout = read_timeout
        self.console = Console(
            log_path=False,
            log_time_format="[%Y-%m-%d %H:%M:%S]"
        )
        self._console_log_prefix = f"[bold blue][INFO] [{self.name}]:[/bold blue]"
        self._security_context = security_context

    def send(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Send a sequence of input to the shell.

        Args:
            sequence (str): The input sequence to send.
            hide_input (bool, optional): If True, masks the input in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the shell's response.
        """
        self._buffer = ""
        self.child.send(sequence)
        return self.stream_command(sequence, hide_input=hide_input)

    def send_line(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Send a sequence of input to the shell, followed by a newline (Enter).

        Args:
            sequence (str): The input sequence to send.
            hide_input (bool, optional): If True, masks the input in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the shell's response.
        """
        self._buffer = ""
        self.child.sendline(sequence)
        return self.stream_command(sequence, hide_input=hide_input)
    
    def send_control(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Send a control sequence (e.g., Ctrl+C, Ctrl+D) to the shell.

        Args:
            sequence (str): The control sequence to send.
            hide_input (bool, optional): If True, masks the sequence in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the shell's response.
        """
        self._buffer = ""
        self.child.sendcontrol(sequence)
        return self.stream_command(sequence, hide_input=hide_input)

    def run_command(self, command: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Execute a command in the shell and return its output after completion.

        Args:
            command (str): The shell command to execute.
            hide_input (bool, optional): If True, masks the command in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the command output.
        """
        is_forbidden, pattern = self._is_forbidden_command(command=command)
        
        if is_forbidden and pattern:
            is_safe = self._check_command_intent(command, pattern)
            
            if not is_safe:
                return self._handle_forbidden_command(
                    command=command,
                    hide_input=hide_input,
                    forbidden_pattern=pattern
                )
            else:
                self.logger.info(f"Allowed sensitive command (Safe Write or Whitelisted): {pattern}")

        return self.send_line(sequence=command, hide_input=hide_input)
    
    def _check_command_intent(self, command: str, pattern: str) -> bool:
        """
        Uses LLM to determine if command is safe (Blind Write) or Whitelisted.
        """
        whitelist_str = self._security_context.get_whitelist_str()
        
        system_prompt = (
            "You are a shell security auditor. Your goal is to protect sensitive files.\n"
            "Analyze the shell command provided by the user.\n\n"
            f"1. The command triggered the forbidden pattern: '{pattern}'\n"
            f"2. The user has explicitly WHITELISTED these paths: [{whitelist_str}]\n\n"
            "Decision Rules:\n"
            "- ALLOW (True) if the command ONLY reads/accesses files found in the WHITELIST.\n"
            "- ALLOW (True) if the command is a pure 'Blind Write' (overwriting without reading), even if not whitelisted.\n"
            "- DENY (False) if the command reads, prints, or exposes a non-whitelisted sensitive file.\n"
        )

        try:
            response = self._llm.invoke(
                schema=SecurityCheckLLMResponse,
                system_message=system_prompt,
                input_text=command,
            )
            return response.is_safe
        except Exception as e:
            self.logger.error(f"Security intent check failed: {e}")
            return False

    def _handle_forbidden_command(self, command: str, hide_input: bool, forbidden_pattern: str) -> StreamToShellOutput:
        """
        Handles user interaction when a command is blocked.
        Allows 'Allow', 'Skip' (Block), or 'Manual Execution'.
        """
        command_to_display = self._mask_sequence(sequence=command, hide_input=hide_input)
        
        print(f"\nSecurity Alert: Command matches forbidden pattern '{forbidden_pattern}'")
        print(f"   Command: {command_to_display}")

        action = select(
            message="Choose an action:",
            choices=[
                "Execute manually & paste output",
                "Allow once", 
                "Allow & Whitelist this file (Session)", 
                "Block / Skip command", 
            ],
            default="Block / Skip command",
        ).unsafe_ask()

        if action == "Execute manually & paste output":
            print(f"\n{'-'*40}")
            print("📝 MANUAL EXECUTION INSTRUCTIONS")
            print(f"{'-'*40}")
            print("1. Open a new terminal window.")
            print(f"2. Run this command:\n\n   {command_to_display}\n")
            print("3. Once done, copy the output (if any) and paste it below.")
            print(f"{'-'*40}")
            
            user_output = text(
                "Paste command output here (press Enter if no output):",
                multiline=True
            ).unsafe_ask()

            self.logger.info(f"Command executed manually by user: {command_to_display}")
            
            return StreamToShellOutput(
                needs_action=False,
                reason="User executed command manually.",
                output=user_output + "\n"
            )

        if action == "Block / Skip command":
            return StreamToShellOutput(
                needs_action=False,
                reason=f"User blocked command matching: {forbidden_pattern}",
                output="Access denied by user. Command was skipped."
            )

        if action == "Allow & Whitelist this file (Session)":
            extracted_file = self._extract_sensitive_path(command)
            if extracted_file:
                self._security_context.add_to_whitelist(extracted_file)
                self.logger.info(f"Globally whitelisted file: {extracted_file}")
            else:
                self.logger.warning("Could not extract specific file to whitelist; allowing once.")

        return self.send_line(sequence=command, hide_input=hide_input)

    def _extract_sensitive_path(self, command: str) -> Optional[str]:
        """Helper to extract the sensitive file path for whitelisting."""
        try:
            response = self._llm.invoke(
                schema=FileExtractionResponse,
                system_message="Extract the specific file path that is likely sensitive (e.g., .env, id_rsa) from this command. Return just the path string.",
                input_text=command
            )
            return response.file_path
        except Exception:
            return None

    def _review_for_interaction(self, buffer: str) -> InteractionReview:
        """
        Analyze shell output with the LLM to determine if user interaction is required.

        Args:
            buffer (str): The accumulated shell output.

        Returns:
            InteractionReview: LLM decision indicating whether interaction is needed, along with reasoning and output.
        """
        interaction_review_llm_response = self._llm.invoke(
            schema=InteractionReviewLLMResponse,
            system_message=BaseInteractiveShellPrompts.REVIEW_FOR_INTERACTION.value,
            input_text=buffer,
        )

        return InteractionReview(
            **interaction_review_llm_response.model_dump(),
            output=buffer,
        )

    def stream_command(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Run a command in the shell, stream output, and detect interaction.
        """
        command_to_display = self._mask_sequence(sequence=sequence, hide_input=hide_input)
            
        with self.console.status(f"[bold green]Running command: {command_to_display}...\n[/bold green]") as status:
            self.logger.info(f"Running command: {command_to_display}")
            llm_called = False

            while True:
                try:
                    chunk = self.child.read_nonblocking(
                        self._read_buffer_size, timeout=self._read_timeout
                    )
                    clean_chunk = self._clean_chunk(chunk)

                    self._buffer += clean_chunk
                    self._step_buffer += clean_chunk

                    if not self._is_progress_noise(clean_chunk):
                        self._log_to_file(clean_chunk)

                    llm_called = False

                    if clean_chunk.rstrip().endswith("$"):
                        self.logger.info("Detected shell prompt; command finished.")
                        break

                except pexpect.TIMEOUT:
                    if not llm_called:
                        self.console.log(f"{self._console_log_prefix} Output stable for {self._read_timeout}s; invoking LLM...")
                        llm_called = True
                        self._buffer = self._mask_sequence_in_text(
                            self._buffer, sequence=sequence, hide_input=hide_input
                        )
                        self._buffer = self._redact_text(self._buffer)

                        status.update("[bold yellow]Analyzing shell state...\n[/bold yellow]", spinner="dots")
                        result = self._evaluate_buffer_state()

                        if result:
                            return result
                        
                        self.console.log(f"{self._console_log_prefix} Analysis complete: Command is still processing. Resuming...")
                        status.update(f"[bold green]Running command: {command_to_display}...\n[/bold green]", spinner="dots")
                except pexpect.EOF:
                    self.logger.error("EOF reached; shell closed.")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected exception: {e}")
                    break

        self._buffer = self._mask_sequence_in_text(self._buffer, sequence=sequence, hide_input=hide_input)
        self._buffer = self._redact_text(self._buffer)
        
        self._log_to_file("\n")
        self.logger.info("Command finished")
        return StreamToShellOutput(needs_action=False, output=self._buffer)
    
    def _evaluate_buffer_state(self) -> Optional[StreamToShellOutput]:
        """Evaluates the buffer to detect interaction prompts or process states.

        Checks if the shell is waiting for user input or if a long-running process is stable or has failed.

        Returns:
            Optional[StreamToShellOutput]: Output object if the shell awaits interaction,
            or if a background process is stable/failed, containing output buffer and justification. Otherwise, None.
        """
        if not self._buffer:
            return None

        try:
            interaction_review = self._review_for_interaction(self._buffer)

            if interaction_review.needs_action:
                self.logger.info("Shell awaits interaction")
                self._log_to_file("\n")
                return StreamToShellOutput(
                    needs_action=True,
                    reason=interaction_review.reason,
                    output=self._buffer
                )

            wait_reason = interaction_review.reason
            if self._id != "MAIN":
                long_running_review = self._review_for_long_running(self._buffer)

                if long_running_review.state.value == "running":
                    return StreamToShellOutput(
                        needs_action=False,
                        reason=(
                            "Long-running process is stable and can be left unsupervised. "
                            + long_running_review.reason
                        ),
                        output=self._buffer,
                    )

                if long_running_review.state.value == "error":
                    return StreamToShellOutput(
                        needs_action=True,
                        reason=long_running_review.reason,
                        output=self._buffer,
                    )
                wait_reason = long_running_review.reason
            self.console.log(f"{self._console_log_prefix} Command is still processing. Reason: {wait_reason}")
        except Exception as e:
            self.logger.error(f"LLM invocation failed: {e}")

        return None

    def _log_to_file(self, sequence: str) -> None:
        """
        Append a sequence of text to the shell's log file if logging is enabled.

        This method safely opens the log file in append mode and writes
        the provided sequence. If no log file is set, it does nothing.

        Args:
            sequence (str): The text or command output to log.
        """
        if self._log_file:
            with open(self._log_file, "a") as f:
                f.write(sequence)

    def _review_for_long_running(self, buffer: str) -> LongRunningShellInteractionReviewLLMResponse:
        """
        LLM review for long-running/background shells.
        Determines process state: initializing, running, or error.

        Args:
            buffer (str): Shell output.

        Returns:
            LongRunningShellInteractionReviewLLMResponse: needs_action, reasoning, and process state.
        """
        long_running_review = self._llm.invoke(
            schema=LongRunningShellInteractionReviewLLMResponse,
            system_message=BaseInteractiveShellPrompts.LONG_RUNNING_SHELL_REVIEW,
            input_text=buffer,
        )

        return long_running_review

    def _is_forbidden_command(self, command: str) -> Tuple[bool, Optional[str]]:
        command_lower = command.lower()
        for pattern in FORBIDDEN_PATHS:
            if fnmatch.fnmatch(command_lower, f"*{pattern.lower()}*"):
                return True, f"*{pattern.lower()}*"
        return False, None