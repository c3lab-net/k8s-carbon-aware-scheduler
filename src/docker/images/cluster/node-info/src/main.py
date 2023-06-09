#!/usr/bin/env python3

import csv
from dataclasses import dataclass
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


@dataclass
class NodeInfo:
    region: str
    zone: str


def load_nodes_info() -> dict[str, NodeInfo]:
    d_node_info = dict()
    with open("nodes.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            nodename = row[0]
            region = row[1]
            zone = row[2]
            if not (nodename and region and zone):
                continue
            d_node_info[nodename] = NodeInfo(region, zone)
    return d_node_info


ALL_NODE_INFO = load_nodes_info()


app = FastAPI()

@app.get("/{nodename}")
def get_node_info(nodename: str):
    if nodename in ALL_NODE_INFO:
        node_info = ALL_NODE_INFO[nodename]
        return {
            "region": node_info.region,
            "zone": node_info.zone
        }
    else:
        return {}

@app.get("/{nodename}/region", response_class=PlainTextResponse)
def get_node_region(nodename: str):
    if nodename in ALL_NODE_INFO:
        node_info = ALL_NODE_INFO[nodename]
        return node_info.region
    else:
        return None


@app.get("/{nodename}/zone", response_class=PlainTextResponse)
def get_node_zone(nodename: str):
    if nodename in ALL_NODE_INFO:
        node_info = ALL_NODE_INFO[nodename]
        return node_info.zone
    else:
        return None

