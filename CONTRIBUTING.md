# Contributing
All contributions, bug reports, bug fixes, documentation improvements, enhancements, and ideas are welcome.

Please follow these steps:

* Fork the [autocrop](https://github.com/leblancfg/autocrop) repository to your
  personal GitHub account and clone it locally
* Install the development setup (see section below)
* Branch off of `master` for every change you want to make
* Develop changes on your branch
* Test your changes (see section below)
* Modify the tests and documentation as necessary
* When your changes are ready, make a pull request to the upstream
  [autocrop](https://github.com/leblancfg/autocrop) repository

## Development Setup
This project uses [uv](https://docs.astral.sh/uv/) for development environments
and command execution.

To start things off, run:

```
$ uv venv
$ uv pip install -r requirements-dev.txt -e .
```

You can then run `autocrop` like so:

```
$ uv run autocrop
```

This uses the files in your local Git checkout, which makes it easy to work on
the code and test your changes.

To refresh your local environment in future, run:

```
$ uv pip install -r requirements-dev.txt -e .
```

## Tests

Pull requests are tested using continuous integration (CI) which will
green-light changes.

Specifically, we:

* Use [just](https://just.systems/) as the project command runner
* Use [flake8](http://flake8.pycqa.org/en/latest/) for coding style tests
* Run a test suite using [pytest](https://docs.pytest.org/en/latest/)

You can run the tests locally, like so:

```
$ just check
```


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
