# -*- coding: utf-8 -*-
import argparse
import os
import sys
import traceback

import pytest

project_dir = os.path.dirname(__file__)
sys.path.append(project_dir)


def exe_test(
    cases_dir="testcases",
    slowest_cases=100,
    output_mode="-s",
    process_num=3,
    generate_report=False,
    marker=None,
    reruns=0,
):
    testcase_dir = os.path.abspath(os.path.join(project_dir, cases_dir))
    args = [testcase_dir]

    args.extend(["--alluredir", report_raw_dir])

    args.append(f"-{output_mode}")

    args.extend(["--durations", f"{slowest_cases}"])

    if process_num:
        args.extend(
            ["-n", f"{process_num}", "--dist", "loadfile", "--reruns", f"{reruns}"]
        )

    if marker is not None:
        args.extend(["-m", marker])

    logger.info(f"""pytest args: {" ".join(args)}""")

    pytest.main(args)

    if generate_report:
        command = f"allure generate {report_raw_dir} -o {report_html_dir} --clean"
        execute_local_command(command)


def get_parse_args():
    parser = argparse.ArgumentParser(description="run testcases")

    parser.add_argument(
        "--cases_dir",
        type=str,
        default="testcases",
        help="Directory of test cases",
    )

    parser.add_argument(
        "--slowest_cases",
        type=int,
        default=100,
        help="Number of slowest cases to show",
    )

    parser.add_argument(
        "--output_mode",
        type=str,
        default="s",
        help="Output mode (e.g. v or s or q)",
    )

    parser.add_argument(
        "--process_num",
        type=int,
        default=3,
        help="Number of process to use",
    )

    parser.add_argument(
        "--generate_report",
        action="store_true",
        help="Whether to generate a html report",
    )

    parser.add_argument(
        "--env",
        type=str,
        default="test",
        help="Environment (e.g. test or staging or production)",
    )

    parser.add_argument(
        "--marker",
        type=str,
        default=None,
        help="Run testcases with the specified marker",
    )

    parser.add_argument(
        "--reruns",
        type=int,
        default=0,
        help="Rerun failed testcases",
    )

    parser.add_argument(
        "--key",
        type=str,
        default=None,
        help="The key to decrypt config files",
    )

    return parser.parse_args()


def pre_action():
    clean_logs_and_reports()


def post_action():
    send_email()
    send_message()


def main():
    pre_action()

    args = get_parse_args()

    os.environ["ENV"] = args.env
    logger.info(f"current env is {args.env}")

    if args.key:
        os.environ["KEY"] = args.key
        decrypt_config()

    exe_test(
        cases_dir=args.cases_dir,
        slowest_cases=args.slowest_cases,
        output_mode=args.output_mode,
        process_num=args.process_num,
        generate_report=args.generate_report,
        marker=args.marker,
        reruns=args.reruns,
    )


if __name__ == "__main__":
    from utils.common import clean_logs_and_reports, execute_local_command
    from utils.cryptor import decrypt_config
    from utils.dirs import report_html_dir, report_raw_dir
    from utils.email_notification import send_email
    from utils.logger import logger
    from utils.message_notification import send_message

    try:
        main()  # test
    except Exception as e:
        logger.error(f"{e}\n{traceback.format_exc()}")
