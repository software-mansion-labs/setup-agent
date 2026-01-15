import typer

from cli.scripts import setup

app = typer.Typer(help="My multi-command CLI tool")

app.add_typer(setup.app, name="setup")

if __name__ == "__main__":
    app()
