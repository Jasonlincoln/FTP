#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__:JasonLIN
#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" __author__:JasonLIN """
import logging
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from FTP_SERVER.conf import settings


def login_log(msg):  # login log
    logger = logging.getLogger("user login success log")
    logger.setLevel(logging.DEBUG)
    login_log_file = os.path.join(settings.LOG_DIR, "login.log")
    fh = logging.FileHandler(login_log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh_formatter = logging.Formatter("%(asctime)s %(message)s")
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    logger.debug(msg)


def operate_log(msg, level):
    logger = logging.getLogger("user operate log")
    logger.setLevel(logging.DEBUG)
    operate_log_file = os.path.join(settings.LOG_DIR, "operate.log")
    fh = logging.FileHandler(operate_log_file, encoding="utf-8")
    ch = logging.StreamHandler()
    fh.setLevel(logging.DEBUG)
    ch.setLevel(logging.ERROR)
    fh_formatter = logging.Formatter("%(asctime)s %(message)s")
    ch_formatter = logging.StreamHandler("%(asctime)s %(message)s")
    fh.setFormatter(fh_formatter)
    ch.setFormatter(ch_formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    if level == "error":
        logger.error(msg)
    elif level == "debug":
        logger.debug(msg)
    else:
        print("level is invalid")
        return



