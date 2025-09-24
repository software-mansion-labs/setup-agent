from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from agents.runner import runner
from graph_state import GraphState
from agents.agents import AgentNode
from agents.planner import planner
from agents.installer import installer
from dotenv import load_dotenv
from shell.interactive_shell import get_interactive_shell, InteractiveShell


# TODO: update workflow by adding condtional reverse edges
def main():
    load_dotenv()

    graph = StateGraph(GraphState)
    graph.add_node(AgentNode.PLANNER, planner)
    graph.add_node(AgentNode.INSTALLER, installer)
    graph.add_node(AgentNode.RUNNER, runner)

    graph.add_edge(START, AgentNode.PLANNER)
    graph.add_edge(AgentNode.PLANNER, AgentNode.INSTALLER)
    graph.add_edge(AgentNode.INSTALLER, AgentNode.RUNNER)
    graph.add_edge(AgentNode.RUNNER, END)

    workflow = graph.compile()

    workflow.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Install all required tools according to the provided guidelines."
                )
            ]
        }
    )

    interactive_shell = get_interactive_shell()
    interactive_shell.run_command("ls -al")

if __name__ == "__main__":
    main()
