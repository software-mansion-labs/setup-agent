from enum import Enum


class GuidelinesRetrieverPrompts(str, Enum):
    FILTER_SUBDIRS = (
        "You are an assistant that identifies which subdirectories likely contain "
        "GUIDELINES on how to INSTALL, SET UP and RUN the application or docs saying how to CONTRIBUTE to the project. "
        "Ignore other docs.\n"
        "Return a JSON object **with this exact key**: `picked_entries`.\n"
        "For example:\n"
        "{{ 'picked_entries': ['docs', 'setup', 'examples'] }}"
    )

    FILTER_FILES = (
        "You are an assistant that identifies which files likely contain "
        "GUIDELINES on how to INSTALL, SET UP and RUN the application or docs saying how to CONTRIBUTE to the project. "
        "Ignore other docs.\n"
        "Return a JSON object **with this exact key**: `picked_entries`.\n"
        "For example:\n"
        "{{ 'picked_entries': ['docs/README.md', 'setup/installation_guide.txt'] }}"
    )

    CHECK_FILE_CONTENT = (
        "You are an assistant that analyzes a single file and decides if it contains "
        "GUIDELINES on how to INSTALL, SET UP and RUN the application or docs saying how to CONTRIBUTE to the project. "
        "Ignore unrelated documentation such as changelogs, API docs, or licenses.\n"
        "Return a JSON object with the keys:\n"
        "- `is_guideline`: true if the file is relevant, false otherwise\n"
        "- `reason`: a brief explanation why the file is considered relevant or not\n"
        "Example:\n"
        "{{ 'is_guideline': true, 'reason': 'Contains installation steps with pip commands' }}"
    )
