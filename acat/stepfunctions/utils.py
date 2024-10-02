import re
from datetime import UTC
from datetime import datetime
from datetime import timedelta

import boto3
from loguru import logger
from mypy_boto3_stepfunctions import SFNClient
from mypy_boto3_stepfunctions.type_defs import ExecutionListItemTypeDef

from acat.stepfunctions.exceptions import InvalidArnError

MACHINE_ARN_FORMAT = r"^arn:aws:states:(?P<region>[a-z0-9-]+):(?P<account_id>[0-9]+):stateMachine:(?P<name>[a-zA-Z0-9-_]+)$"  # noqa: E501
EXECUTION_ARN_FORMAT = r"^arn:aws:states:(?P<region>[a-z0-9-]+):(?P<account_id>[0-9]+):execution:(?P<name>[a-zA-Z0-9-_]+):(?P<id>[a-f0-9-]+)$"  # noqa: E501


def validate_arn(arn: str):
    if not re.match(MACHINE_ARN_FORMAT, arn):
        raise InvalidArnError(arn)


def parse_datetime(date_time: str) -> datetime:
    logger.info(f"Parsing date time: {date_time}")
    formats = (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%d %H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H",
        "%Y-%m-%d %H",
        "%Y-%m-%d",
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
    )

    for fmt in formats:
        try:
            logger.debug(f"Trying to parse date time with format: {fmt}")
            return datetime.strptime(date_time, fmt)
        except ValueError:
            logger.debug("Could not parse date time with this format")
            pass

    raise ValueError(f"Could not parse date time: {date_time}")


def get_dates(
    start_date: datetime | None = None,
    stop_date: datetime | None = None,
    max_days: int = 14,
) -> tuple[datetime, datetime]:
    logger.debug(f"Getting dates: start={start_date}, stop={stop_date}")
    now = datetime.now(UTC)
    max_age = now - timedelta(days=max_days)

    if not start_date:
        logger.debug(f"Start date not provided, using '{max_age}'")
        start_date = max_age

    if not stop_date:
        logger.debug(f"Stop date not provided, using '{now}'")
        stop_date = now

    if not (max_age <= start_date <= stop_date <= now):
        raise ValueError(
            f"Start and stop dates must be within the last {max_days} days, and"
            " start date must be before stop date"
        )

    return start_date, stop_date


def get_executions(
    arn: str,
    status: str = "FAILED",
    start_date: datetime | None = None,
    stop_date: datetime | None = None,
) -> list[ExecutionListItemTypeDef]:
    """Get a list of failed executions in a Step Functions state machine.

    It returns a list of executions that started between the start and stop
    dates, and have the specified status (default is "FAILED").

    The list is sorted by start date, from the most recent to the oldest. This
    comes from the `client.list_executions` method, which returns the executions
    sorted by start date, and we can stop when we reach the first execution that
    started before the start date.

    Args:
        arn: The ARN of the Step Functions state machine.
        start_date: Optional. The start date of the executions to get. Defaults\
            to 14 days ago.
        stop_date: Optional. The stop date of the executions to get. Defaults\
            to now.

    Returns:
        list[ExecutionListItemTypeDef]: A list of executions.
    """
    logger.info(f"Getting executions for state machine {arn}")
    validate_arn(arn)
    start_date, stop_date = get_dates(start_date, stop_date)
    client: SFNClient = boto3.client("stepfunctions")
    page = 1
    executions: list[ExecutionListItemTypeDef] = []

    while True:
        logger.debug(f"Getting list of executions, page {page:02d}")
        args = {"stateMachineArn": arn, "statusFilter": status}

        if page > 1:
            # If it's not the first page, there is a response and a `NextToken`
            args["NextToken"] = response["NextToken"]  # type: ignore # noqa F821 #pragma: no cover

        response = client.list_executions(**args)  # type: ignore

        for execution in response["executions"]:
            if execution["startDate"] > stop_date:
                # Skip all the executions that started after the stop date
                logger.debug("Skipping execution that started after the stop date")
                continue

            if execution["startDate"] < start_date:
                # Stop when we reach the first execution that started before the
                # start date
                logger.debug(
                    "Reached the first execution that started before the start"
                    f" date ({execution['startDate']})"
                )
                return executions

            executions.append(execution)

        page += 1

        if not response.get("nextToken"):
            break  # pragma: no cover

    return executions
