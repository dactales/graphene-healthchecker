from . import app, health, envdump
from flask import jsonify, request
from datetime import datetime, timedelta

from prometheus_client import Gauge
from prometheus_client import make_wsgi_app
from werkzeug.wsgi import DispatcherMiddleware

from .utils import query, parse_time, format_time

DGP = dict()
dgp = {}


def get_dgp():
    global DGP
    DGP = query(app.config["witness_url"], ["database", "get_objects", [["2.1.0"]]])


def get_headblock():
    global DGP
    if DGP.get("head_block_number") is None:
        get_dgp()
    return DGP.get("head_block_number") or 0


def get_participation_rate():
    global DGP
    if DGP.get("recent_slots_filled") is None:
        get_dgp()
    return bin(int(DGP.get("recent_slots_filled"))).count("1") / 128


def get_connected_count():
    try:
        network_info = query(
            app.config["witness_url"], ["network_node", "get_info", []]
        )
        return network_info.get("connection_count") or 0
    except Exception:
        return 0


def check_blockchain_alive():
    try:
        get_dgp()
    except Exception:
        return False, "Blockchain not available"
    else:
        return True, DGP


def check_network_node_plugin():
    return True, query(app.config["witness_url"], ["network_node", "get_info", []])


def check_headblock_timestamp():
    global DGP
    try:
        if DGP is None:
            get_dgp()
        head_time = parse_time(DGP.get("time"))
    except Exception:
        return False, "Blockchain not available"
    else:
        if head_time < datetime.utcnow() + timedelta(
            seconds=30
        ) and head_time > datetime.utcnow() - timedelta(seconds=30):
            return True, "head_block_time ok"
        return False, f"head_block_time not ok: {head_time}"


def check_maintenance_block_in_future():
    global DGP
    try:
        if DGP is None:
            get_dgp()
    except Exception:
        return False, "Blockchain not available"
    else:
        maint_time = parse_time(DGP.get("next_maintenance_time"))
        if maint_time > datetime.utcnow() - timedelta(seconds=60):
            return True, "maintenance_block_time ok"
        else:
            return False, f"maintenance_block_time not ok: {maint_time}"


def check_participation_rate():
    global DGP
    try:
        if DGP is None:
            get_dgp()
    except Exception:
        return False, "Blockchain not available"
    else:
        if get_participation_rate() > 0.67:
            return True, f"Participation rate ok"
        else:
            return False, f"Participation rate too low"


def additional_data():
    return dict()


# Healthchecker
health.add_check(check_blockchain_alive)
# health.add_check(check_network_node_plugin)
health.add_check(check_headblock_timestamp)
health.add_check(check_maintenance_block_in_future)
health.add_check(check_participation_rate)
envdump.add_section("additional_data", additional_data)

app.add_url_rule("/-/health", "healthcheck", view_func=lambda: health.run())
app.add_url_rule("/", "healthcheckroot", view_func=lambda: health.run())
app.add_url_rule("/-/env", "environment", view_func=lambda: envdump.run())


# Prometheus exporeter
clean_endpoint = app.config["witness_url"].split("@")[-1]
BACKEND_HEADBLOCK_NUM = Gauge(
    "backend_headblock_number", "Backend Head Block Number", ["endpoint"]
)
BACKEND_PARTICIPATION_RATE = Gauge(
    "backend_participation_rate", "Block producer participation rate", ["endpoint"]
)
# BACKEND_CONNECTIONS_NUM = Gauge(
#    "backend_num_connections", "Backend Connections in P2P network", ["endpoint"]
# )
BACKEND_HEADBLOCK_NUM.labels(clean_endpoint).set_function(get_headblock)
BACKEND_PARTICIPATION_RATE.labels(clean_endpoint).set_function(get_participation_rate)
# BACKEND_CONNECTIONS_NUM.labels(clean_endpoint).set_function(get_connected_count)
# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})
