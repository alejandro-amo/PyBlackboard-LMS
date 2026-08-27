# PyBlackboard-LMS

Python and command-line interfaces for Blackboard LMS API.

The Python API (`blackboard_api`) provides:

- Resilient HTTP transport and OAuth authentication.
- API quota tracking.
- Transparent pagination for object collections.
- Iterators for consuming large result sets without accumulating every item in memory.
- An atomic operations layer for individual requests (`resources`).
- A service layer for combinations of operations, such as upserts (`services`).
- Public facades with validated, human-oriented methods.

The `blackboard-cli` command exposes every public facade method except iterators,
and can export data as JSON, CSV, or Microsoft Excel files. It is intended as a
data exploration and management tool for Blackboard administrators.

## Installation

PyBlackboard-LMS requires Python 3.10 or later.

```text
python -m pip install PyBlackboard-LMS
```

The package installs the `blackboard-cli` command and the `blackboard_api` module.

## Configuration with explicit parameter values (API only)

In a Python script:

```python
from blackboard_api import BlackboardAPI
client = BlackboardAPI(
    url="https://blackboard.example.com",
    client_id="...",
    client_secret="...",
)
```

`url` is the URL of the Blackboard instance. `client_id` is the value called
`APP_KEY` in the [Blackboard Developer Portal](https://developer.blackboard.com/portal/applications),
and `client_secret` is its corresponding `APP_SECRET` value.

## Configuration with .env files (API and CLI)

When creating `BlackboardAPI` without direct credentials, `env_file` is required.
Both the API and CLI use dotenv-style files as their configuration source.

1. Copy the `.env.example` template file to `.env.production.local` and configure it with
API credentials and Blackboard instance URL of your **PRODUCTION** Blackboard instance.

2. Copy the `.env.example` template file to `.env.test.local` and configure it with
API credentials and Blackboard instance URL of your **TEST** Blackboard instance,
if you have any.

You can then specify the ENV-file path with:

```text
blackboard-cli --env-file .env.production.local <command>
```

or use the API directly:

```python
from blackboard_api import BlackboardAPI

client = BlackboardAPI(env_file=".env.production.local")
```

The optional `BB_REQUEST_CONNECT_TIMEOUT` and `BB_REQUEST_READ_TIMEOUT` ENV
settings are positive integer durations in seconds. They default to `10` and
`60`, respectively. You can add them to env files if you want to tweak them.

## Writes are disabled by default

To reduce the risk of accidental changes, mutating operations are disabled by
default. The API blocks `POST`, `PUT`, `PATCH`, and `DELETE` before they reach
Blackboard unless writes are explicitly enabled.

You can enable writing operations by passing
`enable_write=True` to `BlackboardAPI`, or `--enable-write` to the CLI.

## API reference

See [the API reference](https://github.com/alejandro-amo/PyBlackboard-LMS/blob/master/docs/api_reference.md) for the public interface and
internal layers.

## CLI command reference

The CLI exposes one command for every public API facade method except iterators.
Iterators are intended for progressive data consumption in Python scripts and
do not provide a useful CLI abstraction.

See [the CLI reference](https://github.com/alejandro-amo/PyBlackboard-LMS/blob/master/docs/cli_reference.md) for the complete command list.

Use `--command-help` to view every available command.

## Developers only

### Development setup

Install the project and development tools in editable mode:

```text
python -m pip install -e ".[dev]"
```

### Unit tests

Run automated tests with:

```text
python -m unittest discover -s tests/unit -v
```

Unit tests are 100% offline and never require Blackboard credentials or an
environment file.

### Live integration tests

Run live integration tests with:

```text
python -m tests.integration.run
```

While unit tests are fully offline, live integration tests connect to Blackboard
and create, modify, and delete test objects. Use an isolated **test tenant** and
ensure that `.env.test.local` contains only its credentials. The test runner requires
that file, but cannot verify that its URL is truly a non-production instance.
If test environment dot-env file is missing or invalid, live integration tests fail.

The test runner writes the same messages to standard output and to a timestamped log
under `data/test-artifacts/logs/`. Use `--log-level DEBUG` for HTTP and
fixture lifecycle diagnostics. It never logs credentials, OAuth tokens, or
passwords.

The integration test suite uses randomized, easily recognizable identifiers to avoid
collisions with existing data. Its final test explicitly verifies cleanup,
and emergency cleanup is attempted when the process exits.
Failures outside the process or API failures may still require manual review of the
test tenant.
