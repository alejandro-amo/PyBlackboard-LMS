# PyBlackboard-LMS

Python and command-line interfaces for Blackboard LMS API.

`blackboard_api` is a Python module that provides Blackboard LMS API interfaces. It features:

- Resilient HTTP transport and OAuth authentication.
- API quota tracking.
- A write lock that blocks mutating operations before they reach Blackboard.
- Transparent pagination for object collections.
- Iterators for consuming large result sets without accumulating every item in memory.
- An abstraction layer that provides human-oriented methods for doing the most common tasks.

`blackboard-cli` is a command-line tool that exposes the methods provided by
`blackboard_api` and can export data as JSON, CSV, or Microsoft Excel files. It is intended as a
data exploration and management tool for Blackboard administrators.

## Installation

PyBlackboard-LMS requires Python 3.10 or later.

```text
python -m pip install PyBlackboard-LMS
```

The package installs the `blackboard-cli` command and the `blackboard_api` module.

## API reference

See [the API reference](https://github.com/alejandro-amo/PyBlackboard-LMS/blob/master/docs/api_reference.md) for the public interface.

## CLI command reference

See [the CLI reference](https://github.com/alejandro-amo/PyBlackboard-LMS/blob/master/docs/cli_reference.md) for the complete command list.

Use `--command-help` to view every available command.

## Contact and collaboration requests

via email: [hello@alejandroamo.eu](mailto://hello@alejandroamo.eu)
