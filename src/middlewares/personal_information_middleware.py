from langchain.agents.middleware import AgentMiddleware
from typing import Callable

from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command
from detect_secrets.core.secrets_collection import SecretsCollection
import re
from typing import Dict

def retrieve_key_value_pairs(text: str) -> Dict[str, str]:
    pattern = r'(\w+)=(".*?"|\'.*?\'|[^\s]+)'
    pairs = re.findall(pattern, text)
    result: Dict[str, str] = {
        key: value.strip('"').strip("'")
        for key, value in pairs
    }

    return result

class PersonalInformationMiddleware(AgentMiddleware):
    def wrap_tool_call(self, request: ToolCallRequest, handler: Callable[[ToolCallRequest], ToolMessage | Command]) -> ToolMessage | Command:
        result = handler(request)

        if isinstance(result, ToolMessage):
            content_str = result.content if isinstance(result.content, str) else str(result.content)
            result_output_values = retrieve_key_value_pairs(content_str).values()
            secrets_collection = SecretsCollection()
            potential_secrets = []
            for value in result_output_values:
                for secret in secrets_collection.scan_text(value):
                    if secret["is_secret"]:
                        potential_secrets.append(secret["secret_value"])

            for secret in set(potential_secrets):
                content_str = content_str.replace(secret, "[REDACTED_PERSONAL_INFORMATION]")
            result.content = content_str

        return result
