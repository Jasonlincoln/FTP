
## 1.需求
1. 用户加密认证
2. 多用户同时登陆
3. 每个用户有自己的家目录且只能访问自己的家目录
4. 对用户进行磁盘配额、不同用户配额可不同
5. 用户可以登陆server后，可切换目录
6. 查看当前目录下文件
7. 上传下载文件，保证文件一致性
8. 传输过程中现实进度条
9. 支持断点续传

## 2.程序目录结构
```
FTP
    ├── FTP_CLIENT
    │   ├── bin
    │   │   ├── client_start.py  客户端启动程序
    │   │   
    │   ├── conf
    │   │   
    │   │   └── settings.py  客户端配置文件
    │   ├── core             
    │   │   ├── ftp_client.py  客户端主程序 
    │   │
    │   ├── down  客户端下载文件夹
    │   │
    │   ├
    │   └── upload  客户端上传文件夹
    │       
    ├── FTP_SERVER
    │   ├── bin 
    │   │   ├
    │   │   └── server_start.py  服务端启动程序
    │   ├── conf
    │   │   ├── accounts.txt     用户信息文件
    │   │   
    │   │   └── settings.py      服务端配置文件
    │   ├── core                 服务端核心程序
    │   │   ├── ftp_server.py    服务端程序
    │   │   ├
    │   │   ├── logs.py          日志程序 
    │   │   ├── main.py          服务端主程序
    │   │   └──
    │   ├── home                 用户家目录
    │   │   ├── 
    │   ├
    │   └── log                 日志文件夹
    │       ├
    │       ├── login.log       登陆日志
    │       └── operate.log     操作日志
    
    
```
## 3.测试


### 3.1测试步骤
可以自行更改ip测试，FTP_SERVER/settings/中更改相关配置文件

服务端命令：
```
start       启动服务端
create      创建新用户
rm          删除用户
setup       修改用户信息(paasword, Quotation, rest space)
view        查看用户信息
```
启动服务端：
```
python /FTP/FTP_SERVER/bin/目录下 server_start.py start
启动其他命令方法和start方法相同
启动客户端前先启动服务端即(python server_start.py start)

python server_start.py  create  创建新用户
python server_start.py  setup   修改用户信息
任何界面输入q或者exit 退出
```
客户端命令：
```
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
        
```
启动客户端：
```
以本地端，端口9999为例，-s后面+服务端ip, -P 为端口 （命令区分大小写）
启动文件在 FTP/FTP_CLIENT/bin/下，python client_start.py -s "127.0.0.1" -P "9999"
新创建用户需要手动在客户端FTP/FTP_CLIENT/down和FTP/FTP_CLIENT/unload创建以用户名为文件名的空文件夹
```
具体操作可以按提示进行。例如:

输入用户名：test，密码：123  登录

put/get test.pdf md5 上传/下载文件(md5校验)

put/get test.pdf  上传/下载文件

rmdir 删除文件夹，不为空不能删除

更多例子参照客户端命令

