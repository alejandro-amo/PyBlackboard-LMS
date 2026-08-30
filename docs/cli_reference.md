# CLI Reference

The CLI exposes API operations as user-oriented commands. Users do not need to
know the internal client structure.

## API coverage

The CLI provides every public facade method except iterator methods (`iter` and
`iter_by_*`). Iterators are intended for direct Python API use; collection
commands invoke the corresponding eager `list` method instead.

This is a coverage contract: every new public facade method needs a CLI command
unless it is explicitly an iterator or internal configuration operation.

## Syntax

```text
python -m blackboard_cli [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

Global options precede the command. Each command has its own subparser and
accepts text, numeric, boolean, or repeated field options; it does not accept
JSON input.

```text
python -m blackboard_cli \
  --env-file .env.production.local \
  get-course \
  --course-identifier "_11811_1"
```

## Global options

| Option | Description |
|---|---|
| `--env-file` | Required ENV file for the CLI. |
| `--enable-write` | Allows mutating commands for this invocation. |
| `--log-level` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `--max-retries` | Additional retries after the initial attempt. |
| `--command-help` | Shows commands, descriptions, and arguments. |

`--format` and `--output` are command options, not global options. They are
available only on `get-*` and `list-*` commands. `--format` accepts `json`,
`csv`, or `excel`; `--output` is required for Excel and optional for JSON/CSV.

Writes are disabled by default. The ENV file cannot enable them; use
`--enable-write` explicitly for a mutating command.

The CLI configures its standard output and standard error streams as UTF-8 on
Windows and Linux. CSV and JSON written to standard output therefore use UTF-8.

## Courses

```text
list-courses
get-course
create-course
update-course
delete-course
set-available-course
set-unavailable-course
set-disabled-course
list-courses-by-node
list-courses-by-term
get-course-copy-history
assign-node-to-course
unassign-node-to-course
assign-term-to-course
unassign-term-to-course
```

Course commands use `course_identifier`; node and term relations use
`node_identifier` and `term_identifier`.

## Users

```text
list-users
get-user
create-user
update-user
delete-user
set-available-user
set-unavailable-user
set-disabled-user
list-users-by-node
assign-node-to-user
unassign-node-to-user
change-username
```

`change-username` requires `current_username` and `new_username`.

## Nodes

```text
list-nodes
get-node
create-node
update-node
delete-node
list-nodes-by-course
list-nodes-by-user
```

## Enrollments

```text
list-enrollments-by-course
list-enrollments-by-user
get-enrollment
create-enrollment
update-enrollment
delete-enrollment
set-available-enrollment
set-unavailable-enrollment
set-disabled-enrollment
find-enrollment
upsert-enrollment
change-role-enrollment
set-availability-enrollment
activate-enrollment
deactivate-enrollment
delete-enrollment-by-if-exists
validate-course-role-enrollment
list-enrollments-for-courses
list-enrollments-for-users
enroll-user-in-courses-enrollment
enroll-users-in-course-enrollment
```

Enrollment commands receive their course and user identifiers through dedicated
command options.

## Resource fields

Non-enrollment `create-*` and `update-*` commands use repeated
`--field NAME=VALUE` options instead of JSON. Specify `--field` once per field.
Dotted names create nested objects.

Do not supply top-level `id` or `uuid`: Blackboard manages them and the CLI
rejects them.

| Command | Minimum creation fields | Client-controlled identifier |
|---|---|---|
| `create-course` | `courseId`, `name` | optional `externalId` |
| `create-user` | `userName`, `password`, `name.given`, `name.family` | optional `externalId` |
| `create-node` | `title` | optional `externalId` |
| `create-term` | `externalId`, `name` | required `externalId` |

Example:

```text
--field name="Example course" --field availability.available=Yes
```

## Terms

```text
list-terms
get-term
create-term
update-term
delete-term
get-term-by-course
```

## Enrollment roles and API usage quota

```text
list-enrollment-roles
check-api-quota
```

`check-api-quota` writes the known quota as
`remaining/max_requests_per_day`, for example `1234/10000`. If necessary, the
client makes a safe GET request to obtain quota headers. Unknown values use
`?`, for example `?/10000` or `?/?`.

## Command help

General help is concise. Use this command for the detailed command list:

```text
python -m blackboard_cli --command-help
```

## Exporting output

CSV can be written to standard output or to a file:

```text
python -m blackboard_cli --env-file .env.production.local \
  list-courses --format csv
```

Excel requires `--output`:

```text
python -m blackboard_cli --env-file .env.production.local \
  list-courses --format excel --output courses.xlsx
```

JSON is the default format and writes to standard output without `--output`.
When `--output` is used, its destination must not exist and its parent
directory must already exist. The CLI never overwrites files or creates missing
output directories.
