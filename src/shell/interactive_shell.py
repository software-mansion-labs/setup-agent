import pexpect
import getpass
from functools import reduce

from model import get_llm
from langchain_core.messages import HumanMessage

from utils.remove_ansi_escape_characters import remove_ansi_escape_characters
from utils.apply_backspaces import apply_backspaces
from utils.remove_carriage_characters import remove_carriage_character
from utils.is_progress_noise import is_progress_noise
from utils.logger import with_logger, Logger
from src.shell.types import InteractionReviewLLMResponse, InteractionReview, StreamToShellOutput

@with_logger(name="Shell")
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

    def __init__(self) -> None:
        """
        Initialize the interactive shell and set up environment.
        Starts a persistent zsh shell and sets a simple prompt.
        """
        self.logger: Logger
        self._llm = get_llm()
        self._buffer = ""

        self.logger.info("Starting persistent zsh shell...")
        self.child = pexpect.spawn("/bin/zsh", ["-l"], encoding="utf-8", echo=False)
        self.child.sendline('PS1="$ "')
        self.child.expect(r"\$ ", timeout=10)
        self.logger.info("Shell ready.")

    def _send(self, text: str) -> None:
        """
        Send a raw command or input string to the shell process.

        Args:
            text (str): The command or input to send to the shell.
        """
        self.logger.debug(f"Sending to shell: {text}")
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

    def run_command_with_confirmation(self, command: str) -> StreamToShellOutput:
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

        self.logger.debug(f"Running command: {command}")
        llm_called = False

        while True:
            try:
                chunk = self.child.read_nonblocking(65536, timeout=2.0)
                clean_chunk = self._clean_chunk(chunk)

                self._buffer += clean_chunk

                if not is_progress_noise(clean_chunk):
                    with open("logs.txt", "a") as f:
                        f.write(clean_chunk)

                llm_called = False

                if clean_chunk.strip().endswith("$"):
                    self.logger.debug("Detected shell prompt; command finished.")
                    break

            except pexpect.TIMEOUT:
                if not llm_called:
                    self.logger.debug("Output stable for 2s; invoking LLM...")                    
                    llm_called = True

                    try:
                        interaction_review = self._review_for_interaction(
                            self._buffer.strip()
                        )

                        if interaction_review.needs_action:
                            self.logger.debug("Shell awaits interaction")
                            with open("logs.txt", "a") as f:
                                f.write("\n")
                            
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

        with open("logs.txt", "a") as f:
            f.write("\n")

        self.logger.info("Command finished")
        return StreamToShellOutput(needs_action=False, output=self._buffer.strip())


interactive_shell = InteractiveShell()
