import click

from acat.ssm.core import ssm


@click.group()
def cli():
    """Adrian Carreno's AWS Toolkit.

    This is a collection of tools that I use to manage my AWS resources.
    """
    pass


cli.add_command(ssm)
