# Contributing
All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

Please follow these steps:

* Fork the [autocrop](https://github.com/leblancfg/autocrop) repository to your
  personal GitHub account and clone it locally
* Install the development setup (see section below)
* Branch off of `master` for every change you want to make
* Develop changes on your branch
* Test your changes (see section below)
* Modify the tests and documentation as necessary; annotate public and internal package functions
* When your changes are ready, make a pull request to the upstream
  [autocrop](https://github.com/leblancfg/autocrop) repository

## Development Setup
This project uses [uv](https://docs.astral.sh/uv/) for development environments
and command execution.

To start things off, run:

```
$ uv sync
```

You can then run `autocrop` like so:

```
$ uv run autocrop
```

This uses the files in your local Git checkout, which makes it easy to work on
the code and test your changes.

To refresh your local environment in future, run:

```
$ uv sync
```

## Tests

Pull requests are tested using continuous integration (CI) which will
green-light changes.

Specifically, we:

* Use [just](https://just.systems/) as the project command runner
* Use [Ruff](https://docs.astral.sh/ruff/) for linting, import sorting, and formatting
* Check package types and downstream usage examples with [ty](https://docs.astral.sh/ty/)
* Run a test suite using [pytest](https://docs.pytest.org/en/latest/)

You can run the tests locally, like so:

```
$ just check
```

This runs Ruff linting and format checks, `just typecheck` (ty), and tests.
Use `just format` to apply formatting, or `uv run ruff check --fix autocrop tests`
for safe lint fixes and import sorting. CI only checks files; it never rewrites them.

Ruff also requires annotations on package functions and limits complexity to 10.
Ty checks the package and `tests/typing`, failing on warnings as well as errors.
CI runs these checks on every supported Python/OS combination. The package ships
`py.typed`; the consumer examples use `assert_type` to check the public API. Keep
dynamic types confined to external-library boundaries and use specific
`ty: ignore[rule]` comments only when justified. Unused ignores fail the check.


## Contact

If you have any questions, please email me at
[leblancfg@gmail.com](mailto:leblancfg@gmail.com).

## Releasing

PyPI releases are published from GitHub Actions with PyPI trusted publishing, so
the release workflow does not use a long-lived API token.

One-time PyPI setup:

1. Open the PyPI project: `https://pypi.org/project/autocrop/`.
2. Go to **Publishing**, then add a trusted publisher.
3. Use these values:
   - Owner: `leblancfg`
   - Repository name: `autocrop`
   - Workflow filename: `build.yml`
   - Environment name: leave blank unless the workflow later adds a protected environment
4. Save the trusted publisher.

Release flow:

1. Merge the release commit that updates `autocrop/__version__.py` and `changelog.md`.
2. Create and publish a GitHub Release with a tag that exactly matches the
   package version, for example `v1.3.1`.
3. The `Build` workflow checks out that tag, verifies the tag matches the
   package version, builds the sdist and wheel, and publishes to PyPI through
   OIDC.

If the GitHub Release already exists but PyPI did not publish, rerun
`.github/workflows/build.yml` manually with the release tag.
