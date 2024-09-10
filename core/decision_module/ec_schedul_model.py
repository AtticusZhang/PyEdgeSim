from pyomo.environ import ConcreteModel, Set, Var, Param, Expression, Objective, Constraint
from pyomo.environ import Binary, Reals, minimize, SolverFactory, value


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
        self.R_off = {}
        self.R_sch = {}
        self.s = []
        self.Ha = []
        self.f = []
        self.Hmax = []

        self.queue_ = {}
        self.z_deploy_ = {}

    def set_parameter(self, **kwargs):
        self.n_device = kwargs["n_device"]
        self.n_edge = kwargs["n_edge"]
        self.n_app = kwargs["n_app"]

        self.delta = kwargs["delta"]
        self.beta = kwargs["beta"]

        self.C_u = {j: kwargs["C_u"][j] for j in range(self.n_edge)}    # 应该修改为 C^u_{i,j}
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
        self.R_off = kwargs["r"]
        self.R_sch = kwargs["R"]
        self.s = kwargs["s"]
        self.Ha = kwargs["Ha"]
        self.f = kwargs["f"]
        self.Hmax = kwargs["Hmax"]

        self.queue_ = kwargs["queue_"]
        self.z_deploy_ = kwargs["y_deploy_"]

    def create_model(self):
        model = ConcreteModel()

        model.I = Set(initialize=range(self.n_device))
        model.J = Set(initialize=range(self.n_edge))
        model.A = Set(initialize=range(self.n_app))
        model.delta = Param(initialize=self.delta)
        model.beta = Param(initialize=self.beta)

        model.x = Var(model.I, model.J, within=Binary)
        # model.y = Var(model.J, model.J, model.A, within=Binary)
        model.z = Var(model.J, model.A, within=Binary)
        model.theta = Var(model.J, model.J, model.A, within=Reals, bounds=[0, 1])
        model.mu = Var(model.J, model.A, within=Reals, bounds=[0, 1])

        model.C_u = Param(model.J, initialize=self.C_u)
        model.C_d = Param(model.J, model.J, initialize=self.C_d)
        model.C_a = Param(model.A, initialize=self.C_a)
        model.C_c = Param(model.J, initialize=self.C_c)
        model.p = Param(model.I, model.A, initialize=self.p)

        model.L = Param(model.I, model.A, initialize=self.L)
        model.R_off = Param(model.I, model.J, initialize=self.R_off)
        model.R_sch = Param(model.J, model.J, initialize=self.R_sch)
        model.s = Param(model.A, initialize=self.s)
        model.Ha = Param(model.A, initialize=self.Ha)
        model.f = Param(model.J, initialize=self.f)
        model.Hmax = Param(model.J, initialize=self.Hmax)

        model.queue_ = Param(model.J, model.A, initialize=self.queue_)
        model.z_deploy_ = Param(model.J, model.A, initialize=self.z_deploy_)    # 修改 原 y 表示调度，z表示部署

        def offload_time_rule(mod, i, a):
            return sum(
                mod.x[i, j] * mod.L[i, a] / mod.R_off[i, j]
                for j in mod.J
            )
        model.offload_time = Expression(model.I, model.A, rule=offload_time_rule)

        def task_offloaded_rule(mod, j, a):
            return sum(
                mod.L[i, a] * mod.x[i, j]
                for i in mod.I
            )
        model.task_offloaded = Expression(model.J, model.A, rule=task_offloaded_rule)

        def time_of_task_offloaded_rule(mod, j, a):
            return sum(
                mod.L[i, a] * mod.x[i, j] / mod.R_off[i, j]
                for i in mod.I
            )
        model.time_of_task_offloaded = Expression(model.J, model.A, rule=time_of_task_offloaded_rule)

        def send_task_amount_rule(mod, j, k, a):
            return mod.theta[j, k, a] * (mod.queue_[j, a] + mod.task_offloaded[j, a])
        model.send_task_amount = Expression(model.J, model.J, model.A, rule=send_task_amount_rule)

        def task_send_to_other_rule(mod, j, a):
            return sum(mod.send_task_amount[j, k, a] for k in model.J)
        model.task_send_to_other = Expression(model.J, model.A, rule=task_send_to_other_rule)

        def task_received_from_other_rule(mod, j, a):
            return sum(mod.send_task_amount[k, j, a] for k in model.J)
        model.task_received_from_other = Expression(model.J, model.A, rule=task_received_from_other_rule)

        def queue_before_process_rule(mod, j, a):
            return mod.queue_[j, a] + mod.task_offloaded[j, a] + mod.task_received_from_other[j, a] \
                   - mod.task_send_to_other[j, a]
        model.queue_before_process = Expression(model.J, model.A, rule=queue_before_process_rule)

        def queue_after_process_rule(mod, j, a):
            return (1 - mod.mu[j, a]) * mod.queue_before_process[j, a]
        model.queue_after_process = Expression(model.J, model.A, rule=queue_after_process_rule)

        def send_time_rule(mod, j, k, a):
            return mod.send_task_amount[j, k, a] / mod.R_sch[j, k]
        model.send_time = Expression(model.J, model.J, model.A, rule=send_time_rule)

        def time_send_task_to_other_rule(mod, j, a):
            return sum(mod.send_time[j, k, a] for k in mod.J)
        model.time_send_task_to_other = Expression(model.J, model.A, rule=time_send_task_to_other_rule)

        def time_receive_task_from_other_rule(mod, j, a):
            return sum(mod.send_time[k, j, a] for k in mod.J)
        model.time_receive_task_from_other = Expression(model.J, model.A, rule=time_receive_task_from_other_rule)

        def time_of_deploy_rule(mod, j, a):
            return (1 - mod.z_deploy_[j, a]) * mod.s[a] * mod.z[j, a]
        model.time_of_deploy = Expression(model.J, model.A, rule=time_of_deploy_rule)

        def time_of_process_rule(mod, j, a):
            return mod.mu[j, a] * mod.queue_before_process[j, a] / model.f[j]   # f 修改为 F_edge，增加本地计算能力
        model.time_of_process = Expression(model.J, model.A, rule=time_of_process_rule)

        def total_time_of_edge_rule(mod, j):
            return sum(mod.time_of_task_offloaded[j, a] for a in model.A) \
                   + sum(model.send_time[j, k, a] for a in model.A for k in model.J) \
                   + sum(model.send_time[k, j, a] for a in model.A for k in model.J) \
                   + sum(model.time_of_deploy[j, a] for a in model.A) \
                   + sum(model.time_of_process[j, a] for a in model.A)
        model.total_time_of_edge = Expression(model.J, rule=total_time_of_edge_rule)

        # 定义总的目标函数

        def obj_rule(mod):
            return mod.beta * sum(mod.queue_after_process[j, a] for a in mod.A for j in mod.J) \
                   + (1 - mod.beta) * (sum(
                    mod.offload_time[i, a] for i in mod.I for a in mod.A) + sum(
                    mod.send_time[j, k, a] for j in mod.J for k in mod.J for a in mod.A) + sum(
                    mod.time_of_deploy[j, a] + mod.time_of_process[j, a] for j in mod.J for a in mod.A)
                   )
        model.obj = Objective(rule=obj_rule, sense=minimize)

        # 定义约束条件

        # 择一约束，用户关联约束
        def c1_rule(mod, i):
            return sum(mod.x[i, j] for j in mod.J) == 1
        model.c1 = Constraint(model.I, rule=c1_rule)

        # 发送比例总不能大于1
        def c5_rule(mod, j, a):
            return sum(mod.theta[j, k, a] for k in mod.J) <= 1
        model.c5 = Constraint(model.J, model.A, rule=c5_rule)

        # 处理比例控制
        def c7_rule(mod, j, a):
            return mod.mu[j, a] <= mod.z[j, a]
        model.c7 = Constraint(model.J, model.A, rule=c7_rule)

        # 放置资源约束
        def c9_rule(mod, j):
            return sum(mod.z[j, a] * mod.Ha[a] for a in mod.A) <= mod.Hmax[j]
        model.c9 = Constraint(model.J, rule=c9_rule)

        # 时延约束：每个边的运行时间要小于时隙长度
        def c10_rule(mod, j):
            return mod.total_time_of_edge[j] <= mod.delta
        model.c10 = Constraint(model.J, rule=c10_rule)

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
            (j, k, a): 0
            for j in model.J
            for k in model.J
            for a in model.A
        }
        for j in model.J:
            for k in model.J:
                for a in model.A:
                    if value(model.theta[j, k, a]) > 0:
                        y[(j, k, a)] = 1

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

