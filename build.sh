#!/bin/bash
# Ensure we remove old installer versions.
rm -rf dist
rm -f installers/linux/*.whl
set -e
# syntax checking
pyflakes3 src/retirement_finances/*.py
# code style checking
pycodestyle --max-line-length=300 src/retirement_finances/*.py
cp pyproject.toml src/retirement_finances/assets
poetry -vvv build
cp dist/*.whl installers/linux
# Generate new docx readme file
./create_single_docx_readme.sh

