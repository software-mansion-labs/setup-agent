from abc import abstractmethod, ABC
import pexpect
import re
from uuid import UUID
from typing import Optional
from shell.types import StreamToShellOutput
from functools import reduce
from utils.logger import LoggerFactory
from llm import StructuredLLM
from utils.secrets_redactor import SecretsRedactor

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
PROGRESS_RE = re.compile(r"\d{1,3}\.\d%#+\s*")
ZSH_ARTIFACT_RE = re.compile(r"%\s+(\r|$)")
SPINNER_CHARS = set("⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇|/-\\")
CARRIAGE_CHARACTER = "\r"


class BaseShell(ABC):
    def __init__(
        self, 
        id: Optional[UUID] = None, 
        init_timeout: int = 10,
        term: str = "vt100",
        columns: int = 2000
    ) -> None:
        self._id = str(id) if id else "MAIN"
        self._buffer = ""
        self._step_buffer = ""
        self.logger = LoggerFactory.get_logger(name=f"SHELL - {self._id}")
        self._llm = StructuredLLM()

        env = os.environ.copy()
        env["TERM"] = term
        env["NO_COLOR"] = "1"
        env["COLUMNS"] = str(columns)
        env["PAGER"] = "cat"

        self.logger.info(f"Starting {shell_path} shell...")
        self.child = pexpect.spawn(
            "/bin/zsh",
            ["-l"],,
            encoding="utf-8",
            echo=False,
            env=env
        )

        self.logger.info("Starting zsh shell...")
        self.child = pexpect.spawn(
            "/bin/zsh",
            ["-l"],
            encoding="utf-8",
            echo=False,
            env=env
        )
        self.child.sendline('PS1="$ "')
        self.child.expect(r"\$ ", timeout=init_timeout)
        self.logger.info("Ready.")

    @abstractmethod
    def stream_command(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Run a command in the shell, stream output, and use the LLM to detect
        if user interaction is required.

        Args:
            sequence (str): Command to execute in the shell.
            hide_input (bool, optional): If True, masks the command in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: Either the final shell output (needs_action=False) or an LLM decision indicating that interaction is required.
        """
        pass

    @abstractmethod
    def send(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Send a sequence of input to the shell.

        Args:
            sequence (str): The input sequence to send.
            hide_input (bool, optional): If True, masks the input in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the shell's response.
        """
        pass

    @abstractmethod
    def send_line(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Send a sequence of input to the shell, followed by a newline (Enter).

        Args:
            sequence (str): The input sequence to send.
            hide_input (bool, optional): If True, masks the input in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the shell's response.
        """
        pass
    
    @abstractmethod
    def send_control(self, sequence: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Send a control sequence (e.g., Ctrl+C, Ctrl+D) to the shell.

        Args:
            sequence (str): The control sequence to send.
            hide_input (bool, optional): If True, masks the sequence in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the shell's response.
        """
        pass

    @abstractmethod
    def run_command(self, command: str, hide_input: bool = False) -> StreamToShellOutput:
        """
        Execute a command in the shell and return its output after completion.

        Args:
            command (str): The shell command to execute.
            hide_input (bool, optional): If True, masks the command in logs/output. Defaults to False.

        Returns:
            StreamToShellOutput: A structured object representing the command output.
        """
        pass
    
    def _mask_sequence(self, sequence: str, hide_input: bool = False) -> str:
        """
        Mask a sequence of characters with asterisks if hide_input is True.

        Args:
            sequence (str): The sequence to potentially mask.
            hide_input (bool, optional): Whether to mask the sequence. Defaults to False.

        Returns:
            str: The masked sequence or the original sequence if hide_input is False.
        """
        return "*" * len(sequence) if hide_input else sequence
    
    def _mask_sequence_in_text(self, text: str, sequence: str, hide_input: bool = False) -> str:
        """
        Replace all occurrences of a sequence in a text with asterisks if hide_input is True.

        Args:
            text (str): The text in which to mask the sequence.
            sequence (str): The sequence to mask.
            hide_input (bool, optional): Whether to mask the sequence. Defaults to False.

        Returns:
            str: The text with the sequence masked or unchanged if hide_input is False.
        """
        return text.replace(sequence, "*" * len(sequence)) if hide_input else text
    
    def _redact_text(self, text: str) -> str:
        """
        Redact all secrets and personal information in the text by applying mask.

        Args:
            text (str): The text that should be scanned for secrets and redacted.

        Returns:
            str: The redacted text.
        """
        return SecretsRedactor.mask_secrets_in_text(text)
    
    def _remove_zsh_artifacts(self, sequence: str) -> str:
        """
        Remove Zsh PROMPT_SP artifacts (a '%' followed by spaces and a CR).
        
        This artifact is generated by Zsh when a command output doesn't end 
        with a newline. Zsh prints a '%' (inverted) and fills the rest of 
        the line with spaces.
        Args:
            sequence (str): The input string that may contain Zsh artifacts.
        Returns:
            str: The input string with Zsh artifacts removed.
        """
        return ZSH_ARTIFACT_RE.sub("", sequence)

    def _remove_ansi_escape_characters(self, sequence: str) -> str:
        """
        Remove ANSI escape sequences from a given string.

        ANSI escape sequences are used in terminal text formatting
        (e.g., adding colors, bold, underline). This function strips
        those sequences, returning plain text.

        Args:
            sequence (str): The input string that may contain ANSI escape codes.

        Returns:
            str: The input string with all ANSI escape codes removed.

        Example:
            >>> remove_ansi_escape_characters("\\x1b[31mHello\\x1b[0m")
            'Hello'
        """
        return ANSI_ESCAPE_RE.sub("", sequence)

    def _remove_carriage_character(self, sequence: str) -> str:
        """
        Remove all carriage return characters ('\\r') from a given string.

        Args:
            sequence (str): The input string that may contain carriage return characters.

        Returns:
            str: A new string with all carriage return characters removed.
        """
        return sequence.replace(CARRIAGE_CHARACTER, "")

    def _apply_backspaces(self, sequence: str) -> str:
        """
        Simulates the effect of backspace characters in a string.

        This function processes a string that may contain the backspace character (`\b`).
        Each backspace removes the most recent non-backspace character from the result,
        if one exists. If a backspace appears at the beginning of the string (when there
        are no characters to remove), it is ignored.

        Args:
            sequence (str): The input string which may contain regular characters and `\b`.

        Returns:
            str: A new string with the backspace effects applied.

        Example:
            >>> apply_backspaces("abc\bde")
            'abde'
            >>> apply_backspaces("hello\b\b\b world")
            'he world'
            >>> apply_backspaces("\b\btest")
            'test'
        """

        result = []
        for c in sequence:
            if c == "\b":
                if result:
                    result.pop()
            else:
                result.append(c)

        return "".join(result)

    def _is_progress_noise(self, sequence: str) -> bool:
        """
        Detect spinner frames or progress bar lines in a string.

        This function identifies "progress noise" in CLI output, including:
        1. Progress bars matching the existing regex `PROGRESS_RE`
        (e.g., "23.4%###").
        2. Spinner frames, consisting entirely of characters in `SPINNER_CHARS`.
        The set includes Braille spinners (⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇) as well
        as common ASCII spinners (|, /, -, \\).

        Args:
            sequence (str): The string to check.

        Returns:
            bool: True if the string is likely a spinner frame or a progress bar line,
                False otherwise.

        Examples:
            >>> is_progress_noise("23.4%###")
            True
            >>> is_progress_noise("⠙")
            True
            >>> is_progress_noise("|/-\\")
            True
            >>> is_progress_noise("Processing complete")
            False
        """

        if PROGRESS_RE.search(sequence):
            return True
        if sequence and all(ch in SPINNER_CHARS for ch in sequence.strip()):
            return True
        return False

    def _clean_chunk(self, chunk: str) -> str:
        """
        Clean a chunk of shell output using a series of transformations.

        Steps:
            - Remove ANSI escape codes.
            - Remove Zsh artifacts.
            - Remove carriage returns.
            - Apply backspace character handling.
            - Strip leading/trailing whitespace.

        Args:
            chunk (str): Raw shell output.

        Returns:
            str: Cleaned shell output.
        """
        cleaning_pipeline = [
            self._remove_ansi_escape_characters,
            self._remove_zsh_artifacts,
            self._remove_carriage_character,
            self._apply_backspaces,
        ]
        return reduce(lambda acc, func: func(acc), cleaning_pipeline, chunk)

    def _write_log(self, text: str, fname: str = "logs.txt") -> None:
        with open(fname, "a") as f:
            f.write(text)

    def clean_step_buffer(self) -> None:
        self._step_buffer = ""

    def get_step_buffer(self) -> str:
        return self._step_buffer
