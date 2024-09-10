#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/23 16:22
# @Author  : zhangqi
# @File    : main.py
# @Software: PyCharm
import simpy
import pandas as pd

from datetime import datetime

from core.orchestrator_module.orchestrator import Orchestrator
from core.simsetting_module.simsetting import simSetting, DEVICE_NAMES, EDGE_NAMES, APP_TYPES, ItoAmap


def main():
    orc = Orchestrator()
    while orc.t < 20:
        orc.gen_all_tasks_on_device()
        off_e = [simpy.Event(orc.env.sim) for _ in range(len(EDGE_NAMES))]
        sch_e = [simpy.Event(orc.env.sim) for _ in range(len(EDGE_NAMES))]
        dep_e = [simpy.Event(orc.env.sim) for _ in range(len(EDGE_NAMES))]
        pro_e = [simpy.Event(orc.env.sim) for _ in range(len(EDGE_NAMES))]

        offload, schedule, deploy, process = orc.get_decision_from_model()

        print(f"offload = {offload}")
        print(f"schedule = {schedule}")
        print(f"deploy = {deploy}")
        print(f"deploy = {process}")

        for j, edge_name in  enumerate(EDGE_NAMES):
            orc.env.sim.process(orc.offload_all_device_to_edge(offload[edge_name], edge_name, offload_e=off_e[j]))
            orc.env.sim.process(orc.schedule_all_task_to_other(edge_name, schedule[edge_name], offload_e=off_e[j], schedule_e=sch_e[j]))
            orc.env.sim.process(orc.execute_deploy_decision_on_edge(edge_name, deploy[edge_name], schedule_e=sch_e[j], deploy_e=dep_e[j]))
            orc.env.sim.process(orc.process_all_tasks_on_edge(edge_name, process[edge_name], deploy_e=dep_e[j], process_e=pro_e[j]))

        orc.t += 10
        orc.env.sim.run(until=orc.t)

    task_processed_info = {
        edge_name: orc.scenario.get_edge(edge_name).done_task_info
        for edge_name in EDGE_NAMES
    }

    simulation_data = {edge_name: [] for edge_name in EDGE_NAMES}
    for edge_name in EDGE_NAMES:
        for info in task_processed_info[edge_name]:
            simulation_data[edge_name].append(info["cost_time"])

    # print(orc.get_edge_deployed_info_for_model())
    save_data_to_excel(simulation_data)


def save_data_to_excel(data):
    current_time = datetime.now()
    formatted_time = current_time.strftime("%d_%H-%M-%S")
    file_name = f"data_without_schedule_{formatted_time}.xlsx"
    xls_path = f"./output/{file_name}"
    excel_writer = pd.ExcelWriter(xls_path)

    max_length = max([len(lis) for key, lis in data.items()])
    for key, lis in data.items():
        data[key] = lis + [None] * (max_length - len(lis))

    data_pd = pd.DataFrame(data)
    data_pd.to_excel(excel_writer, index=True)

    excel_writer.close()


if __name__ == '__main__':
    main()
