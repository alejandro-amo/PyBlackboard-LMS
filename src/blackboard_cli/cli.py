"""CLI parser and entry point.

The CLI mirrors every public facade operation. Iterator methods are the sole
intentional exception because they are intended for direct Python API use.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Sequence

from blackboard_api import BlackboardAPI
from blackboard_api.facades.courses import CourseFacade
from blackboard_api.facades.enrollments import EnrollmentFacade
from blackboard_api.facades.resources import EnrollmentRoleFacade, NodeFacade
from blackboard_api.facades.terms import TermFacade
from blackboard_api.facades.users import UserFacade
from blackboard_cli.converters import objects_to_rows
from blackboard_cli.encoding import force_utf8_standard_streams
from blackboard_cli.output import rows_to_csv, rows_to_excel


LOGGER = logging.getLogger(__name__)

RESOURCE_COMMANDS = {
    "courses": (
        "list", "get", "create", "update", "delete",
        "set_available", "set_unavailable", "set_disabled",
        "assign_node", "unassign_node", "list_by_node",
        "assign_term", "unassign_term", "list_by_term", "get_copy_history",
    ),
    "users": (
        "list", "get", "create", "update", "delete",
        "set_available", "set_unavailable", "set_disabled",
        "assign_node", "unassign_node", "list_by_node",
        "change_username",
    ),
    "nodes": (
        "list", "get", "create", "update", "delete",
        "list_by_course", "list_by_user",
    ),
    "enrollments": (
        "list_by_course", "list_by_user",
        "get", "create", "update", "delete", "find", "upsert",
        "set_available", "set_unavailable", "set_disabled",
        "ensure_enrolled", "change_role", "set_availability", "activate",
        "deactivate", "delete_if_exists", "validate_course_role",
        "list_for_courses", "list_for_users", "enroll_user_in_courses",
        "enroll_users_in_course",
    ),
    "terms": ("list", "get", "create", "update", "delete", "get_by_course"),
    "enrollment_roles": ("list",),
    "api_quota": ("get",),
}

RESOURCE_GROUP_NAMES = {"api_quota": "API usage quota"}


def _command_name(resource: str, operation: str) -> str:
    """Build a user-facing command name from a resource operation."""
    if resource == "api_quota" and operation == "get":
        return "check-api-quota"
    if resource == "courses" and operation == "get_copy_history":
        return "get-course-copy-history"
    operation_parts = operation.split("_")
    resource_name = resource.replace("_", "-")
    if operation_parts[0] in {"list", "iter", "get", "create", "update", "delete"}:
        verb = operation_parts[0]
        suffix = operation_parts[1:]
        noun = resource_name if verb in {"list", "iter"} else resource_name.rstrip("s")
        if suffix[:1] == ["by"]:
            suffix = suffix[1:]
        if suffix[:1] == ["for"]:
            return "-".join([verb, noun, *suffix])
        if suffix:
            return "-".join([verb, noun, "by", *suffix])
        return f"{verb}-{noun}"
    operation_name = "-".join(operation_parts)
    if operation_name in {"change-username"}:
        return operation_name
    if operation_parts[0] in {"assign", "unassign"}:
        return "-".join([*operation_parts, "to", resource_name.rstrip("s")])
    return "-".join([operation_name, resource_name.rstrip("s")])


COMMANDS = {
    _command_name(resource, operation): (resource, operation)
    for resource, operations in RESOURCE_COMMANDS.items()
    for operation in operations
}

MUTATING_OPERATIONS = {
    "create", "update", "delete", "assign_node", "unassign_node",
    "assign_term", "unassign_term", "change_username", "upsert",
    "ensure_enrolled", "change_role", "set_availability", "activate",
    "deactivate", "delete_if_exists", "enroll_user_in_courses",
    "enroll_users_in_course",
    "set_available", "set_unavailable", "set_disabled",
}


def format_api_quota(quota: dict[str, int | None]) -> str:
    """Format API quota as ``remaining/max_requests_per_day`` for output."""
    remaining = "?" if quota["remaining"] is None else str(quota["remaining"])
    maximum = quota["max_requests_per_day"]
    maximum_text = "?" if maximum is None else str(maximum)
    return f"{remaining}/{maximum_text}"


class CommandParser(argparse.ArgumentParser):
    """Argument parser for the global-options-first CLI."""

    def parse_args(self, args=None, namespace=None):
        return super().parse_args(args, namespace)


def build_parser() -> argparse.ArgumentParser:
    """Build the parser without loading configuration or making requests."""
    parser = CommandParser(
        prog="blackboard",
        usage="blackboard [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]",
    )
    parser.epilog = "Use --command-help to view the detailed command list."
    _add_global_options(parser)
    parser.add_argument(
        "--command-help",
        action="store_true",
        help="Show descriptions and arguments for all commands.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers._choices_actions = []
    for command in sorted(COMMANDS):
        command_parser = subparsers.add_parser(
            command,
            usage=f"blackboard [GLOBAL_OPTIONS] {command} [COMMAND_OPTIONS]",
            description=f"Execute the {command} command.",
        )
        _add_command_options(command_parser, command)
    parser._positionals._group_actions = []
    parser._optionals.title = "global options"
    return parser


def _add_global_options(parser: argparse.ArgumentParser) -> None:
    """Add options shared by every command."""
    parser.add_argument("--env-file", help="ENV file with Blackboard credentials and configuration.")
    parser.add_argument(
        "--enable-write",
        action="store_true",
        help="Allow mutating commands for this invocation.",
    )
    parser.add_argument("--log-level", type=str.upper, choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), default="WARNING", help="CLI logging level.")
    parser.add_argument("--max-retries", type=int, default=None, help="Maximum number of retries after the initial attempt.")


def _validate_field_assignment(field: str) -> str:
    """Validate one ``--field NAME=VALUE`` argument before client setup."""
    if "=" not in field:
        raise argparse.ArgumentTypeError("--field values must use NAME=VALUE")
    name, _ = field.split("=", 1)
    if not name:
        raise argparse.ArgumentTypeError("--field names cannot be empty")
    if name in {"id", "uuid"}:
        raise argparse.ArgumentTypeError(
            f"--field {name} is not allowed: Blackboard manages this field"
        )
    return field


COMMAND_ARGUMENTS = {
    "get": ("identifier",),
    "delete": ("identifier",),
    "create": (
        "course_identifier", "user_identifier", "course_role_id",
        "availability", "data_source_id", "child_course_id",
    ),
    "update": (
        "course_identifier", "user_identifier", "course_role_id",
        "availability", "data_source_id", "child_course_id",
    ),
    "get_by_course": ("course_identifier",),
    "get_copy_history": ("course_identifier",),
    "list_by_node": ("node_identifier",),
    "list_by_term": ("term_identifier",),
    "iter_by_node": ("node_identifier",),
    "list_by_course": ("course_identifier",),
    "iter_by_course": ("course_identifier",),
    "list_by_user": ("user_identifier",),
    "iter_by_user": ("user_identifier",),
    "assign_node": ("identifier", "node_identifier", "primary"),
    "unassign_node": ("identifier", "node_identifier"),
    "assign_term": ("course_identifier", "term_identifier"),
    "unassign_term": ("course_identifier",),
    "change_username": ("current_username", "new_username"),
    "set_availability": ("course_identifier", "user_identifier", "available"),
    "set_available": (),
    "set_unavailable": (),
    "set_disabled": (),
    "activate": ("course_identifier", "user_identifier"),
    "deactivate": ("course_identifier", "user_identifier"),
    "delete_if_exists": ("course_identifier", "user_identifier"),
    "change_role": ("course_identifier", "user_identifier", "course_role_id"),
    "validate_course_role": ("course_role_id",),
    "find": ("course_identifier", "user_identifier"),
    "upsert": ("course_identifier", "user_identifier", "course_role_id", "availability", "data_source_id", "child_course_id"),
    "ensure_enrolled": ("course_identifier", "user_identifier", "course_role_id", "availability"),
    "list_for_courses": ("course_identifiers",),
    "list_for_users": ("user_identifiers",),
    "enroll_user_in_courses": ("user_identifier", "course_identifiers", "course_role_id"),
    "enroll_users_in_course": ("course_identifier", "user_identifiers", "course_role_id"),
}


def _add_command_options(parser: argparse.ArgumentParser, command: str) -> None:
    """Add typed, non-JSON options for one command."""
    resource, operation = COMMANDS[command]
    if resource == "api_quota":
        return
    if operation in {"create", "update"} and resource != "enrollments":
        if operation == "update":
            identifier = f"{resource.rstrip('s')}_identifier"
            parser.add_argument(f"--{identifier.replace('_', '-')}", required=True)
        parser.add_argument(
            "--field", action="append", type=_validate_field_assignment,
            metavar="NAME=VALUE",
            help=(
                "Resource field; specify once for each field. Do not supply "
                "the Blackboard-generated top-level fields id or uuid."
            ),
        )
        return
    if resource != "api_quota" and (
        operation.startswith("get") or operation.startswith("list")
    ):
        parser.add_argument(
            "--format", choices=("csv", "excel", "json"), default="json",
            help="Output format: csv, excel, or json.",
        )
        parser.add_argument(
            "--output", default=None,
            help="Output file path; if omitted, write to standard output.",
        )
    names = _command_option_names(resource, operation)
    for name in names:
        option = f"--{name.replace('_', '-')}"
        required = (
            name.endswith("identifier")
            or name.endswith("identifiers")
            or name in {"current_username", "new_username", "available", "value"}
        )
        kwargs = {"required": required}
        if name.endswith("identifiers"):
            kwargs.update(action="append", metavar=name.upper())
        if name == "primary":
            kwargs.update(action=argparse.BooleanOptionalAction, required=False, default=None)
        elif name in {"available", "availability"}:
            kwargs["choices"] = ("Yes", "No", "Disabled")
        parser.add_argument(option, dest=name, **kwargs)


def _command_option_names(resource: str, operation: str) -> tuple[str, ...]:
    """Return the command-specific option names for a facade operation."""
    if resource == "api_quota":
        return ()
    if operation in {"set_available", "set_unavailable", "set_disabled"}:
        if resource == "enrollments":
            return ("course_identifier", "user_identifier")
        return (f"{resource.rstrip('s')}_identifier",)
    if operation == "assign_node":
        return (f"{resource.rstrip('s')}_identifier", "node_identifier", "primary")
    if operation == "unassign_node":
        return (f"{resource.rstrip('s')}_identifier", "node_identifier")
    if resource == "enrollments" and operation in {"get", "delete"}:
        return ("course_identifier", "user_identifier")
    if resource == "enrollments" and operation in {"create", "update"}:
        return COMMAND_ARGUMENTS[operation]
    if operation in {"get", "delete"}:
        return (f"{resource.rstrip('s')}_identifier",)
    return COMMAND_ARGUMENTS.get(operation, ())


def command_help_text() -> str:
    """Return detailed user-facing help for every available command."""
    lines = [
        "Available commands by resource",
        "==============================",
        "Use --help after a command for detailed help.",
        "",
    ]
    for resource_name, operations in RESOURCE_COMMANDS.items():
        group_name = RESOURCE_GROUP_NAMES.get(resource_name, resource_name)
        lines.extend([group_name, "-" * len(group_name)])
        for operation_name in operations:
            command = _command_name(resource_name, operation_name)
            uses_fields = (
                operation_name in {"create", "update"}
                and resource_name != "enrollments"
            )
            names = _command_option_names(resource_name, operation_name)
            has_output_options = resource_name != "api_quota" and (
                operation_name.startswith("get")
                or operation_name.startswith("list")
            )
            description = _command_description(
                resource_name, operation_name
            )
            lines.append(f"  {command}: {description}")
            if uses_fields or has_output_options or names:
                lines.append("    Command options:")
            if has_output_options:
                lines.append(
                    "      --format: Output format: json, csv, or excel "
                    "(default: json)."
                )
                lines.append(
                    "      --output: Output file path. Required for excel; "
                    "optional for json and csv."
                )
            if uses_fields:
                if operation_name == "update":
                    identifier = f"{resource_name.rstrip('s')}_identifier"
                    lines.append(
                        f"      --{identifier.replace('_', '-')}: "
                        f"{_option_description(identifier)}"
                    )
                lines.append(
                    "      --field: Resource field; specify once for each "
                    "field. Do not supply the Blackboard-generated "
                    "top-level fields id or uuid."
                )
                if operation_name == "create":
                    lines.append(
                        f"      Creation fields: "
                        f"{_creation_field_description(resource_name)}"
                    )
            for name in (() if uses_fields else names):
                lines.append(f"      --{name.replace('_', '-')}: {_option_description(name)}")
        lines.append("")
    return "\n".join(lines)


def _option_description(name: str) -> str:
    """Return a user-facing description for a command option."""
    descriptions = {
        "course_identifier": "Course primary ID, courseId, externalId, or UUID.",
        "user_identifier": "User primary ID, userName, externalId, or UUID.",
        "node_identifier": "Node primary ID or externalId.",
        "term_identifier": "Term primary ID or externalId.",
        "course_identifiers": "Repeat once for each course identifier.",
        "user_identifiers": "Repeat once for each user identifier.",
        "course_role_id": "Course role ID, such as Student or Instructor.",
        "availability": "Optional availability: Yes, No, or Disabled.",
        "available": "One of Yes, No, or Disabled.",
        "data_source_id": "Blackboard data source key identifier.",
        "child_course_id": "Optional child course primary ID.",
        "primary": "Use --primary or --no-primary to set the node relation.",
        "current_username": "Existing Blackboard username.",
        "new_username": "New Blackboard username.",
    }
    return descriptions.get(name, "Value required by this command.")


def _creation_field_description(resource: str) -> str:
    """Describe the documented client-controlled fields for resource creation."""
    descriptions = {
        "courses": (
            "required courseId and name; optional externalId "
            "(defaults to courseId)."
        ),
        "users": (
            "required userName, password, and name; optional externalId "
            "(defaults to userName)."
        ),
        "nodes": "required title; optional externalId.",
        "terms": "required externalId and name.",
    }
    return descriptions[resource]


def _command_description(
    resource: str, operation: str
) -> str:
    """Return a clear user-facing description for a CLI command."""
    if resource == "api_quota" and operation == "get":
        return "check the current API usage quota"
    singular = resource.rstrip("s").replace("_", " ")
    article = "an" if singular == "enrollment" else "a"
    if operation == "list":
        return f"get list of {resource.replace('_', ' ')}"
    if operation == "get":
        return f"get detailed info of a given {singular}"
    if operation == "create":
        return f"creates {article} {singular}"
    if operation == "update":
        return f"updates data of an existing {singular}"
    if operation == "delete":
        return f"deletes an existing {singular}"
    if operation == "set_available":
        return f"sets a given {singular} as available"
    if operation == "set_unavailable":
        return f"sets a given {singular} as unavailable"
    if operation == "set_disabled":
        return (
            f"sets a given {singular} as disabled. Equivalent to the "
            f'"disable" option of the "integration" button in Blackboard '
            f"{resource.replace('_', ' ')} listings"
        )
    descriptions = {
        "assign_node": (
            "creates a node-course relation"
            if resource == "courses"
            else "creates a node-user relation"
        ),
        "unassign_node": (
            "removes a node-course relation"
            if resource == "courses"
            else "removes a node-user relation"
        ),
        "list_by_node": f"get list of {resource} that pertain to a given node",
        "list_by_course": f"get list of nodes that a given course belongs to"
        if resource == "nodes"
        else "get list of enrollments for a given course",
        "list_by_user": f"get list of nodes that a given user belongs to"
        if resource == "nodes"
        else "get list of enrollments for a given user",
        "assign_term": "moves a given course to a given term",
        "unassign_term": "moves a given course out of a given term",
        "get_by_course": "get the term assigned to a given course",
        "get_copy_history": "get the copy history of a given course",
        "change_username": "changes the username of an existing user",
        "find": "get an enrollment when it exists, otherwise return no result",
        "upsert": "creates an enrollment or updates it to the requested state",
        "ensure_enrolled": "ensures that a user is enrolled in a course",
        "change_role": "changes the course role of an existing enrollment",
        "set_availability": "sets the availability of an existing enrollment",
        "activate": "sets an enrollment as available",
        "deactivate": "sets an enrollment as unavailable",
        "delete_if_exists": "deletes an enrollment only when it exists",
        "validate_course_role": "checks that a course role ID is available",
        "list_for_courses": "get enrollments for multiple courses",
        "list_for_users": "get enrollments for multiple users",
        "enroll_user_in_courses": "ensures that a user is enrolled in multiple courses",
        "enroll_users_in_course": "ensures that multiple users are enrolled in a course",
    }
    return descriptions.get(
        operation,
        f"retrieve or modify the {resource.replace('_', ' ')} resource",
    )


def configure_logging(level: str) -> None:
    """Configure logging only for the CLI execution."""
    logging.basicConfig(level=getattr(logging, level))
    LOGGER.info("CLI logging configured at %s level", level)
    LOGGER.debug("DEBUG messages include conversion and dispatch details")


def create_client(args: argparse.Namespace) -> BlackboardAPI:
    """Create the API using only the configuration supplied by the CLI."""
    LOGGER.info(
        "Initializing BlackboardAPI with ENV=%s, enable_write=%s, max_retries=%s",
        args.env_file, args.enable_write, args.max_retries,
    )
    return BlackboardAPI(
        env_file=args.env_file,
        enable_write=args.enable_write,
        max_retries=args.max_retries,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, invoke a resource operation, and serialize its result."""
    force_utf8_standard_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    LOGGER.debug("CLI arguments parsed: %s", args)
    if args.command is None and not args.command_help:
        parser.print_help()
        return 0
    if args.command_help:
        print(command_help_text())
        return 0
    configure_logging(args.log_level)
    if not args.command_help and args.env_file is None:
        parser.error("--env-file is required to execute a command")
    LOGGER.debug("CLI initialized with explicit ENV file: %s", args.env_file)
    client = create_client(args)
    resource_name, operation_name = COMMANDS[args.command]
    if operation_name in MUTATING_OPERATIONS and not client.enable_write:
        LOGGER.warning(
            "Command %s is mutating but --enable-write was not specified",
            args.command,
        )
    kwargs = {
        key: value for key, value in vars(args).items()
        if key not in {"command", "command_help", "env_file", "enable_write", "log_level", "format", "output", "max_retries", "field"}
        and value is not None
    }
    if getattr(args, "field", None) is not None:
        kwargs["data"] = _parse_fields(args.field, parser)
    if "availability" in kwargs:
        kwargs["availability"] = {"available": kwargs["availability"]}
    resource = getattr(client, resource_name)
    LOGGER.info(
        "Executing command %s (%s.%s)",
        args.command, resource_name, operation_name,
    )
    try:
        result = getattr(resource, operation_name)(**kwargs)
    except Exception:
        LOGGER.exception("Error executing command %s", args.command)
        raise
    if resource_name == "api_quota" and operation_name == "get":
        print(format_api_quota(result))
        return 0
    output_format = getattr(args, "format", "json")
    excluded_fields = (
        ("copyHistory",)
        if resource_name == "courses" and output_format in {"csv", "excel"}
        else ()
    )
    _write_result(result, output_format, getattr(args, "output", None),
                  excluded_fields=excluded_fields)
    return 0


