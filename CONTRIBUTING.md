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
This project works with [virtual envronments](https://docs.python.org/3/library/venv.html) and has a [Makefile](https://krzysztofzuraw.com/blog/2016/makefiles-in-python-projects) for common tasks.

>⚠️  This guide (and the Makefile) assumes that you use `python` to call your interpreter.
>
> * For Debian and Ubuntu, you might need to use `python3` instead.
> * For MacOS, you are best to `brew install pyenv` and [follow these instructions](https://opensource.com/article/19/5/python-3-default-mac).
> * For Windows, it is strongly encouraged to check out the [conda distribution](https://docs.conda.io/projects/conda/en/latest/user-guide/install/windows.html).

To start things off, run

```sh
make initial_setup
. env/bin/activate
```

Alternatively:

```sh
python -m venv env
. env/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

You can then run `autocrop` like so:

```sh
autocrop --help
```

As long as the virtual environment has been activated, this will command will
use the files in your local Git checkout. This makes it super easy to work on
the code and test your changes.

To set up your virtual environment again in future, just run:

```sh
. env/bin/activate
```

And when you're done, return your terminal to its previous state with:

```sh
deactivate
```

## Tests

Pull requests are tested using continuous integration (CI) which will
green-light changes.

Specifically, we:

* Use [flake8](http://flake8.pycqa.org/en/latest/) for coding style tests
* Run a test suite using [pytest](https://docs.pytest.org/en/latest/)

You can run the tests locally, like so:

```
make check
```


## Contact

If you have any questions, please email me at
[leblancfg@gmail.com](mailto:leblancfg@gmail.com).
