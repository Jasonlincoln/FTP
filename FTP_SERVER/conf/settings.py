#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__:JasonLIN
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

USER_HOME = os.path.join(BASE_DIR, 'home')
LOG_DIR = os.path.join(BASE_DIR, 'log')
LOG_LEVEL = "DEBUG"
HOME_PATH = os.path.join(BASE_DIR, "home")
ACCOUNT_FILE = os.path.join(BASE_DIR, 'db', "accounts.txt")
HOST = "127.0.0.1"
PORT = 9999