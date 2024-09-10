#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/23 15:52
# @Author  : zhangqi
# @File    : expression.py
# @Software: PyCharm
def upload_time(model, i, j):
    return sum(model.L[i, a] for a in model.A) * model.x[i, j] / model.r[i, j]


def received_task(model, j, a):
    return sum(model.L[i, a] * model.x[i, j] for i in model.I)


def send_task_to(model, j, k, a):
    return model.theta[j, k, a] * model.y[j, k, a] * (model.queue_[j, a] + model.received_task[j, a])


def received_task_from_other(model, j, a):
    return sum(model.send_task_to[k, j, a] for k in model.J if k != j)


def send_task_to_other(model, j, a):
    return sum(model.send_task_to[j, k, a] for k in model.J if k != j)


def queue_before_process(model, j, a):
    return model.queue_[j, a] + model.received_task[j, a] + model.received_task_from_other[j, a] - model.send_task_to_other[j, a]


def queue_after_process(model, j, a):
    return (1 - model.mu[j, a]) * model.queue_before_process[j, a]


def time_of_send_task_to(model, j, k, a):
    return model.send_task_to[j, k, a] / model.R[j, k]


def time_of_send_task_to_other(model, j, a):
    return sum(model.time_of_send_task_to[j, k, a] for k in model.J if k != j)


def time_of_received_task_from_other(model, j, a):
    return sum(model.time_of_send_task_to[k, j, a] for k in model.J if k != j)


def time_of_deploy(model, j, a):
    return (1 - model.y_deploy_[j, a]) * model.s[a] * model.z[j, a]


def cost_of_deploy(model, j, a):
    return (1 - model.y_deploy_[j, a]) * model.C_a[a] * model.z[j, a]


def time_of_process(model, j, a):
    return model.mu[j, a] * model.queue_before_process[j, a] / model.f[j]


# 择一约束，用户关联约束
def c1(model, i):
    return sum(model.x[i, j] for j in model.J) == 1


# 只有接受到了a才可以向其他边缘发送任务a
def c2(model, a, j, k):
    return model.y[j, k, a] <= sum(model.p[i, a] * model.x[i, j] for i in model.I)


# 最多选择一个边缘发送
def c3(model, j, a):
    return sum(model.y[j, k, a] for k in model.J if k != j) <= 1


# 发送比例控制
def c41(model, a, j, k):
    N = 1000
    return model.theta[j, k, a] / N <= model.y[j, k, a]


def c42(model, a, j, k):
    N = 1000
    return model.y[j, k, a] <= model.theta[j, k, a] * N


# 发送比例总不能大于1
def c5(model, j, a):
    return sum(model.theta[j, k, a] for k in model.J) <= 1


# 只有边缘上部署了应用，才可以发送
def c6(model, a, j, k):
    return model.y[j, k, a] <= model.z[k, a]


# 处理比例控制
def c71(model, a, k):
    N = 1
    return model.mu[k, a] / N <= model.z[k, a]


def c72(model, a, k):
    N = 1
    return model.z[k, a] <= model.mu[k, a] * N


def c8(model, j):
    return sum(model.mu[j, a] for a in model.A) <= 1


# 放置资源约束
def c9(model, j):
    return sum(model.z[j, a] * model.Ha[a] for a in model.A) <= model.Hmax[j]


# 时延约束：每个边的运行时间要小于时隙长度
def c10(model, j):
    return model.total_time_of_edge[j] <= model.delta


def obj_rule(model):

    obj = 0
    queue_remain = 0
    sum_cost = 0
    for j in model.J:
        queue_remain += sum(model.queue_after_process[j, a] for a in model.A)
        sum_cost += model.total_cost_of_edge[j]

    obj += model.beta * queue_remain + (1 - model.beta) * sum_cost

    return obj
