import logging

import boto3
import click

from .types import Parameter
from .utils import get_current_params
from .utils import get_ssm_parameter_names
from .utils import get_ssm_parameters

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
    show_default=True,
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
    ssm_params = get_ssm_parameter_names(path_preffix)
    to_delete = ssm_params - current_params

    if len(to_delete) == 0:
        click.echo("No parameters to delete")
        exit(0)

    click.echo(f"Found {len(to_delete)} parameters to delete:")

    for param in sorted(to_delete):
        click.echo(f"\t{param}")

    proceed = click.prompt(f"Delete {len(to_delete)} parameters? (y/[n])", default="n")

    if proceed.lower() != "y":
        click.echo("Aborted")
        exit(1)

    client = boto3.client("ssm")

    for param in sorted(to_delete):
        click.echo(f"Deleting parameter: {param}")
        client.delete_parameter(Name=param)

    click.echo("Deleted all unused parameters")


@ssm.command()
@click.argument("source")
@click.argument("destination")
@click.option(
    "--overwrite/--no-overwrite",
    default=False,
    show_default=True,
    help="Overwrite existing parameters",
)
def copy(source: str, destination: str, overwrite: bool):
    """Recursively copy all SSM parameters from a path to another path.

    This script will copy all SSM parameters from the source path to the
    destination path. If the destination path already exists, it will be
    overwritten depending on the value of the `overwrite` flag.
    """
    client = boto3.client("ssm")

    source_params = get_ssm_parameters(source)
    dest_param_names = get_ssm_parameter_names(destination)
    new_params: list[Parameter] = []

    for parameter in source_params:
        new_name = parameter["Name"].replace(source, destination)

        if new_name in dest_param_names and not overwrite:
            logger.debug(f"Parameter {new_name} already exists, skipping")
            continue
        new_params.append(
            {"Name": new_name, "Value": parameter["Value"], "Type": parameter["Type"]}
        )

    if len(new_params) == 0:
        click.echo("No parameters to copy")
        exit(0)

    click.echo(f"{len(new_params)} parameters will be created/overwritten:")

    for param in sorted(new_params, key=lambda x: x["Name"]):
        click.echo(f"\t{param['Name']}")

    proceed = click.prompt("Proceed? (y/[n])", default="n")

    if proceed.lower() != "y":
        click.echo("Aborted")
        exit(1)

    for parameter in new_params:
        click.echo(f"Creating parameter: {parameter['Name']}")
        client.put_parameter(Overwrite=overwrite, **parameter)
