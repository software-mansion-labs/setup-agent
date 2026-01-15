from typing import List, Literal

from questionary import Choice, checkbox, path

from graph_state import GuidelineFile
from utils.file_loader import FileLoader


class GuidelinesSelector:
    """
    Handles interactive selection of guideline files from a list of available options.

    Allows users to select from pre-discovered guideline files or manually enter
    custom file paths through a checkbox interface.
    """

    def __init__(self, file_loader: FileLoader) -> None:
        """
        Initialize the guidelines selector.

        Args:
            file_loader: FileLoader instance used to load document content from disk.
        """
        self._file_loader = file_loader

    def select_guidelines(
        self,
        guideline_files: List[GuidelineFile],
        default_files: List[GuidelineFile] = [],
    ) -> List[GuidelineFile]:
        """
        Interactively prompts the user to select guideline files via checkbox interface.

        Presents a sorted list of available guideline files with the option to manually
        enter additional file paths. Files can be pre-selected by providing default_files.

        Args:
            guideline_files (List[GuidelineFile]): List of GuidelineFile objects with content already loaded.
            default_files (List[GuidelineFile]): List of GuidelineFile objects to pre-select in the checkbox.
                          If empty, the first file in the sorted list is selected by default. Defaults to empty list.

        Returns:
            List[GuidelineFile]: Selected guideline files with their content loaded.
                                Returns empty list if no guideline files are available.
        """
        if not guideline_files:
            return []

        sorted_guideline_files = sorted(
            guideline_files, key=lambda f: len(f.file.split("/"))
        )
        default_file_paths = (
            [gf.file for gf in default_files]
            if default_files
            else [sorted_guideline_files[0].file]
        )

        OTHER_OPTION = "Other: (Enter manual path)"

        choices = [
            Choice(title=gf.file, value=gf.file, checked=gf.file in default_file_paths)
            for gf in sorted_guideline_files
        ]
        choices.append(Choice(title=OTHER_OPTION, value=OTHER_OPTION, checked=False))

        selected_files: List[str] = checkbox(
            message="Select guideline files to use",
            choices=choices,
            validate=self._validate_checkbox_selection,
        ).unsafe_ask()

        manual_paths = []
        if OTHER_OPTION in selected_files:
            selected_files.remove(OTHER_OPTION)
            self._handle_manual_entry(selected_files, manual_paths)

        final_selection = [gf for gf in guideline_files if gf.file in selected_files]

        for manual_path in manual_paths:
            if any(gf.file == manual_path for gf in final_selection):
                continue
            content = self._file_loader.load_document(manual_path)
            if content:
                final_selection.append(GuidelineFile(file=manual_path, content=content))

        return final_selection

    def _handle_manual_entry(
        self, selected_files: List[str], manual_files: List[str]
    ) -> None:
        """
        Handles the interactive loop for manually entering custom file paths.

        Continuously prompts the user to enter file paths until they press Enter
        without input to finish. All entered paths are added to the manual_files list.

        Args:
            selected_files (List[str]): List of files already selected from the checkbox.
            manual_files (List[str]): List that will be populated with manually entered file paths.
        """
        while True:
            custom_path = path(
                message="Please enter the file path (or press Enter to finish):",
                validate=lambda p: self._validate_custom_path(
                    selected_files, manual_files, p
                ),
            ).unsafe_ask()

            if not custom_path or not custom_path.strip():
                break

            manual_files.append(custom_path.strip())

    def _validate_checkbox_selection(self, choices: List[str]) -> Literal[True] | str:
        """
        Validates that at least one option is selected in the checkbox.

        Args:
            choices (List[str]): List of selected choices from the checkbox.

        Returns:
            Literal[True] | str: True if valid (at least one option selected), error message otherwise.
        """
        if len(choices) > 0:
            return True
        return "You must choose at least one option."

    def _validate_custom_path(
        self, selected_files: List[str], manual_files: List[str], path: str
    ) -> Literal[True] | str:
        """
        Validates custom path input during manual entry.

        Ensures that at least one file is selected either from the checkbox,
        previously entered manual paths, or the current input.

        Args:
            selected_files (List[str]): List of files already selected from the checkbox.
            manual_files (List[str]): List of files already manually entered.
            path (str): The current path input to validate.

        Returns:
            Literal[True] | str: True if valid (at least one file is selected/entered), error message otherwise.
        """
        if len(selected_files) > 0 or len(manual_files) > 0:
            return True
        if len(path.strip()) > 0:
            return True
        return "You must choose at least one valid file."
