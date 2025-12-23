# Setup Agent

AI Agent responsible for installing all the necessary tools and dependencies and running the app, built with Python and LangGraph.

## Getting started

### Development environment

1. Install `uv` according to the [Astral docs](https://docs.astral.sh/uv/getting-started/installation/)
2. In your terminal run the following commands:

```bash
uv sync # install all dependencies
uv run pre-commit install # install pre-commit hooks
```

For the testing purposes, run:

```bash
source .venv/bin/activate
python src/cli/app.py setup run
```

### CLI

In order to install the CLI globally, use provided installation scripts:

```bash
uv build # or ./scripts/build.sh
./scripts/install.sh
```

Then you can use the tool globally by running:

```bash
setup-agent setup run
```

In order to uninstall the tool globally:

```bash
./scripts/uninstall.sh
```

## Usage

### Environment variables

To make the tool working you will need 2 API keys:

- `TAVILY_API_KEY` - key for [Tavily](https://www.tavily.com/) (web search layer for agents)
- an API key for your LLM provider, e.g `OPENAI_API_KEY` for `OpenAI` models (i.e. `gpt-4o`) or `ANTHROPIC_API_KEY` for `Anthropic` models (i.e. `claude-sonnet-4-5`). For full list of possible integrations, please check out [these Langchain docs](https://python.langchain.com/docs/integrations/chat/) (and make sure to install langchain package for given provider using `uv` if you're using provider other than `OpenAI` or `Anthropic`).

The easiest way to use the tool is to add these 2 API keys to the `.env` file located where the `cli` is used:

```sh
# .env
TAVILY_API_KEY=...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
```

For extended debugging and tool usage metrics, please consider adding these Langsmith related variables:

```sh
# .env
LANGSMITH_TRACING=...
LANGSMITH_ENDPOINT=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=...
```

### Configuration options

The CLI runs an interactive script that allows user to configure everything and define the problem:

| Option            | Type      | Description                                                                                                                                                                | Default                       | Required |
| ----------------- | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | -------- |
| `Project root`    | str       | Path to the root of the project (needs to be a valid directory)                                                                                                            | Current directory             | Yes      |
| `Guideline files` | List[str] | Optional list of guideline files. If no guidelines files are specified at this point, agent will suggest all relevant files to the user.                                   | -                             | No       |
| `Task`            | str       | Predefined goal to achieve by the agent. If `task` is not defined, agent will suggest some tasks to the user.                                                              | -                             | No       |
| `Model`           | str       | LLM model to be used as a core reasoning model. For a full list of available models check out [these Langchain docs](https://python.langchain.com/docs/integrations/chat/) | `anthropic:claude-sonnet-4-5` | No       |

The script allows for optional, extended model configuration as well:

| Option              | Type  | Description                                                                | Default               | Required |
| ------------------- | ----- | -------------------------------------------------------------------------- | --------------------- | -------- |
| `Temperature`       | float | Controls randomness of the model. Must be a number between `0.0` and `1.0` | Model's default value | No       |
| `Max output tokens` | int   | Max output tokens of the model.                                            | Model's default value | No       |
| `Timeout`           | int   | Timeout for LLM calls in seconds.                                          | Model's default value | No       |
| `Max retries`       | int   | Max number of retries for LLM calls.                                       | Model's default value | No       |
