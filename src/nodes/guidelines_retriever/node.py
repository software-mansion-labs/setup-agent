import os
from itertools import chain
from typing import List

from config import Config
from graph_state import GraphState, GuidelineFile, Node
from nodes.base_llm_node import BaseLLMNode
from nodes.guidelines_retriever.node_types import GuidelineFileCheck, PickedEntries
from nodes.guidelines_retriever.prompts import GuidelinesRetrieverPrompts
from user_prompts.guidelines_selector import GuidelinesSelector
from utils.file_loader import FileLoader


class GuidelinesRetrieverNode(BaseLLMNode):
    """Node responsible for identifying and retrieving project guideline files.

    This node scans the project directory structure, filters directories and files
    based on relevance (using LLM filtering), validates content to ensure it
    contains actual guidelines (e.g., coding standards, readmes), and prompts
    the user to select which guidelines should be active for the current workflow.

    Attributes:
        _config (Config): The global configuration settings.
        _project_root (str): The root directory of the project being analyzed.
        _file_loader (FileLoader): Utility for loading file system resources.
        _guidelines_selector (GuidelinesSelector): Helper for interactive guideline selection.
    """

    def __init__(self) -> None:
        """Initializes the GuidelinesRetrieverNode.

        Sets up the file loader and guideline selector utilities using the
        global configuration.
        """
        super().__init__(name=Node.GUIDELINES_RETRIEVER_NODE.value)
        self._config = Config.get()
        self._project_root = self._config.project_root
        self._file_loader = FileLoader(project_root=self._project_root)
        self._guidelines_selector = GuidelinesSelector(self._file_loader)

    def _filter_non_relevant_subdirectories(self, subdir_paths: List[str]) -> List[str]:
        """
        Filters out subdirectories that are likely not relevant for guidelines based on their names.

        Args:
            subdir_paths (List[str]): A list of subdirectory paths to evaluate.

        Returns:
            List[str]: A list of subdirectory paths deemed relevant by the LLM.
        """
        formatted_subdirs = "\n".join(f"- {s}" for s in subdir_paths)

        result: PickedEntries = self._invoke_structured_llm(
            PickedEntries,
            GuidelinesRetrieverPrompts.FILTER_SUBDIRS.value,
            f"List of subdirectories:\n{formatted_subdirs}",
        )

        return result.picked_entries

    def _filter_non_relevant_files(self, files: List[str]) -> List[str]:
        """
        Filters out files that are likely not relevant for guidelines based on their names.

        Args:
            files (List[str]): A list of file paths to evaluate.

        Returns:
            List[str]: A list of file paths deemed relevant by the LLM.
        """
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
        """
        Analyzes file content to identify actual guideline documents.

        Args:
            files (List[str]): A list of candidate file paths.

        Returns:
            List[GuidelineFile]: A list of GuidelineFile objects containing the path and content of confirmed guidelines.
        """
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
        """
        Discover all potentially relevant files (based on extensions and subdirs).

        Returns:
            List[str]: A list of all supported file paths found in relevant directories.
        """
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

    def _get_guideline_files(self) -> List[GuidelineFile]:
        """
        Retrieves the list of guideline files to be processed.

        Sources files either directly from the configuration (if provided) or by
        scanning the project structure and filtering for relevant content.

        Returns:
            List[GuidelineFile]: A list of GuidelineFile objects.
        """
        if self._config.guideline_files:
            return [
                GuidelineFile(file=file, content=self._file_loader.load_document(file))
                for file in self._config.guideline_files
            ]
        else:
            supported_files = self._collect_supported_files()
            relevant_files = self._filter_non_relevant_files(supported_files)
            return self._pick_guideline_files_from_content(relevant_files)

    def invoke(self, state: GraphState) -> GraphState:
        """
        Executes the main logic of the Guidelines Retriever Node.

        Retrieves guidelines, prompts for user selection, and updates the state.

        Args:
            state (GraphState): The current state of the execution graph.

        Returns:
            GraphState: The updated state containing the selected guideline files.
        """
        self.logger.info("Retrieving guidelines from the project")
        possible_guideline_files = self._get_guideline_files()
        state["possible_guideline_files"] = possible_guideline_files

        selected_files = self._guidelines_selector.select_guidelines(
            guideline_files=possible_guideline_files
        )
        state["selected_guideline_files"] = selected_files

        return state
