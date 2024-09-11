import logging

import boto3
import click

from .utils import get_current_params
from .utils import get_ssm_params

MATCH_STR = r"\{\{ ?resolve:ssm:\/\$\{AWS::StackName\}(\/.+) ?\}\}"

logger = logging.getLogger(__name__)


@click.group()
def ssm():
    """Manage SSM parameters."""
    pass


@ssm.command()
@click.argument("path_preffix")
@click.option(
    "--template-path",
    "-t",
    default="template.yaml",
    help="Path to the CloudFormation or SAM template file",
)
def delete_unused(path_preffix: str, template_path: str):
    """Delete unused SSM parameters.

    This script will read a CloudFormation or SAM template file and find all
    SSM parameters that are being used. It will then compare them with the
    parameters that are present in the SSM parameter store for the current stack
    and delete the ones that are not being used.

    The path_preffix argument is used to filter the parameters that are being
    used by the stack. This is useful when you have multiple stacks using the
    same parameter store and you want to delete only the parameters that are
    being used by a specific stack.
    """
    current_params = get_current_params(template_path, path_preffix)
    ssm_params = get_ssm_params(path_preffix)
    to_delete = ssm_params - current_params

    if len(to_delete) == 0:
        click.echo("No parameters to delete")
        exit(0)

    click.echo(f"Found {len(to_delete)} parameters to delete:")

    for param in sorted(to_delete):
        click.echo(f"\t{param}")

    proceed = click.prompt(f"Delete {len(to_delete)} parameters? (y/[n])", default="n")

    if proceed.lower() == "y":
        client = boto3.client("ssm")

        for param in sorted(to_delete):
            logger.debug(f"Deleting parameter: {param}")
            client.delete_parameter(Name=param)

        click.echo("Deleted all unused parameters")
    else:
        click.echo("Aborted")
