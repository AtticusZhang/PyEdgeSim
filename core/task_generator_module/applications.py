#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 0:06
# @Author  : zhangqi
# @File    : applications.py
# @Software: PyCharm
from core.simsetting_module.simsetting import simSetting, APP_TYPES
from core.task_generator_module.app import App


class Applications:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.n_app = simSetting.task_setting["n_app"]
        self.app_types = APP_TYPES
        self.apps = [App(simSetting.task_setting["A"+str(a)]) for a in range(1, self.n_app+1)]

    def get_app_deploy_time_for_model(self):
        return [app.get_app_deploy_cost() for app in self.apps]

    def get_app_mem_occupation(self):
        return [app.get_mem_occupation() for app in self.apps]


if __name__ == '__main__':
    print(Applications().get_app_mem_occupation())
