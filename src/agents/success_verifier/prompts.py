from enum import Enum


class SuccessVerifierPrompts(str, Enum):
    SHOULD_END_CONVERSATION = (
        """
        Analyze if this error collection/troubleshooting conversation should end. Consider:

        1. **Explicit completion**: User says "done", "that's all", "nothing else", "finish"
        2. **Task fully resolved**: All errors collected, user confirms no more issues
        3. **Natural closure**: User provided all necessary information and acknowledged completion
        4. **Ready to proceed**: User indicates readiness to move to next phase
        5. **Success confirmation**: User confirmed success with no additional concerns

        Return 'end' with HIGH confidence for explicit completion signals.
        Return 'end' with MEDIUM confidence if error collection is complete and user shows no intent to add more.
        Return 'continue' if user might have more information to provide or issues to report.
        """
    )
