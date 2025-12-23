from enum import Enum


class ProcessAction(Enum):
    CONTINUE = "Continue with next task"
    PAUSE = "Do nothing (keep shells active)"
    EXIT = "Exit workflow"
