import random
import numpy as np
import math

import learn
from simu import Simu
from Event import mooveEvent, mooveDistEvent, sendPacketEvent
from Packet import Point
from Node import Node

# lecture du fichier de configuration de la sensibilité de l'entenne
def readSensitivity():
    try:
        sensi = []
        with open("config/sensitivity.txt", "r") as fi:
            lines = fi.readlines()
            for line in lines:
                line = line.split(" ")
                tmp = []
                for val in line:
                    if val:
                        tmp.append(val)
                tmp = [float(val) for val in tmp]
                sensi.append(np.array(tmp))
        return np.array(sensi)
    except ValueError:
        print("error in sensitivity.txt")
        exit()


# placement aléatoire des nodes sur un disque de rayon radius
def aleaPlacement(nbNode: int, radius: float):
    res = []
    for i in range(nbNode):
        a = random.random()
        b = random.random()
        if b < a:
            a, b = b, a
        posx = b * radius * math.cos(2 * math.pi * a / b)
        posy = b * radius * math.sin(2 * math.pi * a / b)
        res.append([posx, posy])
    return res


# placement des nodes sur une grille
def gridPlacement(sizeGrid: int, radius: float):
    lin = np.linspace(-radius, radius, sizeGrid)
    res = []
    for i in range(sizeGrid):
        for j in range(sizeGrid):
            if not lin[i] == 0 or not lin[j] == 0:
                res.append([lin[i], lin[j]])
    return res


# placement des nodes sur une ligne
def linePlacement(nbNode: int, radius: float):
    lin = np.linspace(0, radius, nbNode + 1)
    res = []
    for i in lin[1:]:
        res.append([i, 0])
    return res


# evaluation des paramètres des nodes
def evalParam(arg, settings, listAlgo):
    if arg[0] == "sf":
        if arg[1] == "rand" or (arg[1].isdigit() and 12 >= int(arg[1]) >= 7):
            settings["sf"] = arg[1]
        else:
            print("sf parameter must be: rand, 7 ,8 ,9 ,10 ,11 ,12")
            exit()
    elif arg[0] in ["period", "packetLen", "radius"]:
        if arg[1].isdigit():
            settings[arg[0]] = int(arg[1])
        else:
            print("parameter period must be a positive integer")
            exit()
    elif arg[0] == "cr":
        if arg[1].isdigit() and 4 >= int(arg[1]) >= 1:
            settings["cr"] = int(arg[1])
        else:
            print("period parameter must be a positive integer between 1 and 4")
            exit()
    elif arg[0] == "power":
        if arg[1].isdigit() and 20 >= int(arg[1]) >= 0:
            settings["power"] = int(arg[1])
        else:
            print("period parameter must be an integer between 0 and 20")
            exit()
    elif arg[0] == "algo":
        if arg[1] in listAlgo:
            settings["algo"] = arg[1]
        else:
            print("the algorithm", arg[1], "does not exist")
            exit()
    else:
        print("the argument", arg[0], "does not exist")
        exit()


# creation de l'objec algo
def createAlgo(algo, listAlgo, listObjAlgo):
    tmp = listAlgo.index(algo)
    return eval(listObjAlgo[tmp])


# lecture du fichier de configuration des algo de choix de paramètres (SF/Power)
def readConfigAlgo():
    listAlgo = []
    listObjAlgo = []
    with open("config/configAlgo.txt", "r") as fi:
        lines = fi.readlines()
        for line in lines:
            tmp = line.split()
            listAlgo.append(tmp[0])
            listObjAlgo.append(tmp[1])
    return listAlgo, listObjAlgo


# création de la node en fonction des paramètres
def placeNode(settings, listAlgo, listObjAlgo, coord, nodeId, env):
    if settings["sf"] == "rand":
        sf = random.randint(7, 12)
    else:
        sf = int(settings["sf"])
    algo = createAlgo(settings["algo"], listAlgo, listObjAlgo)
    env.envData["nodes"].append(
        Node(nodeId, settings["period"], env.envData["sensi"], env.envData["TX"], settings["packetLen"],
             settings["cr"], 125, sf, settings["power"], Point(coord[0], coord[1]), settings["radius"],
             algo))
    env.addEvent(sendPacketEvent(nodeId, random.expovariate(1.0 / env.envData["nodes"][nodeId].period), env, 0))


# lecture du fichier de configuration des nodes et création des nodes
def parseNode(line, env):
    listAlgo, listObjAlgo = readConfigAlgo()
    listFunc = [aleaPlacement, gridPlacement, linePlacement]
    listFuncArg = ["rand", "grid", "line"]
    nodeId = len(env.envData["nodes"])
    line = line.replace("\n", "")
    line = line.rstrip()
    settings = {"period": 1800000, "packetLen": 20, "cr": 1, "sf": "rand", "power": 14, "radius": 200,
                "algo": "rand"}
    paramSplit = []
    param = line.split()
    for arg in param:
        paramSplit.append(arg.split(":"))

    for arg in paramSplit[2:]:
        evalParam(arg, settings, listAlgo)
    if not param[0].replace(".", "").replace("-", "").isdigit():
        try:
            funcPlacement = listFunc[listFuncArg.index(param[0])]
        except ValueError:
            print(param[0], "should be : rand, grid, line")
            exit()
        try:
            place = funcPlacement(int(param[1]), int(settings["radius"]))
        except ValueError:
            print(param[1], "should be an integer")
            exit()
    else:
        try:
            place = [[float(param[0]), float(param[1])]]
        except ValueError:
            print("the coordinates must be float")
            exit()

    for coord in place:
        placeNode(settings, listAlgo, listObjAlgo, coord, nodeId, env)
        nodeId += 1

# placement des nodes à partir du fichier de configuration
def loadNodeConfig(env):
    with open("config/Nodes.txt", "r") as fi:
        lines = fi.readlines()
        for line in lines:
            parseNode(line, env)


# fonction qui sauvegarde la configuration des nodes de la simulation
def saveConfig(env):
    with open("res/saveENV.txt", "w") as fi:
        tmp = []
        listAlgo, listObjAlgo = readConfigAlgo()
        for algo in listObjAlgo:
            tmp.append(eval(algo))
        algo = tmp

        for nd in env.envData["nodes"]:
            for i in range(len(algo)):
                if type(nd.algo) is type(algo[i]):
                    fi.write(str(nd.coord.x) + " " + str(nd.coord.y) + " sf:" + str(nd.sf) + " period:" + str(nd.period)
                             + " cr:" + str(nd.cr) + " packetLen:" + str(nd.packetLen) + " power:" + str(nd.power)
                             + " algo:" + (listAlgo[i]) + "\n")

# chargement du tableau TX (consommation en mA en fonction de la puissance)
# pour le moment le tableau doit couvrir toutes les puissance entre -2 et 20
def loadTX():
    with open("config/TX.txt", "r") as fi:
        line = fi.readline()
        line = line.split()
        if not len(line) == 23:
            print("TX does not have the right number of arguments")
            exit()
        return [int(val) for val in line]


# lecture d'une commande de création moove et création e l'event associé
def parseMoove(env: Simu, line):
    if len(line) == 5: # déplacement vers un point
        try:
            time = int(line[2])
            x = int(line[3])
            y = int(line[4])
            nodeId = int(line[1])
            env.addEvent(mooveEvent(time, env, Point(x, y), nodeId))
        except ValueError:
            print("time, x or y is not an integer")
            exit()

    elif len(line) == 4: # déplacement vers une destination
        try:
            time = int(line[2])
            dist = int(line[3])
            nodeId = int(line[1])
            env.addEvent(mooveDistEvent(time, env, dist, nodeId))
        except ValueError:
            print("time, x or y is not an integer")
            exit()
    else:
        print("the moove event does not have the right number of arguments")
        exit()

# Lecture du fichier de configuration du scénario
def parseScenario(env: Simu):
    with open("config/scenario.txt", "r") as fi:
        lines = fi.readlines()
        for line in lines:
            line = line.split()
            if line[0] == "moove":
                parseMoove(env, line)
