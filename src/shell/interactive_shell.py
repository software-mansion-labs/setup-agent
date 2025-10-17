import pexpect
import getpass
from functools import lru_cache, reduce
from model import get_llm
from langchain_core.messages import HumanMessage
from shell.utils.remove_ansi_escape_characters import remove_ansi_escape_characters
from shell.utils.apply_backspaces import apply_backspaces
from shell.utils.remove_carriage_characters import remove_carriage_character
from shell.utils.is_progress_noise import is_progress_noise
from shell.types import (
    InteractionReviewLLMResponse,
    InteractionReview,
    StreamToShellOutput,
)
from utils.logger import LoggerFactory
from typing import Optional


class InteractiveShell:
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
        log_file: Optional[str] = None,
        init_timeout: int = 65536,
        read_buffer_size: int = 2,
        read_timeout: int = 10,
    ) -> None:
        """
        Initialize the interactive shell and set up environment.
        Starts a persistent zsh shell and sets a simple prompt.
        """
        self.logger = LoggerFactory.get_logger(name="Shell")
        self._llm = get_llm()
        self._buffer = ""
        self._log_file = log_file
        self._read_buffer_size = read_buffer_size
        self._read_timeout = read_timeout

        self.logger.info("Starting persistent zsh shell...")
        self.child = pexpect.spawn("/bin/zsh", ["-l"], encoding="utf-8", echo=False)
        self.child.sendline('PS1="$ "')
        self.child.expect(r"\$ ", timeout=init_timeout)
        self.logger.info("Shell ready.")

    def _send(self, text: str) -> None:
        """
        Send a raw command or input string to the shell process.

        Args:
            text (str): The command or input to send to the shell.
        """
        self.logger.info(f"Sending to shell: {text}")
        self.child.sendline(text)

    def authenticate(self) -> StreamToShellOutput:
        """
        Prompt the user for a sudo password and send it to the shell securely.

        Returns:
            StreamToShellOutput: The shell output or an LLM decision if interaction is required.
        """
        self.logger.info("Prompting for sudo password")
        passwd = getpass.getpass("\n[Shell] Enter your sudo password: ")
        return self.stream_command(command=passwd.strip())

    def run_command(self, command: str) -> StreamToShellOutput:
        """
        Run a shell command and stream its output with optional LLM analysis.

        Args:
            command (str): The shell command to run.

        Returns:
            StreamToShellOutput: The final shell output or an LLM decision if interaction is required.
        """
        return self.stream_command(command=command)

    def _clean_chunk(self, chunk: str) -> str:
        """
        Clean a chunk of shell output using a series of transformations.

        Steps:
            - Remove ANSI escape codes.
            - Remove carriage returns.
            - Apply backspace character handling.
            - Strip leading/trailing whitespace.

        Args:
            chunk (str): Raw shell output.

        Returns:
            str: Cleaned shell output.
        """
        cleaning_pipeline = [
            remove_ansi_escape_characters,
            remove_carriage_character,
            apply_backspaces,
        ]
        return reduce(lambda acc, func: func(acc), cleaning_pipeline, chunk).strip()

    def _review_for_interaction(self, buffer: str) -> InteractionReview:
        """
        Analyze shell output with the LLM to determine if user interaction is required.

        Args:
            buffer (str): The accumulated shell output.

        Returns:
            InteractionReview: LLM decision indicating whether interaction is needed, along with reasoning and output.
        """
        prompt = f"""
            You are a command-line assistant. Analyze this shell output and determine
            if the system is **actually waiting for user input right now**.

            Shell output:
            \"\"\"{buffer}\"\"\"
        """

        structured_llm = self._llm.with_structured_output(InteractionReviewLLMResponse)
        interaction_review_llm_response: InteractionReviewLLMResponse = (
            structured_llm.invoke([HumanMessage(content=prompt)])
        )
        return InteractionReview(
            **interaction_review_llm_response.model_dump(), output=buffer
        )

    def stream_command(self, command: str) -> StreamToShellOutput:
        """
        Run a command in the shell, stream output, and use the LLM to detect
        if user interaction is required.

        Args:
            command (str): Command to execute in the shell.

        Returns:
            StreamToShellOutput: Either the final shell output (needs_action=False) or
                                 an LLM decision indicating that interaction is required.
        """
        self._buffer = ""
        self._send(command)

        self.logger.info(f"Running command: {command}")
        llm_called = False

        while True:
            try:
                chunk = self.child.read_nonblocking(
                    self._read_buffer_size, timeout=self._read_timeout
                )
                clean_chunk = self._clean_chunk(chunk)

                self._buffer += clean_chunk

                if not is_progress_noise(clean_chunk):
                    self._log_to_file(clean_chunk)

                llm_called = False

                if clean_chunk.strip().endswith("$"):
                    self.logger.info("Detected shell prompt; command finished.")
                    break

            except pexpect.TIMEOUT:
                if not llm_called:
                    self.logger.info("Output stable for 2s; invoking LLM...")
                    llm_called = True

                    try:
                        interaction_review = self._review_for_interaction(
                            self._buffer.strip()
                        )

                        if interaction_review.needs_action:
                            self.logger.info("Shell awaits interaction")
                            self._log_to_file("\n")

                            return StreamToShellOutput(
                                **interaction_review.model_dump()
                            )

                    except Exception as e:
                        self.logger.error(f"LLM invocation failed: {e}")

            except pexpect.EOF:
                self.logger.error("EOF reached; shell closed.")
                break
            except Exception as e:
                self.logger.error(f"Unexpected exception: {e}")
                break

        self._log_to_file("\n")

        self.logger.info("Command finished")
        return StreamToShellOutput(needs_action=False, output=self._buffer.strip())

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


@lru_cache(maxsize=1)
def get_interactive_shell() -> InteractiveShell:
    """
    Return a shared instance of `InteractiveShell`, initialized lazily.

    This function ensures that only one instance of `InteractiveShell` is
    created and reused throughout the application, improving efficiency
    and maintaining consistent state across shell interactions.

    Returns:
        InteractiveShell: A singleton instance of the interactive shell.
    """
    return InteractiveShell()
