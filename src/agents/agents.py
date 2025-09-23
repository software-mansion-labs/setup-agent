from enum import Enum


class AgentNode(str, Enum):
    PLANNER = "planner_agent"
    INSTALLER = "installer_agent"
    RUNNER = "runner_agent"
