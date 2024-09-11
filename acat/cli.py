import os
import sys

import click
from loguru import logger

from acat.ssm.core import ssm

logger.remove()
logger.add(sys.stderr, level=os.getenv("LOGURU_LEVEL", "WARNING"))


@click.group()
def cli():
    """Adrian Carreno's AWS Toolkit.

    This is a collection of tools that I use to manage my AWS resources.

    This applications uses Loguru for logging. To set different debug levels use
    the `LOGURU_LEVEL` environment variable. You can also use any other Loguru
    configuration by setting the `LOGURU_` environment variables.
    """
    pass


cli.add_command(ssm)
