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
