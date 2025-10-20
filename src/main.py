from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from agents.runner import runner
from graph_state import GraphState, Node
from nodes import GuidelinesRetrieverNode, TaskIdentifierNode
from agents.installer import installer
from agents.planner.agent import Planner
from dotenv import load_dotenv
from config import Config
from shell import ShellRegistry

# TODO: update workflow by adding condtional reverse edges
def main():
    load_dotenv()

    _ = Config.init()
    _ = ShellRegistry.init()

    guidelines_retriever_node = GuidelinesRetrieverNode()
    task_identifier_node = TaskIdentifierNode()
    planner_agent = Planner()

    graph = StateGraph(GraphState)
    graph.add_node(
        Node.GUIDELINES_RETRIEVER_NODE.value, guidelines_retriever_node.invoke
    )
    graph.add_node(Node.TASK_IDENTIFIER_NODE.value, task_identifier_node.invoke)
    graph.add_node(Node.PLANNER_AGENT.value, planner_agent.invoke)
    graph.add_node(Node.INSTALLER_AGENT.value, installer)
    graph.add_node(Node.RUNNER_AGENT.value, runner)

    graph.add_edge(START, Node.GUIDELINES_RETRIEVER_NODE.value)
    graph.add_edge(
        Node.GUIDELINES_RETRIEVER_NODE.value,
        Node.TASK_IDENTIFIER_NODE.value,
    )
    graph.add_edge(Node.TASK_IDENTIFIER_NODE.value, Node.PLANNER_AGENT.value)
    graph.add_edge(Node.PLANNER_AGENT.value, Node.INSTALLER_AGENT.value)
    graph.add_edge(Node.INSTALLER_AGENT.value, Node.RUNNER_AGENT.value)
    graph.add_edge(Node.RUNNER_AGENT.value, END)

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
