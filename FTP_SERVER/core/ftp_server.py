#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__:JasonLIN
import socketserver
import json
import struct
from conf import settings
import hashlib
import os
import configparser
from  core import logs

STATUS_CODE = {
    250 : "invalid cmd format",
    251: "invalid cmd",
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
    245: "file has deleted successful",
    246: "the file is not exists",
    247: "the file is deleting, please wait...",
    248: "The file is empty under this path",
    249: "The file is not empty under this path",
    230: "return path",
    231: "return path or file",
    401: "exit"
}
config = configparser.ConfigParser()
config.read(settings.ACCOUNT_FILE, encoding="utf-8")


class FTPHandler(socketserver.BaseRequestHandler):
    def handle(self):  # the name must be handle
        while True:
            self.data = self.get_response()
            if self.data is None:
                break
            if self.data["status_code"] == 401:  # 401：退出
                print(" --exit-- ")
                break
            elif not self.data:
                print("client closed...")
                break
            elif self.data.get("action"):
                if hasattr(self,"cmd_%s" % self.data.get("action")):
                    func = getattr(self,"cmd_%s" % self.data.get("action"))
                    if self.data.get("cmd"): # "cmd": 单指令，如pwd
                        func()
                    else:  # cd ..
                        func(self.data)
                else:
                    print("invalid cmd")
                    self.send_response(251)
            else:
                print("invalid cmd format")
                self.send_response(250)

    def cmd_path_join(self):
        """cmd 文件路径拼接"""
        self.cmd_path = self.path.split(self.home_path)[-1]
        return self.cmd_path

    def log_info(self, msg, **kwargs):
        """日志记录"""
        try:
            info = "user[%s] [%s]" %(self.user, msg)
            return info
        except AttributeError:
            info = msg
            return info

    def send_response(self, status, data=None):
        """发送报头"""
        response = {"status_code": status, "status_msg": STATUS_CODE[status]}
        if data:
            response.update(data)
            response["status_code"] = status
        bytes_response = bytes(json.dumps(response), encoding="utf-8")
        head_len = struct.pack("i", len(bytes_response))
        self.request.send(head_len)
        self.request.send(bytes_response)

    def get_response(self):
        """得到客户端回复的结果"""
        head_len_obj = self.request.recv(4)
        if head_len_obj is None:
            return
        head_len = struct.unpack("i", head_len_obj)[0]
        response = self.request.recv(head_len)
        response = json.loads(response)
        return response

    def cmd_info(self, *args):
        password = config.get(self.user, "password")
        rest_space = config.get(self.user, "rest space")
        data = {"password": password, "rest_space": rest_space}
        self.send_response(300, data)

    def cmd_auth(self, *args, **kwargs):
        data = args[0]
        if data.get("username") is None or data.get("password") is None:
            self.send_response(252)  # 252：用户数据格式不对
        user = self.authentification(data.get("username"), data.get("password"))
        if user is None:
            info = self.log_info("login error")
            logs.login_log(info)
            self.send_response(253)  # 253：用户名或者密码错误
        else:
            self.send_response(254)  # 255：登录认证通过
            info = self.log_info("login successful")
            logs.login_log(info)

    def authentification(self, username, password):
        """
        登录认证，
        通过返回用户名
        不通过返回None
        """
        if username in config.sections():
            _password = config[username]["Password"].strip()
            if _password == password:
                print("[%s] loginning..." % username)
                config[username]["Username"] = username
                self.user = username
                self.home_path = os.path.join(settings.USER_HOME, self.user)   #用户家目录
                self.path = os.path.join(settings.USER_HOME, self.user)  # 当前目录
                self.cmd_path = self.cmd_path_join()  # 相对路径
                return config[username]

    def show_progress(self, total):
        """进度条"""
        receive_size = 0
        current_present = 0
        while receive_size < total:
            if int((receive_size/total) * 100) > current_present:
                print("#", end="", flush=True)
                current_present = int((receive_size/total) * 100)
            new_size = yield
            receive_size += new_size

    def disk_size(self):
        """获取用户磁盘空间"""
        user_size = config.get(self.user, "rest space")# 字节
        user_size = int(user_size)
        return  user_size

    def set_user_size(self, file_size, user):
        """设置用户磁盘空间"""
        user_size = int(self.disk_size())
        user_size -= int(file_size)
        config.set(user, "rest space:", str(user_size))
        info = self.log_info("update %s space %d" % (user, user_size))
        logs.operate_log(info, "debug")
        self.user_size = user_size

    def cmd_pwd(self):
        """pwd命令"""
        self.cmd_path = self.cmd_path_join()
        info = self.log_info("view relative path")
        logs.operate_log(info, "debug")
        self.send_path(300, self.cmd_path)

    def cmd_ls(self):
        """ls命令"""
        print("ls path:", self.path)
        data_header = {"list": os.listdir(self.path)}
        info = self.log_info("use ls command")
        logs.operate_log(info, "debug")
        self.send_response(249, data_header)  # The file is  not empty under this path

    def send_path(self,status, path):
        """
        send path to client
        :param status: status code
        :param path: path currently
        :return:
        """
        data_header = {'path': path}
        self.send_response(status, data_header)

    def cmd_cd(self, *args):
        cmd = args[0]["action_name"]
        if cmd == "..":
            info = self.log_info("use cd .. command")
            logs.operate_log(info, "debug")
            if self.path == self.home_path:
                self.send_path(230, self.cmd_path)
                return
            else:
                self.path = os.path.dirname(self.path)
                self.send_path(230, self.cmd_path)
                return
        elif cmd == "../..":
            info = self.log_info("use cd ../.. command")
            logs.operate_log(info, "debug")
            home_path = "/"
            self.send_path(230, home_path)
            return
        else:
            path = os.path.join(self.path, cmd)
            info = self.log_info("cd %s" % path)
            logs.operate_log(info, "debug")
            if os.path.isdir(path):
                self.path = path
            else:
                self.log_info("[%s]  not exists" % path)
                logs.operate_log(info, "error")
                self.send_response(241)
                return
            file_list = os.listdir(self.path)
            if file_list == []:
                data = {"path": self.cmd_path}
                self.send_response(230, data)
            else:
                data = {"list": file_list}
                self.send_response(231, data)

    def cmd_mkdir(self, *args, **kwargs):
        """
        make dir
        :param args:
        :param kwargs:
        :return:
        """
        data = args[0]
        if data["path"]:
            abspath = os.path.join(self.path, data["path"])
            if os.path.isdir(abspath):
                info = self.log_info("%s is not exists")
                logs.operate_log(info, "error")
                self.send_response(243)
                return
            os.mkdir(abspath)
            info = self.log_info("make dir %s sucessful" % abspath)
            logs.operate_log(info, "debug")
            self.send_response(242)
        else:
            info = self.log_info.error("make dir %s failed" % data["path"])
            logs.operate_log(info, "error")
            self.send_response(251)

    def cmd_rm(self, *args, **kwargs):
        """
        remove file
        :param args:
        :param kwargs:
        :return:
        """
        data = args[0]
        if data.get("filename"):
            filename = os.path.join(self.path, data["filename"])
            if os.path.isfile(filename):
                self.send_response(247, data)
                file_size = os.path.getsize(filename)
                os.remove(filename)
                self.set_user_size(file_size, self.user)
                data["rest_space"] = self.user_size
                info = self.log_info("remove %s successful" % filename)
                logs.operate_log(info, "debug")
                self.send_response(245, data)
                return
            else:
                info = self.log_info("remove %s failed" % filename)
                logs.operate_log(info, "error")
                self.send_response(246)  # the file  not exists
                return
        else:
            info = self.log_info("invalid cmd")
            logs.operate_log(info, "error")
            self.send_response(251)  # invalid cmd
            return

    def cmd_rmdir(self, *args, **kwargs):
        """
        remove dir
        :param args:
        :param kwargs:
        :return:
        """
        data = args[0]
        if data.get("path"):
            abspath = os.path.join(self.path, data["path"])
            if os.path.isdir(abspath):
                if os.listdir(abspath):
                    info = self.log_info("path is not void")
                    logs.operate_log(info, "error")
                    self.send_response(244)
                    return
                else:
                    os.rmdir(abspath)
                    info = self.log_info("delete [%s] successful!" % abspath)
                    logs.operate_log(info, "debug")
                    self.send_response(245)
                    return
            else:
                info = self.log_info("path is not exists")
                logs.operate_log(info, "debug")
                self.send_response(241)
                return
        else:
            info = self.log_info("invalid cmd")
            logs.operate_log(info, "error")
            self.send_response(251)

    def cmd_put(self, *args, **kwargs):
        """上传"""
        data_header = args[0]
        if data_header.get("filename"):
            pass
        else:
            info = self.log_info("invalid cmd")
            logs.operate_log(info, "error")
            self.send_response(255)
            return
        file_abs_path = os.path.join(self.path, data_header["filename"])
        rest_space = self.disk_size()
        file_size = int(data_header["file_size"])
        if int(rest_space) > file_size:
            info = self.log_info("adequate disk space, rest space %.2fM" % (rest_space/1024/1024))
            logs.operate_log(info, "debug")
            if os.path.isfile(file_abs_path):
                temp_size = os.path.getsize(file_abs_path)
                if temp_size == file_size:
                    temp_size = 0
                data_header["temp_size"] = temp_size
                data_header["bool_breakpoint"] = True
                info = self.log_info("file breakpoint is continued")
                logs.operate_log(info, "debug")
            else:
                temp_size = 0
            self.send_response(260, data_header)
            received_size = 0
            file_obj = open(file_abs_path, "wb")
            file_obj.seek(temp_size)
            rest_size = file_size - temp_size
            if data_header.get("md5"):
                md5_obj = hashlib.md5()
                while received_size < rest_size:
                    if int(rest_size - received_size) < 1024:
                        data = self.request.recv(1024)
                    else:
                        last_size = int(rest_size - received_size)
                        data = self.request.recv(last_size)
                    received_size += len(data)
                    md5_obj.update(data)
                    file_obj.write(data)
                info = self.log_info("--file recv done--")
                logs.operate_log(info, "debug")
                self.set_user_size(file_size, self.user)
                file_obj.close()
                md5_val = md5_obj.hexdigest()
                response = self.get_response()
                md5_from_client = response["md5"]
                if response["status_code"] == 259:
                    if md5_from_client == md5_val:
                        info = self.log_info("File consistency check is successful")
                        logs.operate_log(info, "debug")
                        data_header = {"rest_space": self.user_size}
                        self.send_response(262, data_header)
                        return
            else:
                while received_size < rest_size:
                    if int(rest_size - received_size) < 1024:
                        data = self.request.recv(1024)
                    else:
                        last_size = rest_size - received_size
                        data = self.request.recv(last_size)
                    received_size += len(data)
                    file_obj.write(data)
                info = self.log_info("--file recv done--")
                logs.operate_log(info, "debug")
                self.set_user_size(file_size, self.user)
                file_obj.close()
                data_header = {"rest_space": self.user_size}
                self.send_response(300, data_header)
                return
        else:
            data_header["rest_space"] = rest_space
            info = self.log_info("insufficient disk space")
            logs.operate_log(info, "error")
            self.send_response(261, data_header)
            return

    def cmd_get(self, *args, **kwargs):
        """下载"""
        data = args[0]
        if data.get("filename") is None:  # 文件名为空
            info = self.log_info("invalid cmd")
            logs.operate_log(info,"error")
            self.send_response(255)
            return
        file_abs_path = os.path.join(self.path, data["filename"])
        if os.path.isfile(file_abs_path):
            file_size = os.path.getsize(file_abs_path)
            self.send_response(257, data={"file_size": file_size})
            response = self.get_response()
            if response.get("bool_breakpoint"):
                temp_size = response["temp_size"]
                info = self.log_info("file breakpoint is continued")
                logs.operate_log(info, "debug")
            else:
                temp_size = 0
            rest_size = file_size - temp_size
            f = open(file_abs_path, "rb")
            f.seek(temp_size)
            send_size = 0
            if data.get("md5"):
                md5_obj = hashlib.md5()
                while send_size < rest_size:
                    for line in f:
                        md5_obj.update(line)
                        self.request.send(line)
                        send_size += len(line)
                else:
                    f.close()
                    info = self.log_info("__send file done__")
                    logs.operate_log(info, "debug")
                    md5_val = md5_obj.hexdigest()
                    self.send_response(259, {"md5": md5_val})
            else:
                while send_size < rest_size:
                    for line in f:
                        self.request.send(line)
                        send_size += len(line)
                else:
                    f.close()
                    info = self.log_info("__send file done__")
                    logs.operate_log(info, "debug")
        else:
            info = self.log_info("%s is not exists" % file_abs_path)
            logs.operate_log(info, "error")
            self.send_response(256)
