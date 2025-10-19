from enum import Enum


class WorkflowNode(str, Enum):
    PLANNER = "planner_agent"
    INSTALLER = "installer_agent"
    RUNNER = "runner_agent"
    GUIDELINES_RETRIEVER_NODE = "guidelines_retriever_node"
