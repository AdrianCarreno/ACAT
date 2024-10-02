from datetime import UTC
from datetime import datetime
from datetime import timedelta

import pytest

from acat.stepfunctions.exceptions import InvalidArnError
from acat.stepfunctions.utils import get_dates
from acat.stepfunctions.utils import get_executions
from acat.stepfunctions.utils import parse_datetime
from acat.stepfunctions.utils import validate_arn


class TestValidateArn:
    def test_success(self):
        arn = "arn:aws:states:us-west-2:123456789012:stateMachine:my-state-machine"

        assert validate_arn(arn) is None

    def test_failure(self):
        arn = "arn:aws:states:us-west-2:123456789012:stateMachine:my-state-machine:my-execution"  # noqa E501

        with pytest.raises(InvalidArnError) as exc_info:
            validate_arn(arn)

        assert str(exc_info.value) == f"Invalid ARN: {arn}"


class TestParseDatetime:
    def test_success(self):
        date_time = "2021-10-01T12:00:00Z"

        assert isinstance(parse_datetime(date_time), datetime)

    def test_failure(self):
        date_time = "2021-10 12:00:00"

        with pytest.raises(ValueError) as exc_info:
            parse_datetime(date_time)

        assert str(exc_info.value) == f"Could not parse date time: {date_time}"


class TestValidateDates:
    def test_success(self):
        now = datetime.now(UTC)
        start_date = now - timedelta(days=13)
        stop_date = now - timedelta(days=1)

        assert get_dates(start_date, stop_date) == (start_date, stop_date)

    def test_success_no_dates(self):
        now = datetime.now(UTC)
        start_date = now - timedelta(days=14)
        stop_date = now

        automatic_start_date, automatic_stop_date = get_dates()
        assert automatic_start_date < automatic_stop_date
        assert start_date < automatic_start_date
        assert (automatic_start_date - start_date) < timedelta(milliseconds=1)
        assert stop_date < automatic_stop_date
        assert (automatic_stop_date - stop_date) < timedelta(milliseconds=1)

    def test_success_max_days(self, days=15):
        now = datetime.now(UTC)
        start_date = now - timedelta(days=days) + timedelta(seconds=1)
        stop_date = now

        assert get_dates(start_date, stop_date, days) == (start_date, stop_date)

    def test_failure_start_date_too_old(self, days_over=1, max_days=14):
        now = datetime.now(UTC)
        start_date = now - timedelta(days=max_days + days_over)
        stop_date = now - timedelta(days=1)

        with pytest.raises(ValueError) as exc_info:
            get_dates(start_date, stop_date, max_days=max_days)

        assert str(exc_info.value) == (
            f"Start and stop dates must be within the last {max_days} days, and"
            " start date must be before stop date"
        )

    def test_failure_stop_date_too_new(self, max_days=14):
        now = datetime.now(UTC)
        start_date = now - timedelta(days=14)
        stop_date = now + timedelta(days=1)

        with pytest.raises(ValueError) as exc_info:
            get_dates(start_date, stop_date, max_days=max_days)

        assert str(exc_info.value) == (
            f"Start and stop dates must be within the last {max_days} days, and"
            " start date must be before stop date"
        )

    def test_failure_start_date_after_stop_date(self):
        now = datetime.now(UTC)
        start_date = now
        stop_date = now - timedelta(days=1)

        with pytest.raises(ValueError) as exc_info:
            get_dates(start_date, stop_date)

        assert str(exc_info.value) == (
            "Start and stop dates must be within the last 14 days, and"
            " start date must be before stop date"
        )


class TestGetExecutions:
    def test_success(self):
        pass
