import re
import threading

import boto3
import click
import pytest

from acat.ssm.types import Parameter
from acat.ssm.utils import create_ssm_parameters
from acat.ssm.utils import get_current_params
from acat.ssm.utils import get_ssm_parameter_names
from acat.ssm.utils import get_ssm_parameters


class TestGetCurrentParams:
    def test_success(self, template_file: str, path_preffix="/test1"):
        params = get_current_params(template_file, path_preffix)

        assert len(params) != 0

        for param in params:
            assert param.startswith(path_preffix)

    def test_fail_template_file_invalid_type(self, path_preffix="/test1"):
        with pytest.raises(
            ValueError,
            match=re.escape("Template file must have .yaml or .yml extension"),
        ):
            get_current_params("wrong_extension.txt", path_preffix)

    def test_fail_template_file_not_found(
        self, missing_template: str, path_preffix="/test1"
    ):
        with pytest.raises(
            FileNotFoundError,
            match=re.escape(
                f"[Errno 2] No such file or directory: '{missing_template}'"
            ),
        ):
            get_current_params(missing_template, path_preffix)

    def test_fail_template_file_invalid_content(
        self, template_file_invalid_content: str, path_preffix="/test1"
    ):
        params = get_current_params(template_file_invalid_content, path_preffix)

        assert params == set()


class TestGetSsmParameterNames:
    def test_success(self, path_preffix="/test2"):
        names = get_ssm_parameter_names(path_preffix)

        assert len(names) != 0

        for name in names:
            assert name.startswith(path_preffix)

    def test_success_no_parameters(self, path_preffix="/no_path"):
        names = get_ssm_parameter_names(path_preffix)

        assert len(names) == 0

    def test_fail_without_path_preffix(self):
        with pytest.raises(
            TypeError,
            match=re.escape(
                "get_ssm_parameter_names() missing 1 required positional argument: 'path_preffix'"  # noqa E501
            ),
        ):
            get_ssm_parameter_names()  # type:ignore


class TestGetSsmParameters:
    def test_success(self, path_preffix="/test3"):
        params = get_ssm_parameters(path_preffix)

        assert len(params) != 0

        for param in params:
            assert param["Name"].startswith(path_preffix)

    def test_success_no_parameters(self, path_preffix="/no_path"):
        params = get_ssm_parameters(path_preffix)

        assert len(params) == 0

    def test_fail_without_path_preffix(self):
        with pytest.raises(
            TypeError,
            match=re.escape(
                "get_ssm_parameters() missing 1 required positional argument: 'path_preffix'"  # noqa E501
            ),
        ):
            get_ssm_parameters()  # type:ignore


# Fake SSM client for testing
class FakeSSMClient:
    def __init__(self, raise_error=False):
        self.put_param_calls = []
        self.raise_error = raise_error
        self.lock = threading.Lock()

    def put_parameter(self, Overwrite, **parameter):
        with self.lock:
            if self.raise_error:
                raise Exception("test error")
            self.put_param_calls.append((Overwrite, parameter))


@pytest.fixture()
def fake_ssm_client(monkeypatch):
    # This fixture allows tests to override the fake client behavior.
    client_instance = FakeSSMClient()

    def fake_client(service_name, *args, **kwargs):
        if service_name == "ssm":
            return client_instance
        return boto3.client(service_name, *args, **kwargs)

    monkeypatch.setattr(boto3, "client", fake_client)
    return client_instance


@pytest.fixture
def captured_click_echo(monkeypatch):
    messages = []

    def fake_echo(message):
        messages.append(message)

    monkeypatch.setattr(click, "echo", fake_echo)
    return messages


def test_create_ssm_parameters_success(fake_ssm_client, captured_click_echo):
    # create some fake parameters
    parameters = [
        Parameter(Name="/test/param1", Value="foo", Type="String"),
        Parameter(Name="/test/param2", Value="bar", Type="String"),
    ]
    overwrite = True

    create_ssm_parameters(parameters, overwrite)

    # check that for each parameter, put_parameter was called and the echo message was printed
    assert len(fake_ssm_client.put_param_calls) == len(parameters)

    for call in fake_ssm_client.put_param_calls:
        call_overwrite, call_param = call
        assert call_overwrite is overwrite
        # Check parameter dict contains proper keys
        assert "Name" in call_param
        assert "Value" in call_param
        assert "Type" in call_param

    # Check that each parameter creation was echoed
    for param in parameters:
        expected_message = f"Creating parameter: {param['Name']}"
        assert expected_message in captured_click_echo


def test_create_ssm_parameters_failure(monkeypatch, captured_click_echo):
    # Set up a fake client which raises an error
    fake_client = FakeSSMClient(raise_error=True)

    def fake_ssm_client(service_name, *args, **kwargs):
        if service_name == "ssm":
            return fake_client
        return boto3.client(service_name, *args, **kwargs)

    monkeypatch.setattr(boto3, "client", fake_ssm_client)

    parameters = [Parameter(Name="/test/param_error", Value="fail", Type="String")]
    overwrite = False

    # Should not raise despite failures; error messages should be echoed.
    create_ssm_parameters(parameters, overwrite)

    # In this case, since exception is caught, put_param_calls remains empty.
    assert len(fake_client.put_param_calls) == 0

    # Check that an error message was echoed
    assert (
        "Error creating parameter /test/param_error: test error" in captured_click_echo
    )
