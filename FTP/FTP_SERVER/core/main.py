#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__:JasonLIN
from optparse import OptionParser
import socketserver
from FTP_SERVER.core.ftp_server import FTPHandler
from FTP_SERVER.conf import settings
import configparser
import os
config = configparser.ConfigParser()


class ArgvHandler(socketserver.BaseRequestHandler):
    def __init__(self):
        self.parser = OptionParser()
        (options, args) = self.parser.parse_args()

        self.verify(options, args)

    def verify(self, options, args):
        """校验并调用相应的功能"""
        if hasattr(self, args[0]):
            func = getattr(self, args[0])
            func()
        else:
            self.parser.print_help()

    def start(self):
        print('---going to start server----')
        host = settings.HOST
        port = settings.PORT
        server = socketserver.ThreadingTCPServer((host, port), FTPHandler)
        server.serve_forever()

    def config_write(self):
        config.write(open(settings.ACCOUNT_FILE, "w"))

    def config_read(self):
        config.read(settings.ACCOUNT_FILE, encoding="utf-8")

    def create(self):
        print("welcome! boss")
        while True:
            user = input("create a new username:").strip()
            self.config_read()
            user_list = config.sections()
            # print(user_list)
            if user in user_list:
                print("[%s] already exists" % user)
            else:
                config.add_section(user)
                self.config_write()
                break
        password = input("please set user password:").strip()
        config.set(user, "password", password)
        
        while True:
            space = input("set user quotation(Mb):").strip()
            try:
                quotation = str(int(space) * 1024 * 1024)
                config.set(user, "Quotation", quotation)
                config.set(user, "rest space", quotation)
                self.config_write()
                os.mkdir(os.path.join(settings.HOME_PATH, user))
                print("create user[%s] successful" % user)
                break
            except ValueError:
                print("please enter digit")
                

    def view(self):
        self.config_read()
        userlist = config.sections()
        print(userlist)
        while True:
            user = input("please enter the user you want to view:")
            if user == "q" or user == "exit":
                break
            password = config.get(user, "password")
            quotation = float(int(config.get(user, "Quotation"))/1024/1024)
            rest_space = float(int(config.get(user, "rest space"))/1024/1024)
            info = """
                user: %s
                password: %s
                Quotation: %.2f
                reat space: %.2f
            """.format() % (user, password, quotation, rest_space)
            print(info)

    def setup(self):
        self.config_read()
        userlist = config.sections()
        print(userlist)
        while True:
            user = input("select the modified user:").strip()
            if user == 'q' or user == "exit":
                break
            user_list = config.sections()
            if user in user_list:
                item_list = config.options(user)
                print(item_list)
                choice = input("select the modified item:").strip()
                if choice == 'q' or choice == "exit":
                    break
                if choice in item_list:
                    val = input("enter the value you want to change:")
                    if val == 'q' or val == "exit":
                        break
                    config.set(user, choice, val)
                    self.config_write()
                    print("change the value of [%s] to [%s] successfully:" % (choice, val))
                    continue
                else:
                    print("invalid item")
            else:
                print("[%s] is not exists" % user)

    def rm(self):
        while True:
            self.config_read()
            user_list = config.sections()
            for user in user_list:
                print(user, type(user))
            choice = input("enter username to delete:").strip()
            if choice == "q" or choice == "exit":
                break
            if choice in user_list:
                config.remove_section(choice)
                self.config_write()
                print("delete %s successful" % choice)
                continue
            else:
                print("%s  not exists" % choice)
