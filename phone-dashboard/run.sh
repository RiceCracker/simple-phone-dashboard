#!/usr/bin/env bash

# Setting up virtual env
. "./env/bin/activate"
export LC_ALL=de_DE.utf8
export FLASK_APP=run.py
export FLASK_ENV=development
export FLASK_DEBUG=1

# Run API
flask run --host=0.0.0.0 --port=5001
