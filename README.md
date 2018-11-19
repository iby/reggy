# Reggy [![Build Status](https://travis-ci.com/ianbytchek/reggy.svg?branch=master)](https://travis-ci.com/ianbytchek/reggy)

Reggy is a micro-utility for matching rule-identified tokens inside the given text using simple pattern syntax. Basic usage:

```py
from reggy.matcher import Matcher
matches = Matcher().match('foo %{0} baz %{1}', 'foo bar baz qux') # {0: ['bar'], 1: [qux]}
```

See code for documentation and unit tests for more usage examples.

## Setup

Reggy requires Python 3.6, uses [Virtualenv](https://github.com/pypa/virtualenv) for isolated Python environment and [pytest](https://github.com/pytest-dev/pytest) for testing. All dependencies and sources live in `dependency` and `source` folders, respectively.

Checkout repository from the GitHub, setup and activate Virtualenv and install dependencies, make sure to `cd dependency` prior that:

```sh
python3 -m venv 'Virtualenv'
source 'Virtualenv/bin/activate'
pip install -r 'requirements.txt'
```

To confirm everything's operational run the tests, make sure to `cd ../source` from `dependency` directory.

```sh
python -m pytest -v reggy
```
