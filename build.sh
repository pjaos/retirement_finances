#!/bin/bash
# Ensure we remove old installer versions.
rm -rf dist
set -e
# syntax checking
pyflakes3 retirement_finances/*.py
# code style checking
pycodestyle --max-line-length=250 retirement_finances/*.py
poetry -vvv build
cp dist/*.whl installers


