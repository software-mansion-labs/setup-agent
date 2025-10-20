from config import Config
from typing import List
import os
from itertools import chain
from graph_state import GuidelineFile, Node, GraphState
from InquirerPy.prompts import checkbox
from nodes.base_llm_node import BaseLLMNode
from utils.file_loader import FileLoader
from nodes.guidelines_retriever.prompts import GuidelinesRetrieverPrompts
from nodes.guidelines_retriever.types import PickedEntries, GuidelineFileCheck


class GuidelinesRetrieverNode(BaseLLMNode):
    def __init__(self):
        super().__init__(name=Node.GUIDELINES_RETRIEVER_NODE.value)
        config = Config.get()
        self._project_root = config.project_root
        self._file_loader = FileLoader(project_root=self._project_root)

    def _filter_non_relevant_subdirectories(self, subdir_paths: List[str]) -> List[str]:
        formatted_subdirs = "\n".join(f"- {s}" for s in subdir_paths)

        result: PickedEntries = self._invoke_structured_llm(
            PickedEntries,
            GuidelinesRetrieverPrompts.FILTER_SUBDIRS.value,
            f"List of subdirectories:\n{formatted_subdirs}",
        )

        return result.picked_entries

    def _filter_non_relevant_files(self, files: List[str]) -> List[str]:
        formatted_files = "\n".join(f"- {s}" for s in files)

        result: PickedEntries = self._invoke_structured_llm(
            PickedEntries,
            GuidelinesRetrieverPrompts.FILTER_FILES.value,
            f"List of files:\n{formatted_files}",
        )

        return result.picked_entries

    def _pick_guideline_files_from_content(
        self, files: List[str]
    ) -> List[GuidelineFile]:
        guideline_files: List[GuidelineFile] = []

        for file in files:
            content = self._file_loader.load_document(file)
            if not content.strip():
                continue

            input_text = f"File path: {file}\nContent Preview:\n{content}"

            result: GuidelineFileCheck = self._invoke_structured_llm(
                GuidelineFileCheck,
                GuidelinesRetrieverPrompts.CHECK_FILE_CONTENT.value,
                input_text,
            )

            if result.is_guideline:
                guideline_files.append(GuidelineFile(file=file, content=content))

        return guideline_files

    def _collect_supported_files(self) -> List[str]:
        """Discover all potentially relevant files (based on extensions and subdirs)."""
        direct_subdirs = self._file_loader.list_direct_subdirectories()
        relevant_subdirs = self._filter_non_relevant_subdirectories(direct_subdirs)
        direct_files = self._file_loader.list_direct_files(self._project_root)

        supported_files = (
            list(
                chain.from_iterable(
                    self._file_loader.list_supported_files(
                        os.path.join(self._project_root, d)
                    )
                    for d in relevant_subdirs
                )
            )
            + direct_files
        )

        self.logger.info(f"Supported files found: {len(supported_files)}")
        return supported_files

    def _prompt_user_selection(
        self, guideline_files: List[GuidelineFile]
    ) -> List[GuidelineFile]:
        if not guideline_files:
            self.logger.warning("No guideline files found.")
            return []

        choices = sorted(
            [gf.file for gf in guideline_files], key=lambda file: len(file.split("/"))
        )

        selected_files = checkbox.CheckboxPrompt(
            message="Select guideline files to use (↑↓ to move, space to toggle, enter to confirm):",
            choices=choices,
            cycle=True,
            default=[choices[0]] if choices else [],
        ).execute()

        selected = [gf for gf in guideline_files if gf.file in selected_files]
        return selected

    def invoke(self, state: GraphState) -> GraphState:
        self.logger.info("Retrieving guidelines from the project")
        supported_files = self._collect_supported_files()
        relevant_files = self._filter_non_relevant_files(supported_files)
        guideline_files = self._pick_guideline_files_from_content(relevant_files)
        selected_files = self._prompt_user_selection(guideline_files=guideline_files)
        state["guideline_files"] = selected_files

        return state
