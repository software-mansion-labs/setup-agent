from enum import Enum


class ChooseActionPromptOptions(str, Enum):
    CONTINUE = "Continue"
    SKIP = "Skip"
    LEARN_MORE = "Learn more"
