main file app.py
This interface looks up for webages containing specific entity word(s).
It uses Mysql database.
It requires a config file with passwords like this (secret key, user&password to set):

import os

basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = ' '
DB_USER = ' '
DB_PWD = ' '
DB_NAME = 'nlp'