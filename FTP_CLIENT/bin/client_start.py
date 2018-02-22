#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__:JasonLIN
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
from core import ftp_client


if __name__ == '__main__':
    ftp_client.start()