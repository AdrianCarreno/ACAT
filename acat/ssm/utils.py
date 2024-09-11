import logging
import re
from typing import Sequence
from typing import Set

import boto3
from mypy_boto3_ssm import SSMClient
from mypy_boto3_ssm.type_defs import ParameterStringFilterTypeDef

from .types import Parameter

MATCH_STR = r"\{\{ ?resolve:ssm:\/\$\{AWS::StackName\}(\/.+) ?\}\+?\}"
logger = logging.getLogger(__name__)


def get_current_params(template_path: str, path_preffix: str) -> Set[str]:
    current_params = set()

    with open(template_path, "r") as f:
        for line in f:
            match = re.search(MATCH_STR, line)
            if match:
                param = f"/{path_preffix.strip('/')}/{match.group(1).strip('/')}"
                current_params.add(param)

    logger.info(f"Found {len(current_params)} current parameters")

    for param in sorted(current_params):
        logger.debug(f"\t{param}")

    return current_params


def get_ssm_parameter_names(path_preffix: str) -> set[str]:
    client: SSMClient = boto3.client("ssm")
    parameters = set()
    parameter_filters: Sequence[ParameterStringFilterTypeDef] = [
        {"Key": "Name", "Option": "BeginsWith", "Values": [path_preffix]}
    ]
    response = client.describe_parameters(ParameterFilters=parameter_filters)

    while "NextToken" in response:
        parameters.update(
            {param["Name"] for param in response["Parameters"] if "Name" in param}
        )
        response = client.describe_parameters(
            ParameterFilters=parameter_filters, NextToken=response["NextToken"]
        )

    return parameters


def get_ssm_parameters(path_preffix: str) -> list[Parameter]:
    client: SSMClient = boto3.client("ssm")
    parameter_filters: Sequence[ParameterStringFilterTypeDef] = [
        {"Key": "Name", "Option": "BeginsWith", "Values": [path_preffix]}
    ]
    response = client.describe_parameters(ParameterFilters=parameter_filters)
    parameters: list[Parameter] = []

    while "NextToken" in response:
        for param in response["Parameters"]:
            if "Name" not in param:
                logger.warning(f"Parameter {param} does not have a name")
                continue

            full_param = client.get_parameter(Name=param["Name"])["Parameter"]
            if (
                "Name" not in full_param
                or "Value" not in full_param
                or "Type" not in full_param
            ):
                logger.warning(
                    f"Parameter {full_param} does not have all required fields"
                )
                continue
            parameters.append(
                {
                    "Name": full_param["Name"],
                    "Value": full_param["Value"],
                    "Type": full_param["Type"],
                }
            )
        response = client.describe_parameters(
            ParameterFilters=parameter_filters, NextToken=response["NextToken"]
        )

    return parameters
