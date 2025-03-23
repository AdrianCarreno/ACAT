import re

import pytest

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
