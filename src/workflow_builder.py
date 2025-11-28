from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph
from agents.runner.agent import Runner
from graph_state import GraphState, Node
from nodes import GuidelinesRetrieverNode, TaskIdentifierNode
from agents.installer.agent import Installer
from agents.planner.agent import Planner
from agents.auditor.agent import Auditor
from dotenv import load_dotenv
from config import Config
from shell import ShellRegistry
from typing import List, Optional
import sys
from utils.logger import LoggerFactory
from llm.model import LLMManager
from pathlib import Path


class WorkflowBuilder:
    def __init__(
            self,
            project_root: str = ".",
            guideline_files: List[str] = [],
            task: Optional[str] = None,
            model: str = "anthropic:claude-sonnet-4-5",
            log_file: Optional[str] = None,
            max_output_tokens: Optional[int] = None,
            max_retries: Optional[int] = None,
            temperature: Optional[float] = None,
            timeout: Optional[float] = None 
        ) -> None:
        load_dotenv(dotenv_path=Path.cwd() / ".env")
        Config.init(project_root=project_root, guideline_files=guideline_files, task=task)
        LLMManager.init(
            model=model,
            max_tokens=max_output_tokens,
            max_retries=max_retries,
            temperature=temperature,
            timeout=timeout
        )
        ShellRegistry.init(log_file=log_file)
        self.shell_registry = ShellRegistry.get()
        self.logger = LoggerFactory.get_logger(name="WORKFLOW_BUILDER")
        self._init_nodes()
        self._build_workflow()

    def _init_nodes(self) -> None:
        self.guidelines_node = GuidelinesRetrieverNode()
        self.task_node = TaskIdentifierNode()
        self.planner_agent = Planner()
        self.installer_agent = Installer()
        self.runner_agent = Runner()
        self.auditor_agent = Auditor()

    def _build_workflow(self):
        self.graph = StateGraph(GraphState)
        self._add_nodes()
        self._add_edges()
        self._add_conditional_edges()

        self.workflow = self.graph.compile()
        return self.workflow

    def _add_nodes(self) -> None:
        self.graph.add_node(
            Node.GUIDELINES_RETRIEVER_NODE.value, self.guidelines_node.invoke
        )
        self.graph.add_node(Node.TASK_IDENTIFIER_NODE.value, self.task_node.invoke)
        self.graph.add_node(Node.PLANNER_AGENT.value, self.planner_agent.invoke)
        self.graph.add_node(Node.INSTALLER_AGENT.value, self.installer_agent.invoke)
        self.graph.add_node(Node.RUNNER_AGENT.value, self.runner_agent.invoke)
        self.graph.add_node(Node.AUDITOR_AGENT.value, self.auditor_agent.invoke)

    def _add_edges(self) -> None:
        self.graph.add_edge(Node.START.value, Node.GUIDELINES_RETRIEVER_NODE.value)
        self.graph.add_edge(
            Node.GUIDELINES_RETRIEVER_NODE.value, Node.TASK_IDENTIFIER_NODE.value
        )
        self.graph.add_edge(Node.TASK_IDENTIFIER_NODE.value, Node.PLANNER_AGENT.value)
        self.graph.add_edge(Node.INSTALLER_AGENT.value, Node.AUDITOR_AGENT.value)
        self.graph.add_edge(Node.RUNNER_AGENT.value, Node.AUDITOR_AGENT.value)
        self.graph.add_edge(Node.AUDITOR_AGENT.value, Node.PLANNER_AGENT.value)

    def _add_conditional_edges(self) -> None:
        self.graph.add_conditional_edges(
            Node.PLANNER_AGENT.value,
            self.route_planner,
            {
                Node.INSTALLER_AGENT.value: Node.INSTALLER_AGENT.value,
                Node.RUNNER_AGENT.value: Node.RUNNER_AGENT.value,
                Node.END.value: Node.END.value,
            },
        )

    @staticmethod
    def route_planner(state: GraphState) -> Node:
        next_node = state.get("next_node")

        if not next_node:
            return Node.END
        if next_node in [Node.INSTALLER_AGENT.value, Node.RUNNER_AGENT.value]:
            return next_node
        return Node.END

    def run(self, initial_message: str):
        try:
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
                ),
                {"recursion_limit": 100}
            )
        except KeyboardInterrupt:
            self.logger.error("\nInterrupted by user. Cleaning up to exit gracefully...")
        finally:
            self.shell_registry.cleanup()
            sys.exit(0)

if __name__ == "__main__":
    builder = WorkflowBuilder(project_root="projects/expensify/App")
    builder.run("Install all required tools according to the provided guidelines")