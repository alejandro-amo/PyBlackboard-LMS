import unittest
import csv
from io import StringIO
import inspect
import tempfile
from unittest.mock import patch
from pathlib import Path

from blackboard_api.facades.courses import CourseFacade
from blackboard_api.facades.enrollments import EnrollmentFacade
from blackboard_api.facades.resources import EnrollmentRoleFacade, NodeFacade
from blackboard_api.facades.api_quota import ApiQuotaFacade
from blackboard_api.facades.terms import TermFacade
from blackboard_api.facades.users import UserFacade
from blackboard_cli.cli import (
    COMMANDS,
    _write_result,
    build_parser,
    format_api_quota,
    main,
)
from blackboard_cli.encoding import force_utf8_standard_streams


class CliTests(unittest.TestCase):
    def test_standard_streams_are_forced_to_utf8_when_supported(self):
        stdout = unittest.mock.Mock()
        stderr = unittest.mock.Mock()
        with patch("blackboard_cli.encoding.sys.stdout", stdout), patch(
            "blackboard_cli.encoding.sys.stderr", stderr
        ):
            force_utf8_standard_streams()
        stdout.reconfigure.assert_called_once_with(encoding="utf-8")
        stderr.reconfigure.assert_called_once_with(encoding="utf-8")

    def test_standard_streams_without_reconfigure_are_supported(self):
        with patch("blackboard_cli.encoding.sys.stdout", StringIO()), patch(
            "blackboard_cli.encoding.sys.stderr", StringIO()
        ):
            force_utf8_standard_streams()

    def test_api_quota_is_formatted_as_remaining_over_daily_maximum(self):
        self.assertEqual(
            format_api_quota(
                {"remaining": 1234, "max_requests_per_day": 10000}
            ),
            "1234/10000",
        )

    def test_unknown_api_quota_values_are_explicit(self):
        self.assertEqual(
            format_api_quota(
                {"remaining": None, "max_requests_per_day": None}
            ),
            "?/?",
        )

    def test_check_api_quota_writes_compact_quota_to_standard_output(self):
        class ApiQuota:
            def get(self):
                return {"remaining": 1234, "max_requests_per_day": 10000}

        class Client:
            enable_write = False
            api_quota = ApiQuota()

        with patch("blackboard_cli.cli.create_client", return_value=Client()):
            with patch("builtins.print") as output:
                self.assertEqual(
                    main(["--env-file", "config.env", "check-api-quota"]),
                    0,
                )
        output.assert_called_once_with("1234/10000")

    def test_env_file_is_required(self):
        parser = build_parser()
        args = parser.parse_args([])
        self.assertIsNone(args.command)

    def test_global_options_precede_command(self):
        parser = build_parser()
        args = parser.parse_args(["--env-file", "config.env", "list-courses"])
        self.assertEqual(args.command, "list-courses")

    def test_command_help_can_be_requested_without_a_command(self):
        args = build_parser().parse_args(["--command-help"])
        self.assertTrue(args.command_help)

    def test_help_usage_documents_global_and_command_options(self):
        self.assertEqual(
            build_parser().usage,
            "blackboard [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]",
        )

    def test_general_help_uses_global_options_label_without_positional_section(self):
        help_text = build_parser().format_help()
        self.assertIn("global options:", help_text)
        self.assertNotIn("positional arguments:", help_text)
        self.assertNotIn("COMMAND\n", help_text)

    def test_cli_covers_all_public_facade_methods_except_iterators(self):
        facade_methods = {
            "courses": CourseFacade,
            "users": UserFacade,
            "nodes": NodeFacade,
            "enrollments": EnrollmentFacade,
            "terms": TermFacade,
            "enrollment_roles": EnrollmentRoleFacade,
            "api_quota": ApiQuotaFacade,
        }
        for resource, facade in facade_methods.items():
            public_methods = {
                name for name, method in inspect.getmembers(facade, callable)
                if not name.startswith("_") and not name.startswith("iter")
            }
            cli_methods = {
                operation for command, (item, operation) in COMMANDS.items()
                if item == resource
            }
            self.assertEqual(public_methods, cli_methods, resource)

    def test_csv_can_be_written_to_standard_output(self):
        stream = StringIO()
        with patch("sys.stdout", stream):
            _write_result([{"id": "1", "name": "Role"}], "csv", None)
        parsed = list(csv.DictReader(StringIO(stream.getvalue())))
        self.assertEqual(parsed, [{"id": "1", "name": "Role"}])

    def test_tabular_output_can_exclude_copy_history(self):
        stream = StringIO()
        with patch("sys.stdout", stream):
            _write_result(
                [{"id": "1", "copyHistory": [{"uuid": "history"}]}],
                "csv",
                None,
                excluded_fields=("copyHistory",),
            )
        parsed = list(csv.DictReader(StringIO(stream.getvalue())))
        self.assertEqual(parsed, [{"id": "1"}])

    def test_excel_requires_output_file(self):
        with self.assertRaisesRegex(ValueError, "output is required"):
            _write_result([{"id": "1"}], "excel", None)

    def test_output_rejects_existing_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "result.json"
            destination.write_text("existing", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "already exists"):
                _write_result({"id": "1"}, "json", str(destination))

    def test_output_rejects_missing_parent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "missing" / "result.json"
            with self.assertRaisesRegex(ValueError, "does not exist"):
                _write_result({"id": "1"}, "json", str(destination))

    def test_cli_configuration_options_are_parsed(self):
        args = build_parser().parse_args([
            "--env-file", "config.env",
            "--enable-write",
            "--log-level", "INFO",
            "--max-retries", "5",
            "list-courses",
            "--format", "json",
            "--output", "result.json",
        ])
        self.assertEqual(args.env_file, "config.env")
        self.assertTrue(args.enable_write)
        self.assertEqual(args.log_level, "INFO")
        self.assertEqual(args.format, "json")
        self.assertEqual(args.output, "result.json")
        self.assertEqual(args.max_retries, 5)

    def test_enable_write_constructs_a_writable_client(self):
        args = build_parser().parse_args([
            "--env-file", "config.env",
            "--enable-write",
            "list-courses",
        ])
        with patch("blackboard_cli.cli.BlackboardAPI") as api_class:
            from blackboard_cli.cli import create_client

            create_client(args)
        api_class.assert_called_once_with(
            env_file="config.env",
            enable_write=True,
            max_retries=None,
        )

    def test_output_options_are_only_available_for_get_and_list_commands(self):
        parser = build_parser()
        parser.parse_args(["list-courses", "--format", "csv"])
        with self.assertRaises(SystemExit):
            parser.parse_args(["create-course", "--format", "json"])

    def test_create_commands_reject_generated_identifier_fields(self):
        parser = build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([
                "create-course", "--field", "id=_1_1",
            ])

    def test_command_help_explains_generated_create_fields(self):
        from blackboard_cli.cli import command_help_text

        help_text = command_help_text()
        self.assertIn("specify once for each field", help_text)
        self.assertIn("Blackboard-generated top-level fields id or uuid", help_text)
        self.assertIn("required courseId and name", help_text)
        self.assertNotIn(
            "create-course: creates a course\n"
            "    Command options: repeated --field NAME=VALUE options\n"
            "      --field: Resource field. Do not supply the "
            "Blackboard-generated top-level fields id or uuid.\n"
            "      --course-identifier",
            help_text,
        )

    def test_command_help_lists_output_options_for_collection_commands(self):
        from blackboard_cli.cli import command_help_text

        help_text = command_help_text()
        list_courses = help_text.split("  get-course:", maxsplit=1)[0]
        self.assertIn("--format: Output format", list_courses)
        self.assertIn("--output: Output file path", list_courses)
        self.assertIn("    Command options:\n", list_courses)
        self.assertNotIn("Command options: none", help_text)

    def test_log_level_is_case_insensitive(self):
        args = build_parser().parse_args([
            "--env-file", "config.env",
            "--log-level", "dEbUg",
            "list-courses",
        ])

        self.assertEqual(args.log_level, "DEBUG")


if __name__ == "__main__":
    unittest.main()
