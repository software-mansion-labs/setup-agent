import pexpect
from shell.types import (
    InteractionReviewLLMResponse,
    InteractionReview,
    StreamToShellOutput,
    LongRunningShellInteractionReviewLLMResponse
)
from typing import Optional
from shell.interactive_shell.prompts import BaseInteractiveShellPrompts
from shell.base_shell import BaseShell
from uuid import UUID


class InteractiveShell(BaseShell):
    """
    A persistent interactive shell interface with streaming output and
    LLM-based detection of user interaction requirements.

    Features:
    - Spawns a persistent zsh shell.
    - Streams command output in real time.
    - Cleans shell output by removing ANSI codes, carriage returns, and handling backspaces.
    - Uses an LLM to determine if the shell is awaiting user input.
    - Logs shell output and LLM decisions.
    """

    def __init__(
        self,
        id: Optional[UUID] = None,
        log_file: Optional[str] = None,
        init_timeout: int = 10,
        read_buffer_size: int = 65536,
        read_timeout: int = 2,
    ) -> None:
        """
        Initialize the interactive shell and set up environment.
        Starts a persistent zsh shell and sets a simple prompt.
        """
        super().__init__(id=id, init_timeout=init_timeout)
        self._log_file = log_file
        self._read_buffer_size = read_buffer_size
        self._read_timeout = read_timeout

    def send(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        self._buffer = ""
        self.child.send(sequence)
        return self.stream_command(sequence, hide_input=hide_input)

    def sendline(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        self._buffer = ""
        self.child.sendline(sequence)
        return self.stream_command(sequence, hide_input=hide_input)
    
    def sendcontrol(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        self._buffer = ""
        self.child.sendcontrol(sequence)
        return self.stream_command(sequence, hide_input=hide_input)

    def run_command(self, command: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Run a shell command and stream its output with optional LLM analysis.

        Args:
            command (str): The shell command to run.

        Returns:
            StreamToShellOutput: The final shell output or an LLM decision if interaction is required.
        """
        return self.sendline(sequence=command, hide_input=hide_input)

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
        Run a command in the shell, stream output, and use the LLM to detect
        if user interaction is required.

        Args:
            command (str): Command to execute in the shell.

        Returns:
            StreamToShellOutput: Either the final shell output (needs_action=False) or
                                 an LLM decision indicating that interaction is required.
        """
        command_to_display = self._mask_sequence(sequence=sequence, hide_input=hide_input)
        
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
                    self.logger.info("Output stable for 2s; invoking LLM...")
                    llm_called = True
                    self._buffer = self._mask_sequence_in_text(self._buffer, sequence=sequence, hide_input=hide_input)


                    if self._buffer:
                        try:
                            interaction_review = self._review_for_interaction(
                                self._buffer
                            )

                            if interaction_review.needs_action:
                                self.logger.info("Shell awaits interaction")
                                self._log_to_file("\n")

                                return StreamToShellOutput(
                                    needs_action=interaction_review.needs_action,
                                    reason=interaction_review.reason,
                                    output=self._buffer
                                )
                            
                            if self._id != "MAIN":
                                long_running_review = self._review_for_long_running(self._buffer)
                                if long_running_review.state.value == "running":
                                    return StreamToShellOutput(
                                        needs_action=False,
                                        reason="Long-running process is running stable and can be left unsupervised. " + long_running_review.reason,
                                        output=self._buffer
                                    )
                                if long_running_review.state.value == "error":
                                    return StreamToShellOutput(
                                        needs_action=True,
                                        reason=long_running_review.reason,
                                        output=self._buffer
                                    )

                        except Exception as e:
                            self.logger.error(f"LLM invocation failed: {e}")
            except pexpect.EOF:
                self.logger.error("EOF reached; shell closed.")
                break
            except Exception as e:
                self.logger.error(f"Unexpected exception: {e}")
                break
            
        self._buffer = self._mask_sequence_in_text(self._buffer, sequence=sequence, hide_input=hide_input)
        
        self._log_to_file("\n")
        self.logger.info("Command finished")
        return StreamToShellOutput(needs_action=False, output=self._buffer)

    def _log_to_file(self, sequence: str):
        """
        Append a sequence of text to the shell's log file if logging is enabled.

        This method safely opens the log file in append mode and writes
        the provided sequence. If no log file is set, it does nothing.

        Args:
            sequence (str): The text or command output to log.
        """
        if self._log_file is not None:
            with open(self._log_file, "a") as f:
                f.write(sequence)

    def _review_for_long_running(self, buffer: str) -> LongRunningShellInteractionReviewLLMResponse:
        """
        LLM review for long-running/background shells.
        Determines process state: initializing, running, or error.

        Args:
            buffer (str): Shell output.

        Returns:
            InteractionReviewWithState: needs_action, reasoning, and process state.
        """
        long_running_review = self._llm.invoke(
            schema=LongRunningShellInteractionReviewLLMResponse,
            system_message=BaseInteractiveShellPrompts.LONG_RUNNING_SHELL_REVIEW,
            input_text=buffer,
        )

        return long_running_review
