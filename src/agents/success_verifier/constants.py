from enum import Enum


class VerifierUserPrompts(str, Enum):
    CHECK_OUTCOME = "How did the installation/execution process go?"
    ERROR_NATURE = "What is the nature of the problem?"
    ERROR_DETAILS = "Please describe the details or paste the error log:"
    PROCEED_ACTION = "How would you like to proceed?"
    USER_ANSWER = "Your answer:"


class VerificationOutcome(str, Enum):
    SUCCESS = "Success - everything works as expected"
    PARTIAL_SUCCESS = "Partial success - works but with errors"
    FAILURE = "Failure - critical error occurred"


class ErrorCategory(str, Enum):
    TERMINAL = "Terminal error (Exception/Traceback)"
    MISSING_FILE = "Missing expected file/directory"
    HANG = "Application does not start (hang/freeze)"
    LOGIC = "Incorrect output/logic"
    OTHER = "Other issue"


class ClarificationChoice(str, Enum):
    ANSWER = "Answer the question"
    SKIP = "Skip this question"
    STOP = "Stop questioning and start fixing"
