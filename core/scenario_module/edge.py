#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 11:00
# @Author  : zhangqi
# @File    : edge.py
# @Software: PyCharm
import copy

from typing import Dict, List

from core.task_generator_module.applications import Applications
from core.simsetting_module.simsetting import simSetting
from core.scenario_module.node import Node, Location
from core.task_generator_module.task import Task


def slice_task(task: Task):
    for i in range(task.get_process_data_size(), 0, -1):
        sliced_task = copy.deepcopy(task.get_info())
        sliced_task.update({"slice_id": i})
        sliced_task.update({"transfer_data_size": 1})
        sliced_task.update({"process_data_size": 1})
        yield Task(sliced_task)


class Edge(Node):

    def __init__(self, info):
        super(Edge, self).__init__()
        self._info = info
        self.location = Location(info["location"][0], info["location"][1])

        self.tasks: Dict[str, List[Task]] = self._init_tasks()
        self.done_task_info = []
        self.deployed_app: List = self._info["deployed_app"]
        self.mem_used = 0

    def get_all_task_queue(self):
        return self.tasks

    def get_max_mem(self):
        return self._info["max_mem"]

    def get_name(self):
        return self._info["edge_name"]

    def get_cpu(self):
        return self._info["cpu_frequency"]

    def add_task_to_queue(self, task_type: str, task: Task):
        if task_type not in self.tasks.keys():
            self.tasks[task_type] = []

        self.tasks[task_type].append(task)
        # 暂时不使用分片
        # sliced_tasks_generator = slice_task(task)
        # for sliced_task in sliced_tasks_generator:
        #     self.tasks[task_type].append(sliced_task)

    def log_processed_task(self, task: Task, processed_time, processed_device_name):
        task_processed_info = {
            "task_id": task.get_id(),
            "slice_id": task.get_slice_id(),
            "app_type": task.get_type(),
            "gen_device": task.get_gen_device(),
            "processed_device": processed_device_name,
            "generate_time": task.get_generate_time(),
            "processed_time": processed_time,
            "cost_time": processed_time - task.get_generate_time()
        }
        self.done_task_info.append(task_processed_info)

    def deploy_app_cost_time(self, task_type: str):
        if task_type in self.deployed_app:
            return 0
        else:
            if self.mem_used < self._info["max_mem"]:
                self.deployed_app.append(task_type)
                self.mem_used += simSetting.task_setting[task_type]["mem_occupation"]
                return simSetting.task_setting[task_type]["app_deploy_cost"]
            else:
                return -1

    def remove_app(self, task_type: str):
        if task_type in self.deployed_app:
            return self.deployed_app.remove(task_type)

    def _init_tasks(self) -> Dict[str, List[Task]]:
        tasks = {app_type: [] for app_type in Applications().app_types}

        for task_type, task_list in self._info["tasks"].items():
            for task in task_list:
                tasks[task_type].append(Task(task))

        return tasks


if __name__ == '__main__':
    edge_info = simSetting.scenario_setting["E2"]
    edge = Edge(edge_info)
    print(edge.tasks)
