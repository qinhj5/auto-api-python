# API自动化测试项目模板

---

<br>

## 一、简介

这是一个支持执行API测试的基础用例模板，主要基于**pytest**测试框架进行构建，用例依靠**requests**模块进行请求。

<br>

## 二、特性

* 使用yaml文件管理环境配置
* 支持allure生成测试报告
* 支持数据驱动模式进行测试
* 支持mysql、tunnel和driver等连接以用于验证
* 支持pytest-xdist多进程加速
* 提供mail通知发送功能
* 提供Dockerfile以支持在自定义镜像中执行测试
* 提供Jenkinsfile以支持自动构建并运行测试项目
* 提供基于swagger一键生成api和testcases模版的脚本
* 提供基于swagger和log一键统计api覆盖情况的脚本

<br>

## 三、目录结构

```
APIAuto/
├── api/
│   ├── __init__.py
│   ├── base_api.py
│   └── google_search/
│       ├── __init__.py
│       └── google_search_api.py
├── config/
│   ├── __init__.py
│   ├── conf.py
│   └── conf_staging.yml
├── data/
│   └── keyword.csv
├── log/
├── report/
├── testcases/
│   ├── __init__.py
│   └── google_search/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_google_search_by_keyword.py
├── utils/
│   ├── __init__.py
│   ├── common.py
│   ├── decorators.py
│   ├── email_notification.py
│   ├── dirs.py
│   ├── enums.py
│   ├── logger.py
│   ├── clickhouse_connection.py
│   ├── redis_connection.py
│   ├── mysql_connection.py
│   ├── driver_client.py
│   ├── ssh_tunnel.py
│   ├── api_coverage.py
│   ├── xmind_parser.py
│   └── swagger_parser.py
├── conftest.py
├── Dockerfile
├── Jenkinsfile
├── main.py
├── pytest.ini
├── README.md
├── report.sh
└── requirements.txt
```

<br>

## 四、使用教程
（Ubuntu 20.04 LTS x64, Python3.7）

### 1.安装工具
```
  sudo apt update
  sudo apt install python3.7 virtualenv git default-jdk allure
```
### 2.克隆仓库
```
  git clone https://github.com/qinhj5/APIAuto.git
  cd APIAuto
```
### 3.安装依赖
```
  virtualenv --python=python3.7 venv
  source venv/bin/activate
  pip3.7 install -r requirements.txt
```
### 4.执行测试
```
  python3.7 ./main.py
```
### 5.生成报告
```
  ./report.sh
```

<br>

---

<p align="center">有错误或者改进的地方请各位积极指出！</p>

---
