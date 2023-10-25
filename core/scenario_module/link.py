#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 11:02
# @Author  : zhangqi
# @File    : link.py
# @Software: PyCharm
from abc import ABCMeta, abstractmethod


class Link(metaclass=ABCMeta):

    def __init__(self):
        self._info = None
        self.src = None
        self.dst = None

    @abstractmethod
    def get_transfer_rate(self):
        pass
