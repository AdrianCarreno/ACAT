import logging
import re
from typing import Sequence
from typing import Set

import boto3
from mypy_boto3_ssm.type_defs import ParameterStringFilterTypeDef

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


def get_ssm_params(path_preffix: str) -> set[str]:
    client = boto3.client("ssm")
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
