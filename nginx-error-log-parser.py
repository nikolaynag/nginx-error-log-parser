#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple tool to get information out of nginx error_log
Author: Nikolay Nagorskiy
License: MIT
"""

import sys
import re
import datetime
import argparse

if sys.version_info < (3, 3):
    sys.stderr.write(
        "Sorry, this script could not run with Python {}.{}, "
        "Python 3.3 or newer required\n".format(*sys.version_info))
    sys.exit(1)


NGINX_ERROR_LOG_RE = re.compile(
    '([\d\/ \:]+) \[([a-z]+)\] (\d+)\#(\d+): \*?(\d+)? ?(.*)'
)
NGINX_ERROR_LOG_FIELDS = "time, level, pid, tid, cid, msg".split(", ")
NGINX_ERROR_MESSAGE_PARAMS_RE = re.compile(', ([a-z]+)\: ')
NGINX_FILENAME_RE = re.compile('(?:\/[^\/\s\"\']+)+')
NGINX_TIME_FORMAT = "%Y/%m/%d %H:%M:%S"


def parse_line(s):
    match = NGINX_ERROR_LOG_RE.fullmatch(s.strip())
    if match is None:
        sys.stdout.write(("No match for line: {}\n".format(s)))
    logItem = dict(zip(NGINX_ERROR_LOG_FIELDS, match.groups(0)))
    msgItems = NGINX_ERROR_MESSAGE_PARAMS_RE.split(logItem["msg"])
    if len(msgItems) > 1:
        logItem["params"] = dict(zip(msgItems[1::2], msgItems[2::2]))
        logItem["msg"] = msgItems[0]
    logItem["time"] = datetime.datetime.strptime(
        logItem["time"], NGINX_TIME_FORMAT
    )
    logItem["filenames"] = NGINX_FILENAME_RE.findall(logItem["msg"])
    logItem["msg"] = NGINX_FILENAME_RE.sub("{}", logItem["msg"])
    return logItem


def print_param_values(name):
    values = set()
    for line in sys.stdin:
        logItem = parse_line(line)
        if name in logItem.get("params", {}):
            values.add(logItem["params"][name])
    sys.stdout.write("\n".join(values) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        help="Count only messages for specified host",
        type=str,
        default=None
    )
    parser.add_argument(
        "command",
        help="Command to be executed",
        type=str,
        choices=["list-hosts", "list-servers", "error-stat"]
    )
    args = parser.parse_args()
    if args.command == "list-hosts":
        print_param_values("host")
        exit(0)
    if args.command == "list-servers":
        print_param_values("server")
        exit(0)
    messageStat = {}
    for line in sys.stdin:
        logItem = parse_line(line)
        if args.host is not None:
            if logItem.get("params", {}).get("host") != args.host:
                continue
        val = messageStat.get(
            logItem["msg"],
            dict(cnt=0, first=None, last=None)
        )
        val["cnt"] = val["cnt"] + 1
        val["last"] = logItem["time"]
        if val["first"] is None:
            val["first"] = logItem["time"]
        messageStat[logItem["msg"]] = val

    lineFormat = "{0!s:<20}\t{1!s:<20}\t{2!s:<10}\t{3}\n"
    columns = "First, Last, Count, Message".split(", ")
    sys.stdout.write(lineFormat.format(*columns))
    for msg, stat in messageStat.items():
        sys.stdout.write(lineFormat.format(
            stat["first"],
            stat["last"],
            stat["cnt"],
            msg
        ))

if __name__ == "__main__":
    main()
