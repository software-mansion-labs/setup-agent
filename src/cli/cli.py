import typer
from  cli.scripts import setup

app = typer.Typer(help="My multi-command CLI tool")

app.add_typer(setup.app, name="installation_script")

if __name__ == "__main__":
    app()
