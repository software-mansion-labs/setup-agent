from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from agents.runner.agent import Runner
from graph_state import GraphState, Node
from nodes import GuidelinesRetrieverNode, TaskIdentifierNode
from agents.installer.agent import Installer
from agents.planner.agent import Planner
from agents.auditor.agent import Auditor
from dotenv import load_dotenv
from config import Config
from shell import ShellRegistry
from typing import List


class WorkflowBuilder:
    def __init__(self, project_root: str = ".", guideline_files: List[str] = []):
        load_dotenv()
        Config.init(project_root=project_root, guideline_files=guideline_files)
        ShellRegistry.init()

        self.guidelines_node = GuidelinesRetrieverNode()
        self.task_node = TaskIdentifierNode()
        self.planner_agent = Planner()
        self.installer_agent = Installer()
        self.runner_agent = Runner()
        self.auditor_agent = Auditor()

        self.graph = StateGraph(GraphState)
        self._add_nodes()
        self._add_edges()
        self._add_conditional_edges()

        self.workflow = self.graph.compile()

    def _add_nodes(self):
        self.graph.add_node(
            Node.GUIDELINES_RETRIEVER_NODE.value, self.guidelines_node.invoke
        )
        self.graph.add_node(Node.TASK_IDENTIFIER_NODE.value, self.task_node.invoke)
        self.graph.add_node(Node.PLANNER_AGENT.value, self.planner_agent.invoke)
        self.graph.add_node(Node.INSTALLER_AGENT.value, self.installer_agent.invoke)
        self.graph.add_node(Node.RUNNER_AGENT.value, self.runner_agent.invoke)
        self.graph.add_node(Node.AUDITOR_AGENT.value, self.auditor_agent.invoke)

    def _add_edges(self):
        self.graph.add_edge(START, Node.GUIDELINES_RETRIEVER_NODE.value)
        self.graph.add_edge(
            Node.GUIDELINES_RETRIEVER_NODE.value, Node.TASK_IDENTIFIER_NODE.value
        )
        self.graph.add_edge(Node.TASK_IDENTIFIER_NODE.value, Node.PLANNER_AGENT.value)
        self.graph.add_edge(Node.PLANNER_AGENT.value, Node.INSTALLER_AGENT.value)
        self.graph.add_edge(Node.INSTALLER_AGENT.value, Node.AUDITOR_AGENT.value)
        self.graph.add_edge(Node.RUNNER_AGENT.value, Node.AUDITOR_AGENT.value)

    def _add_conditional_edges(self):
        self.graph.add_conditional_edges(
            Node.PLANNER_AGENT.value,
            self.route_planner,
            {
                Node.INSTALLER_AGENT.value: Node.INSTALLER_AGENT.value,
                Node.RUNNER_AGENT.value: Node.RUNNER_AGENT.value,
                END: END,
            },
        )

        self.graph.add_conditional_edges(
            Node.AUDITOR_AGENT.value,
            self.route_auditor,
            {
                Node.INSTALLER_AGENT.value: Node.INSTALLER_AGENT.value,
                Node.RUNNER_AGENT.value: Node.RUNNER_AGENT.value,
                Node.PLANNER_AGENT.value: Node.PLANNER_AGENT.value,
            },
        )

    @staticmethod
    def route_planner(state: GraphState):
        next_node = state.get("next_node")
        if not next_node:
            return END
        if next_node in [Node.INSTALLER_AGENT.value, Node.RUNNER_AGENT.value]:
            return next_node
        return END

    @staticmethod
    def route_auditor(state: GraphState):
        next_node = state.get("next_node")
        if not next_node:
            return END
        if next_node in [Node.INSTALLER_AGENT.value, Node.RUNNER_AGENT.value]:
            return next_node
        return Node.PLANNER_AGENT.value

    def run(self, initial_message: str):
        self.workflow.invoke(
            GraphState(
                messages=[HumanMessage(content=initial_message)],
                plan=None,
                finished_steps=[],
                failed_steps=[],
                errors=[],
                next_node=Node.GUIDELINES_RETRIEVER_NODE,
                guideline_files=[],
                possible_tasks=[],
                chosen_task="",
            )
        )
