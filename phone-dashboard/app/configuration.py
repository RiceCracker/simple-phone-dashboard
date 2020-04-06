# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

class Config():
	# Dashboard
	CSRF_ENABLED = True
	SECRET_KEY   = "The quick brown fox jumps over the fence"

	SQLALCHEMY_TRACK_MODIFICATIONS 	= False

	SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')

	# API
	API_SSL       = "http"
	API_URI       = "localhost"
	API_PORT      = "5000/api"
	API_AUTH_USER = "username"
	API_AUTH_PASS = "password"
