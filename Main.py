"""."""
import pulp as solver
from pulp import *
import Graph
from pprint import pprint
import os
import gc
import signal
from tqdm import tqdm
z = 0
solvers = [solver.CPLEX(timeLimit=7200), solver.GLPK(), solver.GUROBI(timeLimit=7200)]
solverUsado = 2

# #problems_packing = ["Instances/packing/" + i for i in os.listdir("Instances/packing/")]
# problems_sep = ["Instances/separated/" + i for i in os.listdir("Instances/separated/")]
instances = [
    # "albano.txt",
    # "blaz1.txt",
    # "blaz2.txt",
    # "blaz3.txt",
    # "dighe1.txt",
    # "dighe2.txt",
    # "fu.txt",
    # "instance_01_2pol.txt",
    # "instance_01_3pol.txt",
    "instance_01_4pol.txt",
    # "instance_01_5pol.txt",
    # "instance_01_6pol.txt",
    # "instance_01_7pol.txt",
    # "instance_01_8pol.txt",
    # "instance_01_9pol.txt",
    # "instance_01_10pol.txt",
    # "instance_01_16pol.txt",
    # "instance_artificial_01_26pol_hole.txt",
    # "rco1.txt",
    # "rco2.txt",
    # "rco3.txt",
    # "shapes2.txt",
    # "shapes4.txt",
    # "spfc_instance.txt",
    # "trousers.txt",
]
# + problems_sep
# problems = list(map(lambda x: "Instances/packing/" + x, instances)) + \
problems = list(map(lambda x: "Instances/separated/" + x, instances))
# problems = problems_packing  # + problems_sep
# print(problems)
# problems = problems[3:]


def signal_handler(signum, frame):
    """."""
    raise Exception("Timed out!")


