# -*- coding: utf-8 -*-
import os
import sys
import pytest
import argparse

project_dir = os.path.dirname(__file__)
sys.path.append(project_dir)


def exe_test(cases_dir="testcases",
             slowest_cases=100,
             output_mode="-s",
             process_num=3,
             generate_report=False,
             marker=None,
             reruns=0
             ):

    testcase_dir = os.path.abspath(os.path.join(project_dir, cases_dir))
    args = [testcase_dir]

    args.extend(["--alluredir", report_raw_dir])

    args.append(f"-{output_mode}")

    args.extend(["--durations", f"{slowest_cases}"])

    if process_num:
        args.extend(["-n", f"{process_num}", "--dist", "loadfile", "--reruns", f"{reruns}"])

    if marker is not None:
        args.extend(["-m", marker])

    logger.info(f"""pytest args: {" ".join(args)}""")

    pytest.main(args)

    if generate_report:
        cmd = f"allure generate {report_raw_dir} -o {report_html_dir} --clean"
        os.system(cmd)


def get_parse_args():
    parser = argparse.ArgumentParser(
        description="run testcases"
    )

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

    return parser.parse_args()


def pre_action():
    clean_logs_and_reports()


def post_action():
    send_email()


def main():
    
    pre_action()
    
    args = get_parse_args()
    set_env(args.env)
    logger.info(f"current env is {args.env}.")

    exe_test(cases_dir=args.cases_dir,
             slowest_cases=args.slowest_cases,
             output_mode=args.output_mode,
             process_num=args.process_num,
             generate_report=args.generate_report,
             marker=args.marker,
             reruns=args.reruns,
             )


if __name__ == "__main__":
    from utils.logger import logger
    from utils.email_notification import send_email
    from utils.dirs import report_raw_dir, report_html_dir
    from utils.common import set_env, clean_logs_and_reports
    main()
