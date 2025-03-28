#!/bin/bash

set -e

# Check [python3 is installed.
python3 --version

sudo apt install pipx
pipx ensurepath

# Install pip
#curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
#python3 get-pip.py

# Ensure we have the latest pip version
#python3 -m pip install --upgrade pip

# Ensure we have pipx installed
#python3 -m pip install pipx

# Ensure the path is set to reach application installed with pipx
#python3 -m pipx ensurepath

# Install the retirement finances app via pipx, this may take a while...
#python3 -m pipx install retirement_finances-3.7-py3-none-any.whl

pipx install retirement_finances-3.7-py3-none-any.whl
