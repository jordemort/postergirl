import os

import typer
from pydantic_yaml import to_yaml_file, to_yaml_str  # type:ignore
from rich import print
from typing_extensions import Annotated

import postergirl.paths as paths
from postergirl.app import run as run_postergirl
from postergirl.login import create_app, make_access_token
from postergirl.models import MastodonConfig, PostergirlConfig

app = typer.Typer()


@app.command()
def run():
    run_postergirl()


@app.command()
def debug():
    run_postergirl(debug_mode=True)


@app.command()
def login(
    instance_url: str,
    username: Annotated[str, typer.Option(prompt=True)],
    password: Annotated[str, typer.Option(prompt=True, hide_input=True)],
    quiet: bool = False,
    overwrite: bool = False,
):
    if ("POSTERGIRL_CLIENT_ID" in os.environ) and (
        "POSTERGIRL_CLIENT_SECRET" in os.environ
    ):
        client_id, client_secret = (
            os.environ["POSTERGIRL_CLIENT_ID"],
            os.environ["POSTERGIRL_CLIENT_SECRET"],
        )
    else:
        client_id, client_secret = create_app(instance_url)

    access_token = make_access_token(
        instance_url, client_id, client_secret, username, password
    )

    config = PostergirlConfig(
        mastodon=MastodonConfig(
            instance_url=instance_url,
            client_id=client_id,
            client_secret=client_secret,
            access_token=access_token,
        ),
        feeds=[],
    )

    if not (quiet):
        print(
            "\n[bold blue]=====[bold green]BEGIN MASTODON CONFIG[/bold green]=====[/bold blue]\n"
        )
        print(to_yaml_str(config.mastodon) + "\n")
        print(
            "[bold blue]=====[bold green]END MASTODON CONFIG[/bold green]=====[/bold blue]\n"
        )

    config_path = paths.config_path()
    if config_path.exists():
        if overwrite:
            print(f"[bold red]Overwriting {config_path}![/bold red]")
        else:
            print(f"[bold yellow]Not overwriting {config_path}[/bold yellow]")
            return

    to_yaml_file(config_path, config)
    print(f"Configuration written to {config_path}")
