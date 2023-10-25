#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 10:57
# @Author  : zhangqi
# @File    : device.py
# @Software: PyCharm
import random

from typing import List

from core.scenario_module.node import Node, Location
from core.task_generator_module.task import Task


class Device(Node):

    def __init__(self, name, edge_location: Location):
        super(Device, self).__init__()
        self.device_name = name
        self.tasks: List[Task] = []
        self.location = self._init_location(edge_location)

    def _init_location(self, e_location) -> Location:
        x = random.random() * 10
        y = random.random() * 10
        return Location(x + e_location.x, y + e_location.y)


    def get_name(self):
        return self.device_name


if __name__ == '__main__':
    pass
