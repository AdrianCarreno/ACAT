import json
from typing import Generator

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_stepfunctions import SFNClient

DEFINITION = {
    "Comment": "An example of the Amazon States Language using a choice state.",
    "StartAt": "DefaultState",
    "States": {
        "DefaultState": {
            "Type": "Fail",
            "Error": "DefaultStateError",
            "Cause": "No Matches!",
        }
    },
}
ROLE = "arn:aws:iam::012345678901:role/service-role"


@pytest.fixture
def mock_state_machine() -> Generator[str, None, None]:
    with mock_aws():
        client: SFNClient = boto3.client("stepfunctions")
        sm = client.create_state_machine(
            name="name", definition=json.dumps(DEFINITION), roleArn=ROLE
        )
        for _ in range(10):
            client.start_execution(stateMachineArn=sm["stateMachineArn"])

        yield sm["stateMachineArn"]
