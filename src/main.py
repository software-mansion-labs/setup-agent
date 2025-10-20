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

def route_planner(state: GraphState):
    next_agent = state.get("next_agent")

    if next_agent in [Node.INSTALLER_AGENT.value, Node.RUNNER_AGENT.value]:
        return next_agent
    
    return END

def route_auditor(state: GraphState):
    next_agent = state.get("next_agent")

    if next_agent in [Node.INSTALLER_AGENT.value, Node.RUNNER_AGENT.value]:
        return next_agent
    
    return Node.PLANNER_AGENT.value

def main():
    load_dotenv()

    _ = Config.init(project_root="projects/expensify/App")
    _ = ShellRegistry.init()

    guidelines_retriever_node = GuidelinesRetrieverNode()
    task_identifier_node = TaskIdentifierNode()
    planner_agent = Planner()
    installer_agent = Installer()
    runner_agent = Runner()
    auditor_agent = Auditor()

    graph = StateGraph(GraphState)
    graph.add_node(
        Node.GUIDELINES_RETRIEVER_NODE.value, guidelines_retriever_node.invoke
    )
    graph.add_node(Node.TASK_IDENTIFIER_NODE.value, task_identifier_node.invoke)
    graph.add_node(Node.PLANNER_AGENT.value, planner_agent.invoke)
    graph.add_node(Node.INSTALLER_AGENT.value, installer_agent.invoke)
    graph.add_node(Node.RUNNER_AGENT.value, runner_agent.invoke)
    graph.add_node(Node.AUDITOR_AGENT.value, auditor_agent.invoke)

    graph.add_edge(START, Node.GUIDELINES_RETRIEVER_NODE.value)
    graph.add_edge(
        Node.GUIDELINES_RETRIEVER_NODE.value,
        Node.TASK_IDENTIFIER_NODE.value,
    )
    graph.add_edge(Node.TASK_IDENTIFIER_NODE.value, Node.PLANNER_AGENT.value)
    graph.add_edge(Node.PLANNER_AGENT.value, Node.INSTALLER_AGENT.value)
    graph.add_edge(Node.INSTALLER_AGENT.value, Node.AUDITOR_AGENT.value)
    graph.add_edge(Node.RUNNER_AGENT.value, Node.AUDITOR_AGENT.value)

    graph.add_conditional_edges(
        Node.PLANNER_AGENT.value,
        route_planner,
        {
            Node.INSTALLER_AGENT.value: Node.INSTALLER_AGENT.value,
            Node.RUNNER_AGENT.value: Node.RUNNER_AGENT.value,
            END: END
        }
    )

    graph.add_conditional_edges(
        Node.AUDITOR_AGENT.value,
        route_auditor,
        {
            Node.INSTALLER_AGENT.value: Node.INSTALLER_AGENT.value,
            Node.RUNNER_AGENT.value: Node.RUNNER_AGENT.value,
            Node.PLANNER_AGENT.value: Node.PLANNER_AGENT.value
        }
    )

    workflow = graph.compile()

    workflow.invoke(
        GraphState(
            messages=[
                HumanMessage(
                    content="Install all required tools according to the provided guidelines."
                )
            ],
            plan=None,
            finished_steps=[],
            failed_steps=[],
            errors=[],
            next_node=Node.GUIDELINES_RETRIEVER_NODE,
            guideline_files=[],
            possible_tasks=[],
            chosen_task=""
        )
    )


if __name__ == "__main__":
    main()
