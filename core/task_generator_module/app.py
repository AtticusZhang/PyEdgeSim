#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 0:05
# @Author  : zhangqi
# @File    : app.py
# @Software: PyCharm

class App:

    def __init__(self, info):
        self._info = info

    def get_app_deploy_cost(self):
        return self._info["app_deploy_cost"]

    def get_mem_occupation(self):
        return self._info["mem_occupation"]
