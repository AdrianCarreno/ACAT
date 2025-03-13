from typing import TypedDict

from mypy_boto3_ssm.literals import ParameterTypeType


class Parameter(TypedDict):
    Name: str
    Value: str
    Type: ParameterTypeType
