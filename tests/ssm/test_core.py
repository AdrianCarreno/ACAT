from acat.ssm.core import copy
from acat.ssm.core import delete_unused
from acat.ssm.utils import get_ssm_parameter_names

from ..conftest import BaseTest


class TestDeleteUnused(BaseTest):
    def test_success(self, template_file: str, path_prefix="/test1"):
        params_before = get_ssm_parameter_names("/")  # All parameters
        result = self.runner.invoke(
            delete_unused, [path_prefix, "-t", template_file], input="y\n"
        )
        params_after = get_ssm_parameter_names("/")

        assert result.exit_code == 0
        assert params_after < params_before

    def test_success_no_parameters_to_delete(self, template_file: str):
        result = self.runner.invoke(
            delete_unused, ["/no-path", "-t", template_file], input="y\n"
        )

        assert result.output == "No parameters to delete\n"

    def test_success_aborted(self, template_file: str):
        result = self.runner.invoke(
            delete_unused, ["/test1", "-t", template_file], input="n\n"
        )

        assert result.exit_code == 1
        assert "Aborted" in result.output

    def test_fail_without_providing_path_preffix(self):
        result = self.runner.invoke(delete_unused, ["-t", "template.yaml"])

        assert result.exit_code == 2
        assert "Error: Missing argument 'PATH_PREFFIX'." in result.output

    def test_fail_template_file_not_found(self):
        result = self.runner.invoke(delete_unused, ["/test1", "-t", "invalid.yaml"])

        assert result.exit_code == 1
        assert (
            str(result.exception)
            == "[Errno 2] No such file or directory: 'invalid.yaml'"
        )

    def test_fail_template_file_invalid_type(self):
        result = self.runner.invoke(delete_unused, ["/test1", "-t", "invalid.txt"])

        assert result.exit_code == 1
        assert (
            str(result.exception) == "Template file must have .yaml or .yml extension"
        )

    def test_fail_template_file_no_parameters(self, template_file_invalid_content: str):
        result = self.runner.invoke(
            delete_unused, ["/test1", "-t", template_file_invalid_content]
        )

        assert result.exit_code == 0
        assert result.output == "No parameters found in the template\n"


class TestCopy(BaseTest):
    def test_success(self, source="/test1", destination="/test2"):
        params_before = get_ssm_parameter_names(destination)
        result = self.runner.invoke(copy, [source, destination], input="y\n")
        params_after = get_ssm_parameter_names(destination)

        assert result.exit_code == 0
        assert "Creating parameter: " in result.output
        assert params_after > params_before

    def test_success_no_parameters_to_copy(self):
        result = self.runner.invoke(copy, ["/no-path", "/test2"], input="y\n")

        assert result.exit_code == 0
        assert "No parameters to copy" in result.output

    def test_success_aborted(self):
        result = self.runner.invoke(copy, ["/test1", "/test2"], input="n\n")

        assert result.exit_code == 1
        assert "Aborted" in result.output

    def test_fail_without_providing_path_preffix(self):
        result = self.runner.invoke(copy, ["/test1"])

        assert result.exit_code == 2
        assert "Error: Missing argument 'DESTINATION'." in result.output
