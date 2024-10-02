import re
import time

import boto3
import click
from loguru import logger
from mypy_boto3_stepfunctions import SFNClient

from .utils import EXECUTION_ARN_FORMAT
from .utils import get_executions
from .utils import parse_datetime
from .utils import validate_arn


@click.group()
def step_functions():  # pragma: nocover
    """Manage Step Functions"""
    pass


@step_functions.command()
@click.argument("arn", type=str)
@click.option(
    "--sleep-time",
    "-t",
    help="Sleep time in seconds between each redrive attempt",
    type=int,
    default=60,
    show_default=True,
)
@click.option(
    "--batch-size",
    "-n",
    help="Number of failed executions to redrive at once. 0 to disable",
    type=int,
    default=0,
    show_default=True,
)
@click.option(
    "--start-date",
    help=(
        "The start date (and time) of the execution to redrive. Format: "
        "YYYY-MM-DD HH:MM:SS"
    ),
    type=str,
)
@click.option(
    "--stop-date",
    help=(
        "The end date (and time) of the execution to redrive. Format: "
        "YYYY-MM-DD HH:MM:SS"
    ),
    type=str,
)
def redrive(
    arn: str,
    sleep_time: int,
    batch_size: int,
    start_date: str | None,
    stop_date: str | None,
) -> None:
    """Redrive failed executions in an AWS Step Functions state machine."""
    validate_arn(arn)
    start = parse_datetime(start_date) if start_date else None
    stop = parse_datetime(stop_date) if stop_date else None
    executions = get_executions(arn, start_date=start, stop_date=stop)

    if not executions:
        click.echo(
            "No redrivable executions found. Executions must be in a failed "
            "state and no older than 14 days."
        )
        exit(0)

    client: SFNClient = boto3.client("stepfunctions")

    for n, execution in enumerate(executions):
        if batch_size != 0 and n + 1 % batch_size == 0:
            click.echo(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
        arn = execution["executionArn"]
        arn_match = re.match(EXECUTION_ARN_FORMAT, arn)

        if not arn_match:
            logger.error(f"Could not parse ARN: {arn}")
            exec_id = "N/A"
        else:
            exec_id = arn_match.group("id")

        click.echo(f"Redriving execution {exec_id}")
        client.redrive_execution(executionArn=arn)
