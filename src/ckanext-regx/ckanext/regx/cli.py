import click


@click.group(short_help="regx CLI.")
def regx():
    """regx CLI.
    """
    pass


@regx.command()
@click.argument("name", default="regx")
def command(name):
    """Docs.
    """
    click.echo("Hello, {name}!".format(name=name))


def get_commands():
    return [regx]
