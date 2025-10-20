from collections import deque
import json
from agents.base_agent import BaseAgent
from graph_state import GraphState, Step, Substep
from shell import ShellRegistry
from tools.websearch import get_websearch_tool
from typing import List
from config import Config
from InquirerPy import inquirer
from langchain_core.messages import HumanMessage
from agents.planner.types import ReadmeAnalysis
from nodes import Node
from agents.planner.prompts import PlannerPrompts

class Planner(BaseAgent):
    def __init__(self):
        websearch_tool = get_websearch_tool()

        tools = [websearch_tool]
        super().__init__(
            name=Node.PLANNER_AGENT,
            prompt=PlannerPrompts.AGENT_DESCRIPTION_PROMPT,
            tools=tools,
        )
        self.project_root = Config.get().project_root
        self.shell_registry = ShellRegistry.get()
        
        self.cd_substep = Substep(
            description="Navigate to the project root directory",
            suggested_commands=[f"cd {self.project_root}"],
        )

        self.cd_step = Step(
            description="Navigate to the App project directory",
            substeps=[self.cd_substep],
            assigned_agent=Node.INSTALLER_AGENT,
            run_in_separate_shell=False,
        )

    def _first_analysis(self, state: GraphState) -> GraphState:
        guideline_files = state["guideline_files"]

        chosen_task = state["chosen_task"]

        if not guideline_files:
            state["plan"] = deque([
                Step(
                    description="No README found — unable to plan installation.",
                    substeps=[],
                    assigned_agent=Node.INSTALLER_AGENT
                )
            ])
            return state
        
        FILE_SEPARATOR = "=" * 10 + "\n"
        guideline_files_merged_content = FILE_SEPARATOR.join([guideline.content for guideline in guideline_files])

        with open("test.txt", "w") as f:
            f.write(guideline_files_merged_content)

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.FIRST_GUIDELINES_ANALYSIS,
            f"raw_texts: {guideline_files_merged_content}\nproject_root:{self.project_root}\n**GOAL**: {chosen_task}",
        )

        output_file = "plan.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis.model_dump(), f, indent=2, ensure_ascii=False)

        def assign_shell_ids(steps: List[Step]) -> List[Step]:
            for step in steps:
                if step.run_in_separate_shell:
                    step.substeps = [self.cd_substep] + step.substeps
                    step.shell_id = self.shell_registry.register_new_shell()
            return steps

        plan_steps = assign_shell_ids([self.cd_step] + analysis.plan)
        state["plan"] = deque(plan_steps)
        return state

    def _handle_errors(self, state: GraphState) -> GraphState:
        errors = state.get("errors", [])
        if not errors:
            return state

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.HANDLE_ERRORS,
            input_text=f"errors: {list(errors)}",
        )

        for step in analysis.plan:
            if step.run_in_separate_shell:
                step.substeps = [self.cd_substep] + step.substeps
                step.shell_id = self.shell_registry.register_new_shell()

        state["plan"] = deque(analysis.plan) + state.get("plan", deque())
        state["errors"] = []
        return state

    def _handle_failed_steps(self, state: GraphState) -> GraphState:
        failed_steps = state.get("failed_steps")
        if not failed_steps or len(failed_steps) == 0:
            return state

        analysis: ReadmeAnalysis = self._invoke_structured_llm(
            ReadmeAnalysis,
            PlannerPrompts.HANDLE_FAILED_STEPS,
            input_text=f"failed_steps: {list(failed_steps)}",
        )

        for step in analysis.plan:
            if step.run_in_separate_shell:
                step.substeps = [self.cd_substep] + step.substeps
                step.shell_id = self.shell_registry.register_new_shell()

        state["plan"] = deque(analysis.plan) + deque([failed_step.step for failed_step in failed_steps]) + state.get("plan", deque())
        state["failed_steps"] = []
        return state

    def _ensure_installation_success(self, state: GraphState) -> GraphState:
        """
        Ask the user if the installation/process succeeded.
        If not, have a mini-chat with the user where the agent asks questions to clarify.
        """

        print("[Planner] Verifying if installation succeeded...")

        user_choice = inquirer.select( # type: ignore
            message="Did the installation/process achieve the desired goal?",
            choices=["Yes, everything worked", "No, there was a problem"],
            default="Yes, everything worked"
        ).execute()

        if user_choice == "Yes, everything worked":
            print("[Planner] User confirmed installation success.")
            state["installation_success"] = True # type: ignore
            return state

        problem_description = inquirer.text( # type: ignore
            message="Please describe the problem or paste the error/output here:"
        ).execute()

        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(problem_description) # type: ignore

        print("[Planner] Let’s clarify the problem with a few follow-up questions.")

        continue_chat = True
        while continue_chat:
            system_prompt = (
                "You are a planner agent helping a user fix installation issues. "
                "The user reported the following problem:\n"
                f"{problem_description}\n\n"
                "Ask ONE concise clarifying question to understand the issue better. "
                "Do NOT provide a solution, only ask."
                "If you don't have any more questions, return empty string."
            )

            try:
                result = self.agent.invoke({"messages": [HumanMessage(content=system_prompt)]})
                agent_question = result["messages"][-1].content.strip()
            except Exception as e:
                print(f"[Planner] Failed to generate agent question: {e}")
                break

            if not agent_question:
                break

            user_reply = inquirer.text(message=f"[Agent] {agent_question}\nYour answer:").execute() # type: ignore
            if not user_reply.strip():
                break

            state["errors"].append(user_reply) # type: ignore
            state["plan"].appendleft(state["finished_steps"][-1].step) # type: ignore

        print("[Planner] Problem details collected. Will adjust the plan accordingly.")
        return state

    def _decide_next_agent(self, state: GraphState) -> GraphState:
        plan = state.get("plan", deque())
        if not plan:
            state["next_node"] = None
            return state

        next_step = plan[0]
        state["next_node"] = next_step.assigned_agent
        return state

    def invoke(self, state: GraphState) -> GraphState:
        print("[Planner] Planning unified step sequence...")

        if "plan" not in state:
            self._first_analysis(state)
            
        state = self._handle_failed_steps(state)

        if len(state["plan"]) == 0:
            self._ensure_installation_success(state)
            state = self._handle_errors(state)

        state = self._decide_next_agent(state)
        return state
