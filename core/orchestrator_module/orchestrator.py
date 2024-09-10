#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/19 16:30
# @Author  : zhangqi
# @File    : orchestrator.py
# @Software: PyCharm
import math

from typing import List, Tuple, Dict

import simpy

from core.task_generator_module.task import Task
from core.scenario_module.device import Device
from core.task_generator_module.task_generator import TaskGenerator
from core.scenario_module.scenario import Scenario
from core.env_module.environment import Env
# from core.decision_module.ec_model import ECModel
from core.decision_module.ec_model_without_schedule import ECModel
# from core.decision_module.ec_schedul_model import ECModel
from core.task_generator_module.applications import Applications
from core.simsetting_module.simsetting import simSetting, DEVICE_NAMES, EDGE_NAMES, APP_TYPES, ItoAmap


class Orchestrator:

    def __init__(self):
        self.task_generator = TaskGenerator()
        self.scenario = Scenario()
        self.env = Env()
        self.ec_model = ECModel()
        self.t = 0

    def _allocate_task_on_device(self, task: Task, device: Device):
        device.tasks.append(task)
        self.env.log(f"Generate {task.get_process_data_size()} KB {task.get_type()} id-{task.get_id()} on {device.get_name()}")

    def gen_all_tasks_on_device(self):
        self.task_generator.task_count = 0
        while not self.task_generator.is_empty():
            task = self.task_generator.random_generate_task_on_device(generate_time=self.env.sim.now)
            self._allocate_task_on_device(task, self.scenario.get_device(task.get_gen_device()))

    def _calculate_transfer_time(self, task: Task, src_name: str, dst_name: str):
        link = self.scenario.get_link(src_name, dst_name)
        return task.get_transfer_data_size() / link.get_transfer_rate()

    def _offload_tasks_from_device_to_edge(self, device_name: str, edge_name: str):
        device = self.scenario.get_device(device_name)
        edge = self.scenario.get_edge(edge_name)

        while len(device.tasks) > 0:
            task = device.tasks.pop()

            offload_cost_time = self._calculate_transfer_time(task, device_name, edge_name)
            yield self.env.sim.timeout(offload_cost_time)

            edge.add_task_to_queue(task.get_type(), task=task)
            self.env.log("-"*10 + f"{device_name} offload {task.get_type()} task id-{task.get_id()} to {edge_name}. [{offload_cost_time:.2f} s]")

    def offload_all_device_to_edge(self, offload_device_list: List, edge_name: str, offload_e: simpy.Event):
        event_list = []
        for device_name in offload_device_list:
            event_list.append(self.env.sim.process(self._offload_tasks_from_device_to_edge(device_name, edge_name)))

        yield simpy.AllOf(self.env.sim, event_list)
        offload_e.succeed()

    def _schedule_tasks_between_edge(self, src_name, dst_name, task_type, schedule_ratio: float):
        src_edge = self.scenario.get_edge(src_name)
        dst_edge = self.scenario.get_edge(dst_name)

        n_schedule_task = math.ceil(len(src_edge.tasks[task_type]) * schedule_ratio)
        # print(f"n_schedule_task = {n_schedule_task}")

        while n_schedule_task > 0:
            task = src_edge.tasks[task_type].pop(0)

            schedule_cost_time = self._calculate_transfer_time(task, src_name, dst_name)
            yield self.env.sim.timeout(schedule_cost_time)

            dst_edge.add_task_to_queue(task_type, task=task)
            self.env.log("-"*20+f"{src_name} schedule {task_type} task id-{task.get_id()} slice-{task.get_slice_id()} to {dst_name}. [{schedule_cost_time:.2f} s]")

            n_schedule_task -= 1

    def schedule_all_task_to_other(self, src_name, schedule_list: List[Tuple[str, str, float]],
                                   offload_e: simpy.Event, schedule_e: simpy.Event):
        yield offload_e     # 等待所有任务卸载完成

        event_list = []
        for schedule in schedule_list:
            event_list.append(self.env.sim.process(
                self._schedule_tasks_between_edge(src_name, schedule[0], schedule[1], schedule[2])))

        yield simpy.AllOf(self.env.sim, event_list)
        schedule_e.succeed()
        self.env.log("-"*20+f"{src_name} schedule complete!")

    def _deploy_app_on_edge(self, edge_name, app_type, deploy_resource: simpy.Resource):
        with deploy_resource.request() as req:
            yield req  # 请求CPU资源

            edge = self.scenario.get_edge(edge_name)
            deploy_time = edge.deploy_app_cost_time(app_type)

            if deploy_time >= 0:
                yield self.env.sim.timeout(deploy_time)
                self.env.log("-"*30+f"App of {app_type} has deployed on {edge_name}. [{deploy_time:.2f} s]")
            else:
                self.env.log("-"*30+f"Failed to deploy app of {app_type} on {edge_name}.")

    def execute_deploy_decision_on_edge(self, edge_name, deploy_decision: List, schedule_e, deploy_e):
        yield schedule_e

        edge = self.scenario.get_edge(edge_name)

        for app_type in APP_TYPES:
            if app_type not in deploy_decision:
                edge.remove_app(app_type)

        event_list = []
        deploy_resource = simpy.Resource(self.env.sim, capacity=1)
        for app_type in deploy_decision:
            event_list.append(self.env.sim.process(self._deploy_app_on_edge(edge_name, app_type, deploy_resource)))

        yield simpy.AllOf(self.env.sim, event_list)
        deploy_e.succeed()
        self.env.log("-"*30+f"{edge_name} deploy complete!")

    def _process_task_on_edge(self, edge_name, task_type, process_ratio: float,
                              cpu_resource: simpy.Resource):
        with cpu_resource.request() as req:
            yield req  # 请求CPU资源

            edge = self.scenario.get_edge(edge_name)
            n_process_task = math.floor(len(edge.tasks[task_type]) * process_ratio)

            if n_process_task > 0:
                while n_process_task > 0:
                    task = edge.tasks[task_type].pop(0)

                    process_cost_time = task.get_process_data_size() / edge.get_cpu()
                    yield self.env.sim.timeout(process_cost_time)

                    self.env.log("-"*40+f"{task_type} task id-{task.get_id()} slice-{task.get_slice_id()} has processed on {edge_name}. [{process_cost_time:.2f} s]")
                    edge.log_processed_task(task, self.env.sim.now, edge_name)

                    n_process_task -= 1

    def process_all_tasks_on_edge(self, edge_name, process_list: List[Tuple[str, float]],
                                  deploy_e: simpy.Event, process_e: simpy.Event):
        yield deploy_e

        cpu_resource = simpy.Resource(self.env.sim, capacity=1)
        event_list = []
        for process in process_list:
            event_list.append(
                self.env.sim.process(self._process_task_on_edge(edge_name, process[0], process[1], cpu_resource))
            )

        yield simpy.AllOf(self.env.sim, event_list)
        process_e.succeed()
        self.env.log("-"*40+f"{edge_name} processed complete!")

    def get_task_info_for_model(self):
        task_amount_info = self.scenario.get_task_amount_info_of_all_device()

        l_for_model = {}
        for i, device_name in enumerate(DEVICE_NAMES):
            for a, app_type in enumerate(APP_TYPES):
                l_for_model[(i, a)] = task_amount_info[device_name][app_type]

        return l_for_model

    def get_offload_rate_for_model(self):
        transfer_rate_info = self.scenario.get_transfer_rate_from_device_to_edge()

        r_for_model = {}
        for i, device_name in enumerate(DEVICE_NAMES):
            for j, edge_name in enumerate(EDGE_NAMES):
                r_for_model[(i, j)] = transfer_rate_info[device_name][edge_name]

        return r_for_model

    def get_schedule_rate_for_model(self):
        schedule_rate_info = self.scenario.get_schedule_rate_between_edges()

        R_for_model = {}
        for j, src_edge_name in enumerate(EDGE_NAMES):
            for k, dst_edge_name in enumerate(EDGE_NAMES):
                R_for_model[(j, k)] = schedule_rate_info[src_edge_name][dst_edge_name]

        return R_for_model

    def get_edge_cpu_for_model(self):
        return [edge.get_cpu() for edge in self.scenario.get_all_edges()]

    def get_edge_max_deploy_for_model(self):
        return [edge.get_max_mem() for edge in self.scenario.get_all_edges()]

    def get_all_edge_queue_for_model(self):
        all_edge_queue_info = self.scenario.get_all_edge_queue_info()

        q_for_model = {
            (j, a): all_edge_queue_info[edge_name][app_type]
            for j, edge_name in enumerate(EDGE_NAMES)
            for a, app_type in enumerate(APP_TYPES)
        }

        return q_for_model

    def get_edge_deployed_info_for_model(self):
        all_edge_deployed_info = self.scenario.get_all_edge_deployed_info()

        y_deploy_for_model = {
            (j, a): all_edge_deployed_info[edge_name][app_type]
            for j, edge_name in enumerate(EDGE_NAMES)
            for a, app_type in enumerate(APP_TYPES)
        }

        return y_deploy_for_model

    def send_parameter_to_decision_module(self):
        devices = self.scenario.get_all_devices()
        edges = self.scenario.get_all_edges()
        apps = Applications().apps

        self.ec_model.set_parameter(n_device=len(devices), n_edge=len(edges), n_app=Applications().n_app,
                                    delta=simSetting.model_setting["delta"],
                                    beta=simSetting.model_setting["beta"],
                                    C_u=simSetting.model_setting["C_u"],
                                    C_d=simSetting.model_setting["C_d"],
                                    C_a=simSetting.model_setting["C_a"],
                                    C_c=simSetting.model_setting["C_c"],
                                    ItoAmap=ItoAmap,
                                    L=self.get_task_info_for_model(),
                                    r=self.get_offload_rate_for_model(),
                                    R=self.get_schedule_rate_for_model(),
                                    s=Applications().get_app_deploy_time_for_model(),
                                    Ha=Applications().get_app_mem_occupation(),
                                    f=self.get_edge_cpu_for_model(),
                                    Hmax=self.get_edge_max_deploy_for_model(),
                                    queue_=self.get_all_edge_queue_for_model(),
                                    y_deploy_=self.get_edge_deployed_info_for_model())

    def get_decision_from_model(self):
        self.send_parameter_to_decision_module()
        x, y, z, theta, mu = self.ec_model.solve()
        # print(x)
        # print(y)
        # print(z)
        # print(theta)
        # print(mu)

        # format: {'E1': ['D1'], 'E2': ['D2', 'D3']}
        offload_decision = self._turn_x_to_offload_decision(x)
        # format: {'E1': [], 'E2': [('E1', 'A2', 0.24074074074074087)]}
        schedule_decision = self._turn_y_and_theta_to_schedule_decision(y, theta)
        # format: {'E1': ['A1', 'A2'], 'E2': ['A2']}
        # format: {}
        deploy_decision, process_decision = self._turn_z_mu_to_deploy_and_proocess_decision(z, mu)

        return offload_decision, schedule_decision, deploy_decision, process_decision

    def _turn_x_to_offload_decision(self, x):
        offload_decision = {edge_name: [] for edge_name in EDGE_NAMES}

        for i, device_name in enumerate(DEVICE_NAMES):
            for j, edge_name in enumerate(EDGE_NAMES):
                if abs(x[i, j] - 1) < 1e-4:
                    offload_decision[edge_name].append(device_name)

        return offload_decision

    def _turn_y_and_theta_to_schedule_decision(self, y, theta):
        schedule_decision = {edge_name: [] for edge_name in EDGE_NAMES}

        for j, src_edge_name in enumerate(EDGE_NAMES):
            for k, dst_edge_name in enumerate(EDGE_NAMES):
                for a, app_type in enumerate(APP_TYPES):
                    if abs(y[j, k, a] - 1) < 1e-4:
                        schedule_decision[src_edge_name].append((dst_edge_name, app_type, theta[j, k, a]))

        return schedule_decision

    def _turn_z_mu_to_deploy_and_proocess_decision(self, z, mu):
        deploy_decision = {edge_name: [] for edge_name in EDGE_NAMES}
        process_decision = {edge_name: [] for edge_name in EDGE_NAMES}

        for j, edge_name in enumerate(EDGE_NAMES):
            for a, app_type in enumerate(APP_TYPES):
                if abs(z[j, a] - 1) < 1e-4:
                    deploy_decision[edge_name].append(app_type)
                    process_decision[edge_name].append((app_type, mu[j, a]))

        return deploy_decision, process_decision


if __name__ == '__main__':
    pass
