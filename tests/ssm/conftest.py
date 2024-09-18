import tempfile
from textwrap import dedent
from typing import Generator

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_ssm import SSMClient

PARAMETERS = {
    "/test1/source/param1": "value1",
    "/test1/source/param2": "value2",
    "/test2/source/param2": "value3",
    "/test2/source/param3": "value3",
}


@pytest.fixture(autouse=True)
def mock_ssm() -> Generator[SSMClient, None, None]:
    with mock_aws():
        client: SSMClient = boto3.client("ssm")

        for name, value in PARAMETERS.items():
            client.put_parameter(Name=name, Value=value, Type="String")

        for i in range(7):
            client.put_parameter(
                Name=f"/test3/source/param{i}", Value=f"value{i}", Type="String"
            )

        yield client


@pytest.fixture
def template_file() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w") as f:
        content = dedent("""\
            AWSTemplateFormatVersion: '2010-09-09'
            Resources:
                S3PermanentBucket:
                    Type: AWS::S3::Bucket
                    Properties:
                    BucketName: !Sub '{{resolve:ssm:/${AWS::StackName}/source/param1}}'
            """)
        f.write(content)
        f.flush()
        yield f.name


@pytest.fixture
def missing_template() -> str:
    return "/tmp/not_found.yaml"


@pytest.fixture
def template_file_invalid_content() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w") as f:
        content = "This is not a valid CloudFormation template"
        f.write(content)
        yield f.name
