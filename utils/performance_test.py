# -*- coding: utf-8 -*-
import os
import subprocess
from config.conf import Global
from utils.logger import logger
from utils.common import get_env_conf
from locust import HttpUser, TaskSet, task, between
from utils.dirs import venv_bin_dir, report_locust_dir

LOCUST_CONF = get_env_conf(name="locust")


class WebsiteTask(TaskSet):
    _count_failure = 0
    _count_success = 0

    @task
    def request_api(self):
        uri = LOCUST_CONF.get("uri")
        method = LOCUST_CONF.get("method")
        response = self.client.request(method=method, url=uri)
        url = Global.constants.BASE_URL + uri
        if response.status_code != 200:
            WebsiteTask._count_failure += 1
            logger.error(f"failure ({method} {url}) [{str(WebsiteTask._count_failure).center(7)}]")
        else:
            WebsiteTask._count_success += 1
            logger.info(f"success ({method} {url}) [{str(WebsiteTask._count_success).center(7)}]")


class WebsiteUser(HttpUser):
    tasks = [WebsiteTask]
    wait_time = between(LOCUST_CONF.get("min_wait"), LOCUST_CONF.get("max_wait"))

    def on_start(self):
        self.client.headers.update(Global.constants.HEADERS)


def main():
    os.makedirs(report_locust_dir, exist_ok=True)
    locust_command = [
        os.path.abspath(os.path.join(venv_bin_dir, "locust")),
        f"--locustfile={__file__}",
        f"--host={Global.constants.BASE_URL}",
        f"""--csv={os.path.abspath(os.path.join(report_locust_dir, "locust_report"))}""",
        f"""--users={LOCUST_CONF.get("users")}""",
        f"""--spawn-rate={LOCUST_CONF.get("spawn_rate")}""",
        f"""--run-time={LOCUST_CONF.get("run_time")}""",
        f"""--html={os.path.abspath(os.path.join(report_locust_dir, "locust_report.html"))}""",
        "--headless",
        "--csv-full-history"
    ]

    if LOCUST_CONF.get("num_requests"):
        locust_command.extend(["-n", f"""{LOCUST_CONF.get("num_requests")}"""])

    command = " ".join(locust_command)
    logger.info(f"executed: {command}")
    process = subprocess.Popen(command, shell=True)
    process.wait()


if __name__ == "__main__":
    main()
