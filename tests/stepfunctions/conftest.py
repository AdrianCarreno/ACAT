import boto3
import pytest
from moto import mock_aws
from mypy_boto3_stepfunctions import SFNClient


@pytest.fixture
def mock_step_functions():
    with mock_aws():
        client: SFNClient = boto3.client("stepfunctions")
