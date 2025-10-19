from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from agents.runner import runner
from graph_state import GraphState
from nodes.nodes import WorkflowNode
from agents.planner import planner
from agents.installer import installer
from nodes.guidelines_retriever import GuidelinesRetrieverNode
from dotenv import load_dotenv
from shell.safe_interactive_shell import get_safe_interactive_shell
from nodes.guidelines_retriever import GuidelinesRetrieverNode
from config import Config

# TODO: update workflow by adding condtional reverse edges
def main():
    load_dotenv()

    config = Config.init(".")
    guidelines_retriever_node = GuidelinesRetrieverNode()

    graph = StateGraph(GraphState)
    graph.add_node(WorkflowNode.GUIDELINES_RETRIEVER_NODE.value, guidelines_retriever_node.invoke)
    graph.add_node(WorkflowNode.PLANNER.value, planner)
    graph.add_node(WorkflowNode.INSTALLER.value, installer)
    graph.add_node(WorkflowNode.RUNNER.value, runner)

    graph.add_edge(START, WorkflowNode.GUIDELINES_RETRIEVER_NODE.value)
    graph.add_edge(WorkflowNode.GUIDELINES_RETRIEVER_NODE.value, WorkflowNode.PLANNER.value)
    graph.add_edge(WorkflowNode.PLANNER.value, WorkflowNode.INSTALLER.value)
    graph.add_edge(WorkflowNode.INSTALLER.value, WorkflowNode.RUNNER.value)
    graph.add_edge(WorkflowNode.RUNNER.value, END)

    workflow = graph.compile()

    workflow.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Install all required tools according to the provided guidelines."
                )
            ]
        }  # type: ignore
    )

if __name__ == "__main__":
    main()
