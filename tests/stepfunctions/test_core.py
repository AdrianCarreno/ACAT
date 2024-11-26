from acat.stepfunctions.core import redrive

from ..conftest import BaseTest


class TestRedrive(BaseTest):
    def test_success(self, mock_state_machine):
        result = self.runner.invoke(redrive, [mock_state_machine])

        assert result.exit_code == 0
        assert "Redriving execution" in result.output

    def test_no_executions_to_redrive(self, mock_state_machine):
        # Assuming a way to clear executions for this test
        result = self.runner.invoke(redrive, [mock_state_machine])

        assert result.exit_code == 0
        assert "No redrivable executions found" in result.output

    def test_invalid_arn(self, arn="invalid-arn"):
        result = self.runner.invoke(redrive, [arn])

        assert result.exit_code == 1
        assert str(result.exception) == f"Invalid ARN: {arn}"

    def test_redrive_with_batch_size_and_sleep_time(self, mock_state_machine):
        result = self.runner.invoke(redrive, [mock_state_machine, "-n", "2", "-t", "1"])

        assert result.exit_code == 0
        assert "Sleeping for 1 seconds..." in result.output

    def test_redrive_with_start_and_stop_dates(self, mock_state_machine):
        result = self.runner.invoke(
            redrive,
            [
                mock_state_machine,
                "--start-date",
                "2023-01-01 00:00:00",
                "--stop-date",
                "2023-01-02 00:00:00",
            ],
        )

        assert result.exit_code == 0
        assert "Redriving execution" in result.output
