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
The consumer checks also verify rejection of the retired array return and diagnostics flag.


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

1. Finish API/release-blocker review and wait for the latest CI checks to pass.
2. Update `autocrop/__version__.py` and date the release in `docs/changelog.md`
   (the canonical changelog). Merge the reviewed release changes.
3. Check the exact commit you will tag:
   ```sh
   uv sync --locked
   just check
   uv build
   uvx --from twine twine check dist/*
   ```
   Use a clean `dist/` directory so no older distributions are included.
4. Prepare a **draft** GitHub Release targeting that reviewed commit, with a tag
   matching the package version (for example `v2.0.0`). Review its notes and any
   assets before publication. With immutable releases enabled, the published
   tag and assets cannot be replaced.
5. Publish the draft only after final approval. This triggers `Build`, which
   checks the tag/version, builds the sdist and wheel, and uploads to PyPI through
   OIDC. A successful GitHub Release alone does not mean PyPI publishing succeeded.
6. Watch `Build`, verify the version and both files on PyPI, then smoke-test a
   fresh installation from PyPI outside the source checkout.

If GitHub published the release but the PyPI upload failed, fix the cause and
rerun `Build` for the same tag. Do not move a published tag or try to replace a
published PyPI distribution. Never enable auto-merge as a substitute for release
approval.

### Pending 2.0.0 review stack

The native GitHub stack starts with #221 (typing only, targeting `master`), then
#213 (diagnostics), #214 (alignment), and #219 (migration FAQ and errors).
Review and merge from the base upward in that order. #221 preserves the current
array-or-None API; the result-object change belongs to #213.

After approval and green CI, use GitHub's stack merge controls to merge the
lowest PR or a contiguous group starting there. Selecting #219 includes the
whole approved stack. GitHub rebases the next unmerged PR onto the stack base
after a partial merge; wait for any new checks before continuing. Do not follow
the former reverse-order/manual-base-edit recipe for these native stacked PRs.

See [GitHub's stack merge guide](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-stacked-pull-requests).
Nothing should be merged or published without maintainer approval.

Before publishing, explicitly resolve or defer the SDK design decisions in
#215 (input types), #216 (array ownership), #217 (detector configuration), and
#218 (numeric validation). They were recorded for discussion, not silently fixed
by this stack. The old `v2.0.0` release/tag were deleted; do not recreate them
until this review is complete.
