#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 23:22
# @Author  : zhangqi
# @File    : simsetting.py
# @Software: PyCharm
import json
import os

# json_files_path = "D:/BaiduSyncdisk/PythonCodeset/PyEdgeSim/core/simsetting_module/json_files_1"
json_files_path = "H:\\BaiduSyncdisk\\PythonCodeset\\PyEdgeSim\\core\\simsetting_module\\json_files_1"


def read_json_file(json_path):
    with open(json_path) as json_file:
        config = json.load(json_file)
    return config


class SimSetting:

    def __init__(self, tasks_setting, scenario_setting, model_setting):
        self.task_setting = read_json_file(tasks_setting)
        self.scenario_setting = read_json_file(scenario_setting)
        self.model_setting = read_json_file(model_setting)


tasks_setting_path = os.path.join(json_files_path, 'tasks_setting.json')
scenario_setting_path = os.path.join(json_files_path, 'scenario_setting.json')
model_setting_path = os.path.join(json_files_path, 'model_setting.json')

simSetting = SimSetting(tasks_setting_path, scenario_setting_path, model_setting_path)

DEVICE_NAMES = ["D" + str(i) for i in range(1, simSetting.scenario_setting["n_device"] + 1)]
EDGE_NAMES = ["E" + str(j) for j in range(1, simSetting.scenario_setting["n_edge"] + 1)]
APP_TYPES = ["A" + str(a) for a in range(1, simSetting.task_setting["n_app"] + 1)]

ItoAmap = [i % len(APP_TYPES) for i in range(len(DEVICE_NAMES))]

if __name__ == '__main__':
    # print(simSetting.task_setting)
    # print(simSetting.scenario_setting)
    # print(simSetting.model_setting)
    #
    # c_u = simSetting.model_setting["C_u"]
    #
    # print(c_u[1][1])
    print(ItoAmap)
