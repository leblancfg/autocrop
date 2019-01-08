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
This project works with [virtualenv](https://virtualenv.pypa.io/en/latest/).

To start things off, run:

```
$ python3 -m venv env
$ source env/bin/activate
```

Then, run:

```
$ pip install -U setuptools
$ pip install -r requirements-test.txt
$ pip install -e .
```

You can then run `autocrop` like so:

```
$ autocrop
```

As long as the virtual environment has been activated, this will command will
use the files in your local Git checkout. This makes it super easy to work on
the code and test your changes.

To set up your virtual environment again in future, just run:

```
$ source env/bin/activate
```

## Tests

Pull requests are tested using continuous integration (CI) which will
green-light changes.

Specifically, we:

* Use [flake8](http://flake8.pycqa.org/en/latest/) for coding style tests
* Run a test suite using [pytest](https://docs.pytest.org/en/latest/)

You can run the tests locally, like so:

```
$ make check
```


## Contact

If you have any questions, please email me at
[leblancfg@gmail.com](mailto:leblancfg@gmail.com).
