# Developers

## Development setup

Install the project and development tools in editable mode:

```text
python -m pip install -e ".[dev]"
```

## Unit tests

Run automated tests with:

```text
python -m unittest discover -s tests/unit -v
```

Unit tests are 100% offline and never require Blackboard credentials or an
environment file.

## Live integration tests

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

## Contact and collaboration requests

via email: [hello@alejandroamo.eu](mailto://hello@alejandroamo.eu)