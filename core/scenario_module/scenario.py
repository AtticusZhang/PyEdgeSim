#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 11:14
# @Author  : zhangqi
# @File    : scenario.py
# @Software: PyCharm
import math
import random

import networkx as nx

from typing import List, Dict

from core.simsetting_module.simsetting import simSetting, DEVICE_NAMES, EDGE_NAMES, APP_TYPES
from core.scenario_module.node import Node
from core.scenario_module.edge import Edge
from core.scenario_module.device import Device
from core.scenario_module.link import Link
from core.scenario_module.offload_link import OffloadLink
from core.scenario_module.schedule_link import ScheduleLink
from core.task_generator_module.task import Task

scenario_setting = simSetting.scenario_setting


class Scenario:

    def __init__(self):
        self._graph = nx.MultiDiGraph()
        self._init_node()
        self._init_link()

    def get_all_edge_deployed_info(self):
        all_edge_deployed_info = {
            edge_name: {
                app_type: 1 if app_type in self.get_edge(edge_name).deployed_app
                else 0
                for app_type in APP_TYPES
            }
            for edge_name in EDGE_NAMES
        }

        return all_edge_deployed_info

    def get_all_edge_queue_info(self):
        return {edge_name: self.get_edge_queue_info(edge_name) for edge_name in EDGE_NAMES}

    def get_edge_queue_info(self, edge_name) -> Dict[str, float]:
        self.get_edge(edge_name)
        all_task_queue: Dict[str, List[Task]] = self.get_edge(edge_name).get_all_task_queue()

        edge_queue_info = {app_type: 0 for app_type in APP_TYPES}

        for app_type, task_queue in all_task_queue.items():
            for task in task_queue:
                edge_queue_info[app_type] += task.get_process_data_size()

        return edge_queue_info

    def get_schedule_rate_between_edges(self):
        schedule_rate_info = {
            src_edge_name: {
                dst_edge_name: math.inf if src_edge_name == dst_edge_name
                else self.get_link(src_edge_name, dst_edge_name).get_transfer_rate()
                for dst_edge_name in EDGE_NAMES
            } for src_edge_name in EDGE_NAMES
        }

        return schedule_rate_info

    def get_transfer_rate_from_device_to_edge(self):
        transfer_rate_info = {
            device_name: {
                edge_name: self.get_link(device_name, edge_name).get_transfer_rate()
                for edge_name in EDGE_NAMES
            } for device_name in DEVICE_NAMES
        }

        return transfer_rate_info

    def get_task_amount_info_of_all_device(self):
        task_amount_on_device = {
            device_name: {
                app_type: 0 for app_type in APP_TYPES
            } for device_name in DEVICE_NAMES
        }

        for device_name in DEVICE_NAMES:
            task_info_list = self._get_task_info_from_device(device_name)
            for task_info in task_info_list:
                task_amount_on_device[task_info["gen_device"]][task_info["app_type"]] += task_info["process_data_size"]

        return task_amount_on_device

    def _get_task_info_from_device(self, device_name):
        device = self.get_device(device_name)

        task_info_list = []
        for task in device.tasks:
            task_info_list.append(task.get_info())

        return task_info_list

    def get_all_devices(self) -> List[Device]:
        devices: List[Device] = [v['data'] for _, v in self._graph.nodes(data=True) if v['category'] == 'Device']
        return devices

    def get_all_edges(self) -> List[Edge]:
        edges: List[Edge] = [v['data'] for _, v in self._graph.nodes(data=True) if v['category'] == 'Edge']
        return edges

    def get_device(self, name: str) -> Device:
        return self._graph.nodes[name]["data"]

    def get_edge(self, name: str) -> Edge:
        return self._graph.nodes[name]["data"]

    def get_link(self, src_name: str, dst_name: str) -> Link:
        return self._graph.edges[src_name, dst_name, 0]["data"]

    def _add_device_node(self, node: Node):
        if node.get_name() not in self._graph:
            self._graph.add_node(node.get_name(), data=node, category="Device")

    def _add_edge_node(self, node: Node):
        if node.get_name() not in self._graph:
            self._graph.add_node(node.get_name(), data=node, category="Edge")

    def _add_offload_link(self, link: OffloadLink):
        self._graph.add_edge(link.src.get_name(), link.dst.get_name(), data=link)

    def _add_schedule_link(self, link: ScheduleLink):
        self._graph.add_edge(link.src, link.dst, data=link)
        self._graph.add_edge(link.dst, link.src, data=link)

    def _init_node(self):
        for j in range(1, scenario_setting["n_edge"] + 1):
            self._add_edge_node(Edge(scenario_setting["E" + str(j)]))

        for device_name in DEVICE_NAMES:
            # 这里按照不均匀分布在边缘附近生成设备
            seed = random.random()
            if seed < 0.5:
                choice_edge = self.get_edge(EDGE_NAMES[0])
            else:
                choice_edge = self.get_edge(random.sample(EDGE_NAMES,1)[0])

            self._add_device_node(Device(device_name, choice_edge.location))

    def _init_link(self):
        for device_name in DEVICE_NAMES:
            for edge_name in EDGE_NAMES:
                device = self.get_device(device_name)
                edge = self.get_edge(edge_name)
                self._add_offload_link(OffloadLink(device, edge))

        for j in range(1, scenario_setting["n_schedule_link"] + 1):
            self._add_schedule_link(ScheduleLink(scenario_setting["SL" + str(j)]))


if __name__ == '__main__':
    scen = Scenario()
    ol = scen.get_device("D1")
    print(ol.location.x, ol.location.y)
