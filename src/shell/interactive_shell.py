import json
import pexpect
import getpass
from model import get_llm
from langchain_core.messages import HumanMessage
from pydantic import BaseModel
from utils.remove_ansi_escape_characters import remove_ansi_escape_characters
from utils.apply_backspaces import apply_backspaces
from utils.remove_carriage_characters import remove_carriage_character
from utils.is_progress_noise import is_progress_noise
from functools import reduce

class Decision(BaseModel):
    needs_action: bool
    reason: str

class InteractiveShell:
    def __init__(self):
        self._llm = get_llm()
        self._buffer = ""
        print("[Shell] Starting persistent zsh shell...")
        self.child = pexpect.spawn("/bin/zsh", ["-l"], encoding="utf-8", echo=False)
        self.child.sendline('PS1="$ "')
        self.child.expect(r"\$ ", timeout=10)
        print("[Shell] Ready.")

    def send(self, text: str):
        self.child.sendline(text)

    def authenticate(self):
        passwd = getpass.getpass("\n[Shell] Enter your sudo password: ")

        return self.stream_command(command=passwd.strip())

    def run_command_with_confirmation(self, command: str):
        return self.stream_command(command=command)

    def _clean_chunk(self, chunk: str) -> str:
        """Remove ANSI escape codes, carriage returns, and handle backspaces."""

        cleaning_pipeline = [
            remove_ansi_escape_characters,
            remove_carriage_character,
            apply_backspaces
        ]
        
        return reduce(lambda acc, func: func(acc), cleaning_pipeline, chunk)
    
    def stream_command(self, command: str):
        """Run a command, stream output, and determine if action is needed using LLM."""
        self._buffer = ""
        self.send(command)

        print(f"[Shell][DEBUG] Running command: {command}.")

        llm_called = False

        while True:
            try:
                chunk = self.child.read_nonblocking(65536, timeout=2.0)
                clean_chunk = self._clean_chunk(chunk)
                self._buffer += clean_chunk
                self._step_buffer += clean_chunk

                if not is_progress_noise(clean_chunk):
                    with open("logs.txt", "a") as f:
                        f.write(clean_chunk)

                llm_called = False

                if clean_chunk.strip().endswith("$"):
                    print("[Shell][DEBUG] Detected shell prompt; command finished.")
                    break

            except pexpect.TIMEOUT:
                if not llm_called:
                    print("[Shell][DEBUG] Output stable for 2s; invoking LLM...")
                    llm_called = True
                    prompt = f"""
                        You are a command-line assistant. Analyze this shell output and determine if the system is **actually waiting for user input right now**.  

                        Output:
                        \"\"\"{self._buffer}\"\"\"
                    """

                    try:
                        structured_llm = self._llm.with_structured_output(Decision)
                        decision: Decision = structured_llm.invoke(
                            [HumanMessage(content=prompt)]
                        )

                        result = {
                            "needs_action": decision.needs_action,
                            "reason": decision.reason,
                            "last_chunk": self._buffer,
                        }
                        with open("log.jsonl", "a") as f:
                            f.write(json.dumps(result) + "\n")

                        if decision.needs_action:
                            print("[Shell][DEBUG] Shell awaits for interaction.")

                            with open("logs.txt", "a") as f:
                                f.write("\n")

                            return result

                    except Exception as e:
                        print(f"[Shell][ERROR] LLM invocation failed: {e}")
            except pexpect.EOF:
                print("[Shell][ERROR] EOF reached; shell closed.")
                break
            except Exception:
                print(f"[Shell][ERROR] Exception: {e}.")
                break

        with open("logs.txt", "a") as f:
            f.write("\n")

        print("\n[Shell] Command finished.\n")
        return {"needs_action": False, "output": self._buffer.strip()}

interactive_shell = InteractiveShell()
