#!/bin/bash
# Ensure we remove old installer versions.
rm -rf dist
rm -f installers/linux/*.whl
rm -f installers/windows/*.whl
set -e
# syntax checking
pyflakes3 retirement_finances/*.py
# code style checking
pycodestyle --max-line-length=250 retirement_finances/*.py
poetry -vvv build
cp dist/*.whl installers/linux
cp dist/*.whl installers/windows
# Generate new docx readme file
./create_single_docx_readme.sh

