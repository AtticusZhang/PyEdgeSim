#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 11:09
# @Author  : zhangqi
# @File    : schedule_link.py
# @Software: PyCharm
from core.scenario_module.link import Link


class ScheduleLink(Link):

    def __init__(self, sl_info):
        super(ScheduleLink, self).__init__()
        self._info = sl_info
        self.src = sl_info["edge_names"][0]
        self.dst = sl_info["edge_names"][1]

    def get_transfer_rate(self):
        return self._info["transfer_rate"]
