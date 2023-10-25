#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 10:42
# @Author  : zhangqi
# @File    : task_generator.py
# @Software: PyCharm
import random

from core.task_generator_module.task import Task
from core.simsetting_module.simsetting import simSetting, DEVICE_NAMES, EDGE_NAMES, APP_TYPES, ItoAmap
from core.scenario_module.scenario import Scenario

n_task = simSetting.task_setting["n_task"]

class TaskGenerator:

    def __init__(self):
        self.task_count = 0

    def is_empty(self) -> bool:
        return self.task_count >= n_task

    def generator_task(self, **kwargs) -> Task:
        self.task_count += 1
        task_info = {
            "generate_time": kwargs["generate_time"],
            "task_id": self.task_count,
            "slice_id": -1,
            "app_type": kwargs["app_type"],
            "gen_device": kwargs["gen_device"],
            "transfer_data_size": kwargs["transfer_data_size"],
            "process_data_size": kwargs["process_data_size"]
        }
        return Task(task_info)

    def random_generate_task_on_device(self, generate_time):
        device_name = random.sample(DEVICE_NAMES, 1)[0]

        return self.generator_task(generate_time=generate_time,
                                   app_type=APP_TYPES[ItoAmap[DEVICE_NAMES.index(device_name)]],
                                   gen_device=device_name,
                                   transfer_data_size=simSetting.task_setting["transfer_data_size"],
                                   process_data_size=simSetting.task_setting["process_data_size"])


if __name__ == '__main__':
    gen = TaskGenerator()
    count_D1 = 0
    count_D2 = 0
    count_D3 = 0
    while not gen.is_empty():
        task = gen.random_generate_task_on_device(0)
        if task.get_gen_device() == "D1":
            count_D1 += 1
        elif task.get_gen_device() == "D2":
            count_D2 += 1
        else:
            count_D3 += 1

    print(count_D1 / simSetting.task_setting["n_task"])
    print(count_D2 / simSetting.task_setting["n_task"])
    print(count_D3 / simSetting.task_setting["n_task"])
