# golangconfig Development

## Setup

 - Install [Package Coverage](https://packagecontrol.io/packages/Package%20Coverage)
   to run tests
 - Install the [shellenv](https://github.com/codexns/shellenv) dependency by
   executing `git clone --branch 1.4.1 https://github.com/codexns/shellenv`
   inside of your `Packages/` folder
 - Install this dependency by
   executing `git clone https://go.googlesource.com/sublime-config golangconfig`
   inside of your `Packages/` folder
 - Use the Package Control command "Install Local Dependency" to install
   `shellenv` and then `golangconfig` so they are available to the Python plugin
   environment

## General Notes

 - All code must pass the checks of the Sublime Text package
   [Python Flake8 Lint](https://packagecontrol.io/packages/Python%20Flake8%20Lint).
   The `python_interpreter` setting should be set to `internal`.
 - Tests and coverage measurement must be run in the UI thread since the package
   utilizes the `sublime` API, which is not thread safe on ST2
 - Sublime Text 2 and 3 must be supported, on Windows, OS X and Linux
 - In public-facing functions, types should be strictly checked to help reduce
   edge-case bugs
 - All functions must include a full docstring with parameter and return types
   and a list of exceptions raised
 - All code should use a consistent Python header

```python
# coding: utf-8
from __future__ import unicode_literals, division, absolute_import, print_function
```

 - Markdown-based API documentation can be automatically copied from the source
   code by executing `dev/api_docs.py` with a Python installation containing
   the `CommonMark` package

```bash
pip install CommonMark
python dev/api_docs.py
```
