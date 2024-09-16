import pytest

from acat.ssm.utils import get_current_params
from acat.ssm.utils import get_ssm_parameter_names


class TestGetCurrentParams:
    def test_success(self, template_file: str, path_preffix="/test1"):
        params = get_current_params(template_file, path_preffix)

        assert len(params) != 0

        for param in params:
            assert param.startswith(path_preffix)

    def test_fail_template_file_invalid_type(self, path_preffix="/test1"):
        with pytest.raises(ValueError) as exc_info:
            get_current_params("wrong_extension.txt", path_preffix)

        assert str(exc_info.value) == "Template file must have .yaml or .yml extension"

    def test_fail_template_file_not_found(
        self, missing_template: str, path_preffix="/test1"
    ):
        with pytest.raises(FileNotFoundError) as exc_info:
            get_current_params(missing_template, path_preffix)

        assert str(exc_info.value) == f"[Errno 2] No such file or directory: '{missing_template}'"  # noqa E501 # fmt: skip

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
        with pytest.raises(TypeError) as exc_info:
            get_ssm_parameter_names()  # type:ignore

        assert str(exc_info.value) == "get_ssm_parameter_names() missing 1 required positional argument: 'path_preffix'"  # noqa E501 # fmt: skip
