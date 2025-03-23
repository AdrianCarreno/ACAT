import concurrent.futures
import re
from typing import Sequence
from typing import Set

import boto3
import click
from mypy_boto3_ssm import SSMClient
from mypy_boto3_ssm.type_defs import ParameterStringFilterTypeDef

from acat.logger import logger
from acat.ssm.types import Parameter

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
    logger.info(f"Getting SSM parameter names with path preffix: {path_preffix}")
    client: SSMClient = boto3.client("ssm")
    parameter_filters: Sequence[ParameterStringFilterTypeDef] = [
        {"Key": "Name", "Option": "BeginsWith", "Values": [path_preffix]}
    ]
    i = 1
    parameters: set[str] = set()

    while True:
        logger.debug(f"Getting parameters page {i:02d}")
        args = {
            "MaxResults": 50,  # AWS maximum allowed value
            "ParameterFilters": parameter_filters,
        }

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
    parameter_names = get_ssm_parameter_names(path_preffix)
    parameters: list[Parameter] = []

    def fetch_parameter(name: str) -> Parameter | None:
        try:
            full_param = client.get_parameter(Name=name)["Parameter"]
            if (
                "Name" not in full_param
                or "Value" not in full_param
                or "Type" not in full_param
            ):  # pragma: no cover
                logger.warning(
                    f"Parameter {full_param} does not have all required fields"
                )
                return None
            parameter: Parameter = {
                "Name": full_param["Name"],
                "Value": full_param["Value"],
                "Type": full_param["Type"],
            }
            return parameter
        except Exception as e:  # pragma: no cover
            logger.error(f"Error fetching parameter {name}: {e}")
            return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_parameter, name) for name in parameter_names]

        for future in concurrent.futures.as_completed(futures):
            parameter = future.result()

            if parameter:
                parameters.append(parameter)

    return parameters


def create_ssm_parameters(parameters: Sequence[Parameter], overwrite: bool) -> None:
    """Create SSM parameters in parallel."""
    client = boto3.client("ssm")

    def create_parameter(parameter: Parameter, overwrite: bool):
        try:
            click.echo(f"Creating parameter: {parameter['Name']}")
            client.put_parameter(Overwrite=overwrite, **parameter)
        except Exception as e:  # pragma: no cover
            click.echo(f"Error creating parameter {parameter['Name']}: {e}")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(create_parameter, parameter, overwrite)
            for parameter in parameters
        ]
        for future in concurrent.futures.as_completed(futures):
            # Raise any exceptions that occurred during parameter creation
            future.result()
