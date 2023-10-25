#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 10:45
# @Author  : zhangqi
# @File    : node.py
# @Software: PyCharm
import math

from abc import ABCMeta, abstractmethod

class Location():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance_with(self, another_location):
        return math.sqrt((self.x - another_location.x) ** 2 + (self.y - another_location.y) ** 2)


class Node(metaclass=ABCMeta):

    def __init__(self):
        self._info = None
        self.location = None

    @abstractmethod
    def get_name(self):
        pass
