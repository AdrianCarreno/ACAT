import click

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
    "--number",
    "-n",
    help="Number of failed executions to redrive at once",
    type=int,
    default=10,
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
    number: int,
    start_date: str | None,
    stop_date: str | None,
) -> None:
    """Redrive failed executions in an AWS Step Functions state machine."""
    if not validate_arn(arn):
        raise click.UsageError("Invalid ARN")

    start = parse_datetime(start_date) if start_date else None
    stop = parse_datetime(stop_date) if stop_date else None
    executions = get_executions(arn, start_date=start, stop_date=stop)

    click.echo(f"Found {len(executions)} executions")
