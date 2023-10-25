from pyomo.environ import ConcreteModel, Set, Var, Param, Expression, Objective, Constraint
from pyomo.environ import Binary, Reals, minimize, SolverFactory, value

from core.simsetting_module.simsetting import simSetting
from core.decision_module.expression import upload_time, received_task, send_task_to, received_task_from_other, \
    send_task_to_other, queue_after_process, queue_before_process, time_of_send_task_to, time_of_send_task_to_other, \
    time_of_received_task_from_other, time_of_deploy, cost_of_deploy, time_of_process, \
    c1, c2, c3, c5, c6, c9, c10, c41, c42, c71, c72, c8, obj_rule


def total_time_of_edge(model, j):
    return sum(model.upload_time[i, j] for i in model.I) \
           + sum(model.time_of_send_task_to_other[j, a] for a in model.A) \
           + sum(model.time_of_received_task_from_other[j, a] for a in model.A) \
           + sum(model.time_of_deploy[j, a] for a in model.A) \
           + sum(model.time_of_process[j, a] for a in model.A)


def total_cost_of_edge(model, j):
    return sum(model.C_u[j] * model.upload_time[i, j] for i in model.I) \
           + sum(model.C_d[j, k] * model.send_task_to[j, k, a] for a in model.A for k in model.J if k != j) \
           + sum(model.cost_of_deploy[j, a] for a in model.A) \
           + sum(model.C_c[j] * model.time_of_process[j, a] for a in model.A)


