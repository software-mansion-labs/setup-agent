from abc import abstractmethod, ABC
import pexpect
import re
from uuid import UUID
from typing import Optional
from shell.types import StreamToShellOutput
from functools import reduce
from utils.logger import LoggerFactory
from llm import StructuredLLM

ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
PROGRESS_RE = re.compile(r"\d{1,3}\.\d%#+\s*")
SPINNER_CHARS = set("⠏⠋⠙⠹⠸⠼⠴⠦⠧⠇|/-\\")
CARRIAGE_CHARACTER = "\r"


class BaseShell(ABC):
    def __init__(self, id: Optional[UUID] = None, init_timeout: int = 65536):
        self._id = str(id) if id else "MAIN"
        self._buffer = ""
        self._step_buffer = ""
        self.logger = LoggerFactory.get_logger(name=f"SHELL - {self._id}")
        self._llm = StructuredLLM()

        self.logger.info("Starting zsh shell...")
        self.child = pexpect.spawn("/bin/zsh", ["-l"], encoding="utf-8", echo=False)
        self.child.sendline('PS1="$ "')
        self.child.expect(r"\$ ", timeout=init_timeout)
        self.logger.info("Ready.")

    @abstractmethod
    def stream_command(self, command: str, hide_input: bool = False) -> StreamToShellOutput:
        """Run a command in the shell and return structured results."""
        pass

    @abstractmethod
    def run_command(self, command: str, hide_input: bool = False) -> StreamToShellOutput:
        return self.stream_command(command=command, hide_input=hide_input)

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
            self._remove_carriage_character,
            self._apply_backspaces,
        ]
        return reduce(lambda acc, func: func(acc), cleaning_pipeline, chunk).strip()

    def _write_log(self, text: str, fname: str = "logs.txt") -> None:
        with open(fname, "a") as f:
            f.write(text)

    def send(self, text: str) -> None:
        self.child.sendline(text)

    def clean_step_buffer(self) -> None:
        self._step_buffer = ""

    def get_step_buffer(self) -> str:
        return self._step_buffer