for ptk in problems:
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(8100)
    try:
        print("Initializing graph", ptk)
        g = Graph.Graph(400, 16.67, z)
        g.initProblem(ptk)
        g.z = len(g.edgeCuts)
        print("Initializing variables X")
        var = [(uv + ',' + str(i + 1)) for uv in g.edgeCuts for i in range(g.z)]
        print("Initializing variables Y")
        var2 = [(uv + ',' + str(i + 1)) for uv in g.edge for i in range(g.z)]
        X = solver.LpVariable.dicts("X", var, cat=solver.LpBinary)
        Y = solver.LpVariable.dicts("Y", var2, cat=solver.LpBinary)
        problem = solver.LpProblem("The_best_Cut", solver.LpMinimize)
        km = set()
        list(km.add(uv) for uv in g.edgeCuts if not (uv in km or uv[::-1] in km))
        K = sum(
            [
                g.pis[uv.split(',')[0]][uv.split(',')[1]]
                for uv in km
            ]
        )
        problem += (
            solver.lpSum(
                0
                if str(uv.split(',')[1]) == str(wp.split(',')[0])
                else g.mis[uv.split(',')[1]][wp.split(',')[0]] * Y.get(
                    str(uv.split(',')[1]) + ',' +
                    str(wp.split(',')[0]) + ',' +
                    str(i + 1)
                )
                for wp in (g.edge)
                for uv in (g.edge)
                for i in (range(g.z))
            ) + K
        )
        print("Initializing First Restriction")
        for uv in tqdm(g.edgeCuts):  # uv \e R
            problem += solver.lpSum(
                X.get(
                    str(uv.split(',')[0]) + ',' +
                    str(uv.split(',')[1]) + ',' +
                    str(i + 1)
                ) for i in range(g.z)
            ) <= 1
        print("Initializing Second Restriction")
        for i in tqdm(range(g.z)):  # Q : 1 .. Q
            problem += solver.lpSum(
                X.get(
                    str(uv.split(',')[0]) + ',' + 
                    str(uv.split(',')[1]) + ',' +
                    str(i + 1)
                ) + X.get(
                    str(uv.split(',')[1]) + ',' +
                    str(uv.split(',')[0]) + ',' + 
                    str(i + 1)
                ) for uv in g.edgeCuts
            ) >= 1
        print("Initializing Third Restriction")
        for vw in tqdm(list(set(g.edge) - set(g.edgeCuts))):  # E - R
            for i in range(1, g.z):
                problem += (
                    solver.lpSum(
                        X.get(
                            str(vw.split(',')[1]) + ',' + 
                            str(v) + ',' +
                            str(i)
                        )
                        for v in g.arrive(vw.split(',')[1])
                    ) + ((solver.lpSum(
                        X.get(
                            str(w) + ',' + 
                            vw.split(',')[0] + ',' + 
                            str(i + 1)
                        )
                        for w in g.arrive(vw.split(',')[0])
                    )) - 1)
                ) <= Y.get(','.join(vw.split(',')[:2]) + ',' + str(i))
        print("Initializing Solver")
        st = problem.solve(solvers[solverUsado])
        tempos = open("tempos.txt", "a+")
        res = ""
        solucionador = {0: "CPLEX", 1: "GLPK", 2: "GUROBI"}[solverUsado]
        if problem.status == 1:
            res = "OPTIMAL"
        else:
            res = "TL exceeded"
        tempos.writelines(
            "PROBLEM: " + ptk.replace(".txt", "") + ""
            ", F.O: " + str(solver.value(problem.objective)) + ""
            ", TIME: " + str(problem.solutionTime) + ""
            " is_Optimal: " + res + ""
            " Solver: " + solucionador + "\n"
        )
        tempos.close()
        valuesX = {}
        valuesY = {}
        try:
            print("Getting results...")
            for k in problem.variables():
                # if(solver.value(k) > 0):
                if(k.name.split('_')[0] == 'X'):
                    valuesX[k] = solver.value(k)
                if(k.name.split('_')[0] == 'Y'):
                    valuesY[k] = solver.value(k)
            result = open("Results-model/" + ptk.split("/")[1] + ""
                          "/" + ptk.split("/")[-1], "a+")
            for k, v in valuesX.items():
                result.write(f"{k} {v}\n")
            for k, v in valuesY.items():
                result.write(f"{k} {v}\n")
            result.close()
            # valuesOr = [None for i in range(len(values))]
            # for i in values:
            #     ind = int(i.name.split(',')[2])
            #     cut = i.name.split(',')[0].split('_')[1] + ',' + i.name.split(',')[1]
            #     valuesOr[ind - 1] = cut
            # try:
            #     os.makedirs("Results/" + ptk.split("/")[-1].split(".")[0])
            # except Exception:
            #     pass
            # g.plotCuts(
            #     "Results/" + ptk.split("/")[-1].split(".")[0] + ""
            #     "/" + ptk.split("/")[-1].replace(".txt", "")
            # )
            # g.plotCor(
            #     "Results/" + ptk.split("/")[-1].split(".")[0] + ""
            #     "/" + ptk.split("/")[-1].replace(".txt", "")
            # )
            # g.plotDesloc(
            #     valuesOr, "Results/" + ptk.split("/")[-1].split(".")[0] + ""
            #     "/" + ptk.split("/")[-1].replace(".txt", "")
            # )
            # g.plotSolution(
            #     valuesOr, "Results/" + ptk.split("/")[-1].split(".")[0] + ""
            #     "/" + ptk.split("/")[-1].replace(".txt", "")
            # )
        except Exception as e:
            print("Fail problem", ptk, "error", str(e))
    except Exception as e:
        res = "TL exceeded "
        tempos = open("tempos.txt", "a+")
        tempos.writelines(
            "PROBLEM: " + ptk.replace(".txt", " ") + ""
            ", F.O: -1"
            " TIME: 2h"
            " is_Optimal: " + res + "\n"
        )
        tempos.close()
        print(e)
        pass
    # del problem
    # del X
    # del Y
    # del g
    gc.collect()
