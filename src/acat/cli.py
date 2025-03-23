import click

from acat.logger import logger  # noqa F401
from acat.ssm.core import ssm


@click.group()
def cli():
    """Adrian Carreno's AWS Toolkit.

    This is a collection of tools that I use to manage my AWS resources.

    To enable tab autocompletion, add the following line to your .bashrc or .zshrc:

        eval "$(_ACAT_COMPLETE=source acat)"
    """
    pass


cli.add_command(ssm)
