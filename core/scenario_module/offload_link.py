#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 11:05
# @Author  : zhangqi
# @File    : offload_link.py
# @Software: PyCharm
import math

from core.scenario_module.link import Link
from core.scenario_module.device import Device
from core.scenario_module.edge import Edge
from core.simsetting_module.simsetting import simSetting


class OffloadLink(Link):

    def __init__(self, device: Device, edge: Edge):
        super(OffloadLink, self).__init__()
        self.src = device
        self.dst = edge

    def get_transfer_rate(self):
        B = 1  # bandwidth 10^6 Hz = 1 MHz
        P_0 = 1  # transmit fixed power 1 Watt
        f_c = 915  # carrier frequency 915 MHz
        # distance between Device and edge server
        # d_M = self.src.location.distance_with(self.dst.location)
        d_M = 30
        A_d = 4.11  # antenna gain 4.11
        d_e = 2.6  # path loss exponent
        theta_2 = 1e-10 # receiver noise power 10^-10 Watt

        h = A_d * math.pow(3 * 1e8 / (4 * math.pi * f_c * d_M), d_e)

        R = B * math.log(1 + (P_0*h / theta_2), 2) / 8
        return R

if __name__ == '__main__':
    D1_info = simSetting.scenario_setting["D1"]
    D2_info = simSetting.scenario_setting["D2"]
    E1_info = simSetting.scenario_setting["E1"]

    D1 = Device(D1_info)
    D2 = Device(D2_info)
    E1 = Edge(E1_info)

    d = E1.location.distance_with(D2.location)
    print(d)
    offload_link = OffloadLink(D1, E1)
    print(offload_link.get_transfer_rate())
