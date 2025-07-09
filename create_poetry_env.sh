#!/bin/bash

# Remove existing python env
# Uncomment this if you want to rebuild the python env from scratch
# python3 -m poetry env remove python3

# Date just used to show how long the env takes to create
date
python3 -m poetry lock
python3 -m poetry install
date
