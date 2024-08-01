# -*- coding: utf-8 -*-
import os
import traceback

from locust import HttpUser, TaskSet, between, events, task

from config.conf import Global
from utils.common import execute_local_command, get_env_conf
from utils.dirs import report_locust_dir, venv_bin_dir
from utils.logger import logger

LOCUST_CONF = get_env_conf(name="locust")


@events.quitting.add_listener
def _(environment):
    if environment.stats.total.fail_ratio > 0.01:
        logger.error("failed due to failure ratio > 1%")
        environment.process_exit_code = 1
    elif environment.stats.total.avg_response_time > 200:
        logger.error("failed due to average response time ratio > 200 ms")
        environment.process_exit_code = 1
    elif environment.stats.total.get_response_time_percentile(0.95) > 800:
        logger.error("failed due to 95th percentile response time > 800 ms")
        environment.process_exit_code = 1
    else:
        environment.process_exit_code = 0


class GetAboutTask(TaskSet):
    _count_failure = 0
    _count_success = 0

    @task
    def get_about(self):
        uri = LOCUST_CONF.get("uri")
        method = LOCUST_CONF.get("method")
        with self.client.request(
            method=method, url=uri, catch_response=True
        ) as response:
            response.request_meta["name"] = "get_about"
            if response.status_code != 200:
                GetAboutTask._count_failure += 1
                response.failure(
                    f"failure ({method} {uri}) [{str(GetAboutTask._count_failure).center(7)}]"
                )
                logger.warning(
                    f"failure ({method} {uri}) [{str(GetAboutTask._count_failure).center(7)}]"
                )
            else:
                GetAboutTask._count_success += 1
                logger.info(
                    f"success ({method} {uri}) [{str(GetAboutTask._count_success).center(7)}]"
                )


class TestUser(HttpUser):
    tasks = {GetAboutTask: 1}
    wait_time = between(LOCUST_CONF.get("min_wait"), LOCUST_CONF.get("max_wait"))

    def on_start(self):
        self.client.headers.update(Global.CONSTANTS.HEADERS)


def main():
    os.makedirs(report_locust_dir, exist_ok=True)
    locust_bin_dir = os.path.abspath(os.path.join(venv_bin_dir, "locust"))
    locust_command = [
        locust_bin_dir,
        "--headless",
        f"--locustfile={__file__}",
        f"--host={Global.CONSTANTS.BASE_URL}",
        f"""--users={LOCUST_CONF.get("users")}""",
        f"""--spawn-rate={LOCUST_CONF.get("spawn_rate")}""",
        f"""--run-time={LOCUST_CONF.get("run_time")}""",
        f"""--html={os.path.abspath(os.path.join(report_locust_dir, "locust_report.html"))}""",
        f"""--csv={os.path.abspath(os.path.join(report_locust_dir, "locust_report"))}""",
        "--csv-full-history",
    ]

    logger.info(f"{locust_bin_dir} running...")
    command = " ".join(locust_command)
    execute_local_command(command)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
