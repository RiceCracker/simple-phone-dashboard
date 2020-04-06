#!/usr/bin/env bash

# Setting up virtual env
. "./venv/bin/activate"
export LC_ALL=de_DE.utf8
export FLASK_APP=api.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run API
flask run
