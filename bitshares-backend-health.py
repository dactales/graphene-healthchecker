#!/usr/bin/env python

import click
import flask
import sys
import requests
import datetime
from flask import Flask
app = Flask(__name__)


def parse_time(block_time):
    timeFormat = '%Y-%m-%dT%H:%M:%S'
    return datetime.datetime.strptime(block_time, timeFormat)


app.config["test_url"] = None


@app.route('/')
def status():
    try:
        req = requests.post(
            app.config["test_url"],
            json={
                "method": "call",
                "params": [
                    "database",
                    "get_objects",
                    [["2.1.0"]]],
                "jsonrpc": "2.0",
                "id": 1
            },
            timeout=2
        )
    except Exception as e:
        return "Node timed out: {}".format(str(e)), 502

    if req.status_code != 200:
        return "Node returns an error core {}".format(
            req.status_code), 502

    data = req.json()

    if "result" not in data:
        return "Node does not return a result but {}".format(
            data), 502

    result = data.get("result")
    time = parse_time(result[0]["time"])
    maintenance = parse_time(result[0]["next_maintenance_time"])

    # Test the current blockchain time
    test1 = (
        time < datetime.datetime.utcnow() +
        datetime.timedelta(seconds=60)
    )

    # Test the next maintenance interval
    test2 = (
        maintenance > datetime.datetime.utcnow() -
        datetime.timedelta(seconds=10)
    )

    if test1 and test2:
        return "Node is responding, blockchain is up to date", 200
    else:
        return "Node is responding, but blockchain is {delta.days} days behind".format(
            delta=(datetime.datetime.utcnow() - time)), 502


@click.command()
@click.argument("url")
@click.option("--listen", default=8088)
def main(url, listen):
    app.config["test_url"] = url
    app.run(port=listen, host="0.0.0.0")


if __name__ == "__main__":
    main()
