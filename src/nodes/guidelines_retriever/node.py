from config import Config
from typing import List
import os
from itertools import chain
from graph_state import GuidelineFile, Node, GraphState
from questionary import checkbox, Choice, path
from nodes.base_llm_node import BaseLLMNode
from utils.file_loader import FileLoader
from nodes.guidelines_retriever.prompts import GuidelinesRetrieverPrompts
from nodes.guidelines_retriever.types import PickedEntries, GuidelineFileCheck


class GuidelinesRetrieverNode(BaseLLMNode):
    def __init__(self):
        super().__init__(name=Node.GUIDELINES_RETRIEVER_NODE.value)
        self._config = Config.get()
        self._project_root = self._config.project_root
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
            content = self._file_loader.load_document(
                os.path.join(self._project_root, file)
            )
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

        sorted_guideline_files = sorted(guideline_files, key=lambda gf: len(gf.file.split("/")))
        OTHER_OPTION = "Other: (Enter manual path)"
        choices = [*[gf.file for gf in sorted_guideline_files], OTHER_OPTION]

        selected_files = checkbox(
            message="Select guideline files to use",
            choices=choices,
            default=choices[0] if choices else None,
            validate=lambda c: True if len(c) > 0 else "You must choose at least one option."
        ).ask()

        manual_paths = []      
        if OTHER_OPTION in selected_files:
            selected_files.remove(OTHER_OPTION)
            
            custom_path = path(
                message="Please enter the file path:",
                validate=lambda val: len(selected_files) > 0 or len(val.strip()) > 0 or "You must choose at least one valid file."
            ).ask()
            
            if custom_path:
                manual_paths.append(custom_path)

        final_selection = [gf for gf in guideline_files if gf.file in selected_files]
        for manual_path in manual_paths:
            if manual_path in final_selection:
                continue
            content = self._file_loader.load_document(manual_path)
            if not content:
                continue
            final_selection.append(GuidelineFile(file=manual_path, content=content))

        return final_selection

    def _get_guideline_files(self) -> List[GuidelineFile]:
        if self._config.guideline_files:
            return [GuidelineFile(file=file, content=self._file_loader.load_document(file)) for file in self._config.guideline_files]
        else:
            supported_files = self._collect_supported_files()
            relevant_files = self._filter_non_relevant_files(supported_files)
            return self._pick_guideline_files_from_content(relevant_files)

    def invoke(self, state: GraphState) -> GraphState:
        self.logger.info("Retrieving guidelines from the project")
        guideline_files = self._get_guideline_files()
        selected_files = self._prompt_user_selection(guideline_files=guideline_files)
        state["guideline_files"] = selected_files

        return state
