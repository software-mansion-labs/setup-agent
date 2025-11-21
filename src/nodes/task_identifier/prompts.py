from enum import Enum


class TaskIdentifierPrompts(str, Enum):
    IDENTIFY_TASKS = """
        You are given documentation (README, setup guide, or contributor guide)
        for a project that has ALREADY BEEN CLONED locally.

        Identify the distinct, **high-level workflows** that a developer or user
        can perform with the project.

        Each task should describe a complete, meaningful goal — 
        typically combining installation, configuration, and execution steps 
        into a single coherent task.

        Be specific about the platforms if applicable (e.g. IOS, Android, Web, Desktop).

        ✅ Examples of acceptable high-level tasks:
        - install dependencies and run the web application in development mode
        - install dependencies and run the backend server
        - install dependencies and run automated tests
        - install dependencies and run the app on Android physical device
        - install dependencies and run the app on iOS simulator
        - build and run the production version of the app
        - generate documentation locally

        🚫 DO NOT include:
        - cloning repositories, creating branches, or making PRs
        - code style or administrative docs
        - individual low-level commands (e.g., “run npm install”)
        - deployment or CI/CD tasks
        - documentation-only activities

        Abstract away tool-specific names — for example:
        - “run the app with npm” → “run the web application in development mode”
        - “pip install -r requirements.txt” → “install project dependencies”

        Return JSON strictly in this format:
        {{ "tasks": [ "task 1", "task 2", ... ] }}
    """
