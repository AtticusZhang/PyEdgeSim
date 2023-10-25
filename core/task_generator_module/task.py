#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 23:49
# @Author  : zhangqi
# @File    : task.py
# @Software: PyCharm
from typing import Dict


class Task:

    def __init__(self, info):
        self._info = info

    def get_id(self):
        return self._info["task_id"]

    def get_slice_id(self):
        return self._info["slice_id"]

    def get_type(self):
        return self._info["app_type"]

    def get_generate_time(self):
        return self._info["generate_time"]

    def get_gen_device(self):
        return self._info["gen_device"]

    def get_transfer_data_size(self):
        return self._info["transfer_data_size"]

    def get_process_data_size(self):
        return self._info["process_data_size"]

    def get_info(self) -> Dict:
        return self._info