def _parse_fields(fields: list[str], parser: argparse.ArgumentParser) -> dict:
    """Convert repeated NAME=VALUE options into a simple data mapping."""
    data = {}
    for field in fields:
        name, value = field.split("=", 1)
        target = data
        parts = name.split(".")
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = _parse_scalar(value)
    return data


def _parse_scalar(value: str) -> str | int | float | bool:
    """Convert a command-line scalar to a Python primitive."""
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return float(value) if "." in value else int(value)
    except ValueError:
        return value


def _write_result(
    result: object,
    output_format: str,
    output: str | None,
    *,
    excluded_fields: tuple[str, ...] = (),
) -> None:
    """Write an operation result using the selected output format."""
    if output_format in {"csv", "excel"}:
        LOGGER.info("Converting result to %s format", output_format)
        items = result if isinstance(result, list) else [result]
        rows = objects_to_rows(items, excluded_fields=excluded_fields)
        if output_format == "excel" and output is None:
            LOGGER.error(
                "Cannot export %s format without --output",
                output_format,
            )
            raise ValueError("--output is required for excel format")
        if output is not None:
            _validate_output_path(output)
        if output_format == "csv":
            LOGGER.info("Exportando CSV a %s", output)
            rows_to_csv(rows, output)
        else:
            LOGGER.info("Exportando Excel a %s", output)
            rows_to_excel(rows, output)
        return
    LOGGER.info("Serializando resultado en formato JSON")
    text = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if output is None:
        print(text)
        return
    _validate_output_path(output)
    Path(output).write_text(text + "\n", encoding="utf-8")


def _validate_output_path(output: str) -> None:
    """Reject existing destinations and missing parent directories."""
    destination = Path(output)
    if destination.exists():
        raise ValueError(f"Output destination already exists: {output}")
    if not destination.parent.is_dir():
        raise ValueError(f"Output directory does not exist: {destination.parent}")
