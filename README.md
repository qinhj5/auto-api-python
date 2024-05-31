# API自动化测试项目模板

---

<br/>

## 一、简介

这是一个支持执行API测试的基础用例模板，主要基于**pytest**测试框架进行构建，用例依靠**requests**模块进行请求。

<br/>

## 二、特性

* 使用yaml文件管理环境配置
* 支持allure生成测试报告
* 支持数据驱动模式进行测试
* 支持mysql、tunnel和driver等连接以用于验证
* 支持pytest-xdist多进程加速
* 提供mail通知发送功能
* 提供Dockerfile以支持在自定义镜像中执行测试
* 提供pipeline script以支持Jenkins自动构建并运行测试
* 提供基于swagger一键生成api和testcases模版的脚本
* 提供基于swagger和log一键统计api覆盖情况的脚本
* ...

<br/>

## 三、目录结构

```
auto-api-python/
├── api/
│   ├── __init__.py
│   ├── base_api.py
│   └── google_search/
│       ├── __init__.py
│       └── google_search_api.py
├── config/
│   ├── __init__.py
│   ├── conf.py
│   ├── conf_ext.yaml
│   ├── conf_test.yaml
│   ├── cred_oauth_client.json
│   └── cred_service_account.json
├── data/
│   └── google_search/
│       └── keywords.csv
├── log/
├── report/
├── testcases/
│   ├── __init__.py
│   └── google_search/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_get_search.py
├── utils/
│   ├── __init__.py
│   ├── api_coverage.py
│   ├── chat_bot.py
│   ├── chrome_browser.py
│   ├── clickhouse_connection.py
│   ├── common.py
│   ├── cryptor.py
│   ├── decorators.py
│   ├── dirs.py
│   ├── driver_shell.py
│   ├── email_notification.py
│   ├── enums.py
│   ├── formatter.py
│   ├── forwarder_setting.py
│   ├── google_drive.py
│   ├── google_email.py
│   ├── google_sheet.py
│   ├── kafka_client.py
│   ├── logger.py
│   ├── message_notification.py
│   ├── mysql_connection.py
│   ├── performance_test.py
│   ├── redis_connection.py
│   ├── swagger_parser.py
│   ├── swagger_diff.py
│   ├── tunnel_shell.py
│   └── xmind_parser.py
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── allure.sh
├── conftest.py
├── Dockerfile
├── Jenkinsfile
├── main.py
├── pytest.ini
├── README.md
└── requirements.txt
```

<br/>

## 四、使用教程
（Ubuntu 20.04 LTS x64, Python3.8）

### 1.安装工具
```
  sudo apt update
  sudo apt install -y python3.8 virtualenv git default-jdk
```
### 2.克隆仓库
```
  git clone https://github.com/qinhj5/auto-api-python.git
  cd auto-api-python
```
### 3.安装依赖
```
  virtualenv --python=python3.8 venv
  source venv/bin/activate
  pip3.8 install -r requirements.txt
```
### 4.执行测试
```
  python3.8 main.py
```

<br/>

---

<p align="center">有错误或者改进的地方请各位积极指出！</p>
<p align="center"><a href="https://github.com/qinhj5">GitHub</a> | <a href="https://blog.csdn.net/embracestar">CSDN</a></p>

---
