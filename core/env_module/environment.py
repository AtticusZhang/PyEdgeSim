#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 18:13
# @Author  : zhangqi
# @File    : environment.py
# @Software: PyCharm
import simpy


class Env:
    def __init__(self):
        self.sim = simpy.Environment()

    def log(self, content):
        print(f"[{self.sim.now:.2f}]: {content}")
