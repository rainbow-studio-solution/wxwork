# 企业微信 For Odoo 14.0

**不知道如何使用，请看帮助文件或者Wiki**

**目前在Wiki中，逐步完善使用文档**


## 项目地址
[![Github](http://img.shields.io/badge/14.0-Github-4cb648.svg?style=flat&colorA=8F8F8F)](https://github.com/rainbow-studio-solution/wxwork)
[![Gitee](http://img.shields.io/badge/14.0-Gitee-875A7B.svg?style=flat&colorA=8F8F8F)](https://gitee.com/rainbowstudio/wxwork)
[![WIKI](http://img.shields.io/badge/14.0-WIKI-875A7B.svg?style=flat&colorA=8F8F8F)](https://gitee.com/rainbowstudio/wxwork/wikis/pages/preview?sort_id=3640278&doc_id=424732)

## 项目介绍

### 基础模块

1. wxwork_l10n （企业微信-本地化模块）完成

2. wxwork_base （企业微信-基础模块）完成

3. wxwork_api （企业微信-API封装）完成

4. wxwork_widget（企业微信消息模板编辑器,密码显示等小部件），完成

### 多公司管理（企业微信企业互联功能） TODO

### 人力资源管理

1. wxwork_smart_hrm （企业微信-HR基本模块）完成

   >TODO：
      1. 待处理多公司（微信的互联企业功能）*

         *互联企业是企业微信提供的满足集团与子公司、企业与上下游供应商进行连接的功能。*

      2. 人事仪表盘

2. wxwork_hr_syncing （企业微信-同步功能）完成
   
   > 功能：

      1. 同步通讯录的部门、人员、标签到odoo的hr

      2. 从HR企业微信员工生成系统用户；定时同步任务。

      3. TODO；互联企业的同步功能
      
   > 故障处理：
   ```bash
    #1. 安装扩展
    pip install numpy==1.19.3 opencv-python==4.4.0.46 -i https://pypi.doubanio.com/simple
    或
    pip3 install numpy==1.19.3 opencv-python==4.4.0.46 -i https://pypi.doubanio.com/simple


    #2. ImportError: libGL.so.1: cannot open shared object file: No such file or directory.解决方案：
    apt-get install -y libgl1-mesa-dev   或  yum install mesa-libGL.x86_64
   ``` 
3. wxwork_hr_extension（企业微信-HR扩展模块）完成   

   > 功能：

      1. 将Odoo中的所有关于HR的模块菜单，按照实际的业务流程进行整合，进行HR的集中管理

4. wxwork_attendance（拉取考勤记录），开展中

   > 功能：

      1. 拉取企业微信考勤记录

5. 企业微信排班管理（计划中）

6. 身份证阅读器对接（计划中）

7. 健康证管理（计划中）

### 登录验证

1. wxwork_auth_oauth （企业微信应用内自动登录，企业微信应用外扫码登录），完成

   > 功能：
      1. 网页扫码登录
      2. 应用内一键登录
      3. 用户消息模板
      
   > 故障处理：
   ```bash
   #若出现链接失败的提示或其他的失败提示，尝试修改odoo.conf 以下参数，我是直接放大10倍
   db_maxconn = 640
   limit_time_cpu = 600
   limit_time_real = 1200 
   ```

### 素材管理

1. wxwork_material （企业素材管理），基本完成

   > 功能：

      1. 上传临时素材和永久图片

      2. 临时素材可以用于发送企业微信消息

      3. 永久图片仅能用于图文消息正文中的图片展示，或者给客户发送欢迎语等；若用于非企业微信环境下的页面，图片将被屏蔽。

   > 安装前置需求：
   ```bash
   # libav
   apt-get install libav-tools libavcodec-extra

   # ffmpeg
   apt-get install ffmpeg libavcodec-extra

   # pip
   pip install ffmpy pydub requests_toolbelt
   ```

### 企业微信消息推送

1. wxwork_message（企业微信消息推送），开展中

2. mass_mailing_wxwork_message（企业微信群发消息），开展中

3. 互联企业的消息发送，TODO


### 企业微信日历（计划中）

### 企业微信流程审批（计划中）

# 帮助

## 安装

[![Install](http://img.shields.io/badge/14.0-安装-875A7B.svg?style=flat&colorA=8F8F8F)](doc/install/index.md)

## 故障处理

[![Help](http://img.shields.io/badge/14.0-帮助-4cb648.svg?style=flat&colorA=8F8F8F)](doc/help/index.md)

## CentOS问题

[![Help](http://img.shields.io/badge/14.0-CentOS-4cb648.svg?style=flat&colorA=8F8F8F)](doc/centos_index.md)



# QQ群

>若有使用问题，可以加入QQ群，寻求本人帮助

![QQ群](doc/img/QQ群二维码.png)

# Odoo商城付费模块

<a href="https://apps.odoo.com/apps/modules/browse?search=RStudio" target="_blank">应用</a>
<a href="https://apps.odoo.com/apps/themes/browse?search=RStudio" target="_blank">主题</a>


如果我的作品能对您有所帮助，能力范围内，请不要介意去<a href="https://gitee.com/rainbowstudio/wxwork">Gitee</a>点击“捐赠”按钮，或者点个⭐，一切随意，开源不易，请多支持。