class ECModel:
    def __init__(self):
        self.n_device = 0
        self.n_edge = 0
        self.n_app = 0

        self.delta = 0
        self.beta = 0.5

        self.C_u = {}
        self.C_d = {}
        self.C_a = []
        self.C_c = []

        self.p = {}
        self.L = {}
        self.r = {}
        self.R = {}
        self.s = []
        self.Ha = []
        self.f = []
        self.Hmax = []

        self.queue_ = {}
        self.y_deploy_ = {}

    def set_parameter(self, **kwargs):
        self.n_device = kwargs["n_device"]
        self.n_edge = kwargs["n_edge"]
        self.n_app = kwargs["n_app"]

        self.delta = kwargs["delta"]
        self.beta = kwargs["beta"]

        self.C_u = {j: kwargs["C_u"][j] for j in range(self.n_edge)}
        self.C_d = {(j, k): kwargs["C_d"][j][k] for j in range(self.n_edge) for k in range(self.n_edge)}
        self.C_a = kwargs["C_a"]
        self.C_c = kwargs["C_c"]

        ItoAmap = kwargs["ItoAmap"]
        for i in range(self.n_device):
            for a in range(self.n_app):
                if a == ItoAmap[i]:
                    self.p[(i, a)] = 1
                else:
                    self.p[(i, a)] = 1

        self.L = kwargs["L"]
        self.r = kwargs["r"]
        self.R = kwargs["R"]
        self.s = kwargs["s"]
        self.Ha = kwargs["Ha"]
        self.f = kwargs["f"]
        self.Hmax = kwargs["Hmax"]

        self.queue_ = kwargs["queue_"]
        self.y_deploy_ = kwargs["y_deploy_"]

    def create_model(self):
        model = ConcreteModel()

        model.I = Set(initialize=range(self.n_device))
        model.J = Set(initialize=range(self.n_edge))
        model.A = Set(initialize=range(self.n_app))
        model.delta = Param(initialize=self.delta)
        model.beta = Param(initialize=self.beta)

        model.x = Var(model.I, model.J, within=Binary)
        model.y = Var(model.J, model.J, model.A, within=Binary)
        model.z = Var(model.J, model.A, within=Binary)
        model.theta = Var(model.J, model.J, model.A, within=Reals, bounds=[0,1])
        model.mu = Var(model.J, model.A, within=Reals, bounds=[0,1])

        model.C_u = Param(model.J, initialize=self.C_u)
        model.C_d = Param(model.J, model.J, initialize=self.C_d)
        model.C_a = Param(model.A, initialize=self.C_a)
        model.C_c = Param(model.J, initialize=self.C_c)
        model.p = Param(model.I, model.A, initialize=self.p)

        model.L = Param(model.I, model.A, initialize=self.L)
        model.r = Param(model.I, model.J, initialize=self.r)
        model.R = Param(model.J, model.J, initialize=self.R)
        model.s = Param(model.A, initialize=self.s)
        model.Ha = Param(model.A, initialize=self.Ha)
        model.f = Param(model.J, initialize=self.f)
        model.Hmax = Param(model.J, initialize=self.Hmax)

        model.queue_ = Param(model.J, model.A, initialize=self.queue_)
        model.y_deploy_ = Param(model.J, model.A, initialize=self.y_deploy_)

        # 定义表达式
        model.upload_time = Expression(model.I, model.J, rule=upload_time)
        model.received_task = Expression(model.J, model.A, rule=received_task)
        model.send_task_to = Expression(model.J, model.J, model.A, rule=send_task_to)
        model.received_task_from_other = Expression(model.J, model.A, rule=received_task_from_other)
        model.send_task_to_other = Expression(model.J, model.A, rule=send_task_to_other)
        model.queue_before_process = Expression(model.J, model.A, rule=queue_before_process)
        model.queue_after_process = Expression(model.J, model.A, rule=queue_after_process)
        model.time_of_send_task_to = Expression(model.J, model.J, model.A, rule=time_of_send_task_to)
        model.time_of_send_task_to_other = Expression(model.J, model.A, rule=time_of_send_task_to_other)
        model.time_of_received_task_from_other = Expression(model.J, model.A,
                                                            rule=time_of_received_task_from_other)
        model.time_of_deploy = Expression(model.J, model.A, rule=time_of_deploy)
        model.cost_of_deploy = Expression(model.J, model.A, rule=cost_of_deploy)
        model.time_of_process = Expression(model.J, model.A, rule=time_of_process)
        model.total_time_of_edge = Expression(model.J, rule=total_time_of_edge)
        model.total_cost_of_edge = Expression(model.J, rule=total_cost_of_edge)

        # 择一约束
        model.c1 = Constraint(model.I, rule=c1)
        model.c2 = Constraint(model.A, model.J, model.J, rule=c2)
        model.c3 = Constraint(model.J, model.A, rule=c3)
        model.c41 = Constraint(model.A, model.J, model.J, rule=c41)
        model.c42 = Constraint(model.A, model.J, model.J, rule=c42)
        model.c5 = Constraint(model.J, model.A, rule=c5)  # inf
        model.c6 = Constraint(model.A, model.J, model.J, rule=c6)
        model.c71 = Constraint(model.A, model.J, rule=c71)
        model.c72 = Constraint(model.A, model.J, rule=c72)
        # model.c8 = Constraint(model.J, rule=self.c8)
        model.c9 = Constraint(model.J, rule=c9)
        model.c10 = Constraint(model.J, rule=c10)

        model.obj = Objective(rule=obj_rule, sense=minimize)

        return model

    def solve(self):
        model = self.create_model()
        opt = SolverFactory('scip')
        solution = opt.solve(model)
        # 输出求解结果
        # solution.write()

        x = {
            (i, j): value(model.x[i, j])
            for i in model.I
            for j in model.J
        }

        y = {
            (j, k, a): value(model.y[j, k, a])
            for j in model.J
            for k in model.J
            for a in model.A
        }

        z = {
            (j, a): value(model.z[j, a])
            for j in model.J
            for a in model.A
        }

        theta = {
            (j, k, a): value(model.theta[j, k, a])
            for j in model.J
            for k in model.J
            for a in model.A
        }

        mu = {
            (j, a): value(model.mu[j, a])
            for j in model.J
            for a in model.A
        }

        return x, y, z, theta, mu


if __name__ == '__main__':
    pass
