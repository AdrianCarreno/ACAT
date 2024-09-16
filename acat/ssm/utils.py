import re
from typing import Sequence
from typing import Set

import boto3
from loguru import logger
from mypy_boto3_ssm import SSMClient
from mypy_boto3_ssm.type_defs import ParameterStringFilterTypeDef

from .types import Parameter

MATCH_STR = r"\{\{ ?resolve:ssm:\/\$\{AWS::StackName\}(\/.+) ?\}\+?\}"


def get_current_params(template_path: str, path_preffix: str) -> Set[str]:
    logger.info(f"Reading SSM parameters used in template file: {template_path}")

    if not re.search(r"\.ya?ml$", template_path):
        raise ValueError("Template file must have .yaml or .yml extension")

    logger.debug(f"Path preffix: {path_preffix}")
    logger.debug(f"Match string: {MATCH_STR}")
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
    logger.info(f"Getting SSM parameters with path preffix: {path_preffix}")
    client: SSMClient = boto3.client("ssm")
    parameter_filters: Sequence[ParameterStringFilterTypeDef] = [
        {"Key": "Name", "Option": "BeginsWith", "Values": [path_preffix]}
    ]
    i = 1
    parameters: set[str] = set()

    while True:
        logger.debug(f"Getting parameters page {i:02d}")
        args = {"ParameterFilters": parameter_filters}

        if i > 1:
            # If it's not the first page, there is a response and a `NextToken`
            args["NextToken"] = response["NextToken"]  # type: ignore # noqa F821

        response = client.describe_parameters(**args)  # type: ignore
        parameters.update({param.get("Name", "") for param in response["Parameters"]})
        i += 1

        if "NextToken" not in response:
            break

    return parameters


def get_ssm_parameters(path_preffix: str) -> list[Parameter]:
    logger.info(f"Getting SSM parameters with path preffix: {path_preffix}")
    client: SSMClient = boto3.client("ssm")
    parameter_filters: Sequence[ParameterStringFilterTypeDef] = [
        {"Key": "Name", "Option": "BeginsWith", "Values": [path_preffix]}
    ]
    response = client.describe_parameters(ParameterFilters=parameter_filters)
    parameters: list[Parameter] = []
    i = 1

    while "NextToken" in response:
        logger.debug(f"Getting parameters page {i:02d}")
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
        i += 1

    return parameters
