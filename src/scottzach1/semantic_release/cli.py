import typer

app = typer.Typer()


@app.command()
def deploy():
    """
    Trigger a semantic release with the click of a button

    Set --verbose to enable detailed output.
    """
    typer.echo("Hello world!")


if __name__ == "__main__":  # pragma: no cover
    app()
