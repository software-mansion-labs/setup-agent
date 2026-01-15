from typing import Callable, Union

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

from detect_secrets.core.secrets_collection import SecretsCollection


class PersonalInformationMiddleware(AgentMiddleware):
    """Middleware to redact sensitive information from tool outputs.

    This middleware intercepts the result of a tool execution (ToolMessage).
    It utilizes secret detectors to scan the output content for potential
    secrets or PII and replaces them with a redaction placeholder before
    the message is passed back to the agent.
    """

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Union[ToolMessage, Command]],
    ) -> Union[ToolMessage, Command]:
        """Intercepts the tool call execution to sanitize the output.

        Executes the underlying tool handler first. If the result is a
        `ToolMessage`, it scans the content for secrets and redacts them.
        If the result is a `Command` (used for graph control flow), it returns
        it unmodified.

        Args:
            request (ToolCallRequest): The request object containing the tool
                name, arguments, and context.
            handler (Callable[[ToolCallRequest], Union[ToolMessage, Command]]):
                The callable that executes the actual tool logic.

        Returns:
            Union[ToolMessage, Command]: The sanitized ToolMessage with secrets
            redacted, or the original Command object.
        """
        result = handler(request)

        if isinstance(result, ToolMessage):
            updated_result = result.model_copy()
            content_str = str(result.content)
            secrets_collection = SecretsCollection()
            potential_secrets = []
            for secret in secrets_collection.scan_text(content_str):
                if secret["is_secret"]:
                    potential_secrets.append(secret["secret_value"])

            for secret in set(potential_secrets):
                content_str = content_str.replace(
                    secret, "[REDACTED_PERSONAL_INFORMATION]"
                )
            updated_result.content = content_str
            return updated_result

        return result
