#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__:JasonLIN

import socket
import os
import json
from optparse import OptionParser
import getpass
import hashlib
import struct
from FTP_CLIENT.conf import settings

STATUS_CODE = {
    250: "invalid cmd format, e.g : {'action':'get', 'filename' : 'test.py', 'size':344}",
    251: "Invalid cmd",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename does not provided",
    256: "File does not exist on server",
    257: "ready to send file",
    258: "md5 verification",
    259: "file has sent done",
    260: "adequate disk space",
    261: "Insufficient disk space",
    262: "File consistency check is successful",
    263: "file breakpoint is continued",
    267: "ready to recv file",
    269: "file has received done",
    300: "send data header",
    240: "delete path successful",
    241: "the path is not exists",
    242: "make dir successful",
    243: "the path is exists",
    244: "the path is not void can not be deleted",
    245: "the file has deleted successful",
    246: "the file is not exists",
    247: "the file is deleting, please wait...",
    248: "The file is empty under this path",
    249: "The file is not empty under this path",
    230: "return  path",
    231: "return path or file",
    401: "exit",
}


class FTPClient(object):
    def __init__(self):
        parser = OptionParser()
        parser.add_option("-s", "--server", dest="server", help="ftp server ip_addr")
        parser.add_option("-P", "--port", type="int", dest="port", help="port")
        parser.add_option("-u", "--username", dest="user", help="user")
        parser.add_option("-p", "--password", dest="password", help="password")
        (self.options, self.args) = parser.parse_args()
        self.verify_args(self.options, self.args)
        self.make_connection()

    def verify_args(self, options, args):
        """检验参数合法性"""
        if options.user is None and options.password is None:
            pass
        elif options.user is not None or options.password is not None:
            pass
        else:
            exit("\033[31;1m error:username and password must be provided together\033[0m")

        if options.server is not None and options.port is not None:
            if 0 < options.port < 65535:
                return True
            else:
                exit("error:host port must in 0-65535")

    def authenticate(self):
        """ 用户验证 """
        if self.options.user:
            print(self.options.user, self.options.password)
            return self.get_auth_result(self.options.username, self.options.password)
        else:
            retry_count = 0
            while retry_count < 3:
                username = input("username:").strip()
                password = getpass.getpass("password:").strip()
                res = self.get_auth_result(username, password)
                if res:
                    return res
                retry_count += 1
            else:
                exit("error too many times")

    def make_connection(self):
        self.sock = socket.socket()
        print(self.options.server, self.options.port)
        self.sock.connect((self.options.server, self.options.port))

    def get_auth_result(self, user, password):
        """
        验证用户名及密码
        :param user:
        :param password:
        :return: self.user
        """
        data = {
            "action": "auth",
            "username": user,
            "password": password,
        }
        self.send_response(300, data)
        response = self.get_response()
        if response.get("status_code") == 254:
            print(STATUS_CODE[254])
            self.user = user
            # print("user:", self.user)
            return True
        else:
            print(response.get("status_msg"))

    def get_response(self):
        """ 得到服务器回复的结果"""
        head_len_obj = self.sock.recv(4)
        head_len = struct.unpack("i", head_len_obj)[0]
        data = self.sock.recv(head_len)
        data = json.loads(data.decode())
        return data

    def send_response(self, status, data=None):
        response = {"status_code": status, "status_msg": STATUS_CODE[status]}
        if data:
            response.update(data)
            response["status_code"] = status
        bytes_response = bytes(json.dumps(response), encoding="utf-8")
        head_len = struct.pack("i", len(bytes_response))
        self.sock.send(head_len)
        self.sock.send(bytes_response)

    def interactive(self):
        """交互"""
        if self.authenticate():
            print("--start interactive with u...")
            while True:
                cmd = input("[%s] : " % self.user).strip()
                if len(cmd) == 0:
                    continue
                else:
                    cmd_list = cmd.split(' ')
                    if len(cmd_list) == 1:
                        if hasattr(self, "cmd_%s" % cmd):
                            func = getattr(self, "cmd_%s" % cmd)
                            data = {"cmd": "single"}
                            func(data)
                        else:
                            print("invalid cmd ")
                    elif len(cmd_list) > 1:
                        if hasattr(self, "_%s" % cmd_list[0]):
                            func = getattr(self, "_%s" % cmd_list[0])
                            func(cmd_list)
                    else:
                        print("Ivalid cmd fromat")

    def __md5_required(self, cmd_list):
        """检测命令是否需要进行MD5验证"""
        if "md5" in cmd_list:
            print("md5 is required")
            return True

    def show_progress(self, total):
        """进度条展示"""
        receive_size = 0
        current_present = 0
        while receive_size < total:
            if int((receive_size / total) * 100) > current_present:
                print("#", end="", flush=True)
                current_present = int((receive_size / total) * 100)
            new_size = yield
            receive_size += new_size

    def cmd_exit(self, *args):
        """退出"""
        self.send_response(401)
        exit("---exit---")

    def cmd_q(self, *args):
        """返回登录界面"""
        print("---out---")
        self.authenticate()

    def _mkdir(self, cmd_list, *args):
        path = cmd_list[1]
        data_header = {
            "action": "mkdir",
            "path": path,
        }
        self.send_response(300, data_header)
        response = self.get_response()
        if response["status_code"] == 242:
            print("mkdir the path[%s] successful!" % path)
        else:
            print("mkdir failed")

    def _rmdir(self, cmd_list, *args):
        path = cmd_list[1]
        data_header = {
            "action": "rmdir",
            "path": path,
        }
        self.send_response(300, data_header)
        response = self.get_response()
        if response["status_code"] == 241:
            print('the path is not exists')
            return
        elif response["status_code"] == 244:
            print("the path is not void, can not be deleted ")
            return
        elif response["status_code"] == 245:
            print("rm the path [%s]successful!" % path)
            return
        else:
            print("unknown error, get response: %s " % response)

    def _rm(self, cmd_list, *args):
        filename = cmd_list[1]
        data_header = {
            "action": "rm",
            "filename": filename,
        }
        self.send_response(300, data_header)
        response = self.get_response()
        if response['status_code'] == 247:
            print('server is deleting file[%s]' % filename)
        elif response["status_code"] == 246:
            print('the [%s] not exists' % filename)
            return
        else:
            print('try deleted the file[%s] failed' % filename)
            return
        response = self.get_response()
        if response["status_code"] == 245:
            print("delete file[%s] successful!rest space[%.2fM]" %
                  (filename, float(float(response["rest_space"]) / 1024 / 1024)))
        else:
            print('try deleted the file[%s] failed' % filename)

    def _cd(self, cmd_list, *args):
        cmd = cmd_list[1]
        data_header = {
            "action": "cd",
            "action_name": cmd,
        }
        self.send_response(300, data_header)
        response = self.get_response()
        status = response["status_code"]
        if status == 241:
            print("the path is not exists")
        elif status == 230:  # return  path
            print(response['path'])
        elif status == 231:
            for i in response['list']:
                print(i)

    def cmd_ls(self, data):
        data_header = {
            "action": "ls",
        }
        data_header.update(data)
        self.send_response(300, data_header)
        response = self.get_response()
        if response["status_code"] == 248:
            print("No file or path is  under this path")
        elif response["status_code"] == 249:
            ls = response["list"]
            for file in ls:
                print(file)

    def cmd_pwd(self, data):
        data_header = {
            "action": "pwd",
        }
        data_header.update(data)
        self.send_response(300, data_header)
        response = self.get_response()
        path = response["path"]
        print(path)

    def cmd_info(self, data):
        data["username"] = self.user
        data["action"] = "info"
        self.send_response(300, data)
        response = self.get_response()
        psd = response["password"]
        rest_space = response["rest_space"]
        info = """
                name: %s
                password: %s
                rest space: %s
        """.format() % (self.user, psd, rest_space)
        print(info)

    def help(self):
        attr = """
        help            Instructions to help
        -----------------------------------------
        info            Personal information
        -----------------------------------------
        ls              View current directory
        -----------------------------------------
        pwd             Check the current path
        -----------------------------------------
        cd 目录         Switch directory
        -----------------------------------------
        get filename    download the file
        -----------------------------------------
        put filename    upload the file
        ------------------------------------------
        md5             Use md5 in the back of
                        get/put filename
        ------------------------------------------
        mkdir name      create a directory
        ------------------------------------------
        rmdir name      delete the directory
        ------------------------------------------
        rm filename     delete the file
        ------------------------------------------
        exit            Exit
        ------------------------------------------
        q               Return to login interface
        ------------------------------------------
         """.format()
        print(attr)

    def _put(self, cmd_list):
        if cmd_list:
            base_filename = cmd_list[1]
            username = self.user
            file_dir = os.path.join(settings.PUT_FILE, username, base_filename)
            if os.path.isfile(file_dir):
                file_size = os.path.getsize(file_dir)
                data_header = {
                    "action": "put",
                    "filename": base_filename,
                    "file_size": file_size,
                    "md5": None,
                }
                if self.__md5_required(cmd_list):
                    md5_obj = hashlib.md5()
                    data_header["md5"] = True
                self.send_response(300, data_header)
                response = self.get_response()
                if response.get("status_code") == 260:  # 判断磁盘空间是否充足
                    received_size = 0
                    if response.get("bool_breakpoint"):  # 断点续传
                        temp_size = response["temp_size"]
                        print("file breakpoint is continued")
                    else:
                        temp_size = 0
                    rest_size = file_size - temp_size
                    progress = self.show_progress(rest_size)
                    progress.__next__()
                    f = open(file_dir, "rb")
                    f.seek(temp_size)
                    if data_header["md5"]:  # MD5校验
                        while received_size < rest_size:
                            for line in f:
                                md5_obj.update(line)
                                self.sock.send(line)
                                received_size += len(line)
                                try:
                                    progress.send(len(line))
                                except StopIteration as e:
                                    print("100%")
                                    break
                        print("file send done")
                        f.close()
                        md5_val = md5_obj.hexdigest()
                        self.send_response(259, {"md5": md5_val})
                        response = self.get_response()
                        rest_space = float(int(response["rest_space"]) / 1024 / 1024)
                        md5_from_server = response["status_code"]
                        print("your rest space: %.2fM" % rest_space)
                        if md5_from_server == 262:
                            print("File consistency check is successful")
                    else:  # 不校验MD5码
                        while received_size < rest_size:
                            line = f.read(8192)
                            self.sock.send(line)
                            received_size += len(line)
                            try:
                                progress.send(len(line))
                            except StopIteration:
                                print("100%")
                        print("file send done")
                        f.close()
                        response = self.get_response()
                        rest_space = response["rest_space"] / 1024 / 1024
                        print("your rest space: %.2fM" % rest_space)
                elif response["status_code"] == 261:
                    rest_space = float(int(response["rest_space"]) / 1024 / 1024)
                    print(f"{STATUS_CODE[261]} ,rest dual disk space {rest_space}M")
            else:
                print("the file not exists")
        else:
            print("invalid cmd format, e.g : {'action':'get', 'filename' : 'test.py', 'size':344}")

    def _get(self, cmd_list):
        if cmd_list:
            data_header = {
                "action": "get",
                "filename": cmd_list[1],
            }
            if self.__md5_required(cmd_list):
                data_header["md5"] = True
            self.send_response(300, data_header)
            response = self.get_response()
            if response["status_code"] == 257:
                if response["file_size"] == 0:
                    print("The file has been corrupted")
                    return
                base_filename = cmd_list[1].split("/")[-1]
                received_size = 0
                username = self.user
                file_dir = os.path.join(settings.GET_FILE, username, base_filename)
                if os.path.isfile(file_dir):
                    if os.path.getsize(file_dir) == response["file_size"]:
                        temp_size = 0
                    else:
                        temp_size = os.path.getsize(file_dir)
                        print("file breakpoint is continued")
                        data_header["temp_size"] = temp_size
                        data_header["bool_breakpoint"] = True
                else:
                    temp_size = 0
                self.send_response(267, data_header)
                file_obj = open(file_dir, "wb")
                file_obj.seek(temp_size)
                rest_size = int(response["file_size"] - temp_size)
                if self.__md5_required(cmd_list):
                    md5_obj = hashlib.md5()
                    progress = self.show_progress(rest_size)  # generator
                    progress.__next__()
                    while received_size < rest_size:
                        try:
                            if rest_size - received_size > 1024:
                                data = self.sock.recv(1024)
                            else:
                                last_size = rest_size - received_size
                                data = self.sock.recv(last_size)
                            received_size += len(data)
                            progress.send(len(data))
                        except StopIteration:
                            print("100%")
                        file_obj.write(data)
                        md5_obj.update(data)
                    else:
                        print("--file receive done--")
                        file_obj.close()
                        md5_val = md5_obj.hexdigest()
                        md5_form_server = self.get_response()
                        if md5_form_server["status_code"] == 259:
                            if md5_form_server["md5"] == md5_val:
                                print("%s File consistency check is successful!" % base_filename)
                else:
                    progress = self.show_progress(rest_size)
                    progress.__next__()
                    while received_size < rest_size:
                        try:
                            if rest_size - received_size > 1024:
                                data = self.sock.recv(1024)
                            else:
                                last_size = rest_size - received_size
                                data = self.sock.recv(last_size)
                            received_size += len(data)
                            progress.send(len(data))
                            file_obj.write(data)
                        except StopIteration:
                            print("100%")
                            break
                    print("--file receive done--")
                    file_obj.close()


def start():
    ftp = FTPClient()
    ftp.interactive()
