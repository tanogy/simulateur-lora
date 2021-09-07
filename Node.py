from Battery import Battery
from func import calcDistMax, aleaCoord, Packet
from learn import *


class Node:
    """
    nodeid : id de la node
    period : temps moyen entre deux envoi de message (en ms)
    sf : spreading factor (entier compris entre 7 et 12)
    cr : coding rate (entier compris entre 1 et 4)
    bw : bandwith (125, 250 ou 500)
    coord : coordonées (x,y) de la node
    power : puissance d'émition des message en dB (entier compris entre -2 et 20 dB)
    packetLen : taille du packet
    freq : fréquence de la porteuse (860000000, 864000000, 868000000 hz)
            (peut valoir un entier entre 860000000 et 1020000000 par pas de 61hz, raport )
    packetSent : nombre de paquet envoyés
    firstSendPacket : compteur du nombre de première émition d'un paquet
    packetLost : compteur du nombre de packet perdu
    packetTotalLost : compteur du nombre de packet qui n'on jamais été reçu
    validCombination : liste contenant les combinaison de paramètre valide
    waitTime : temps pendant lequel le noeud doit attendre au minimum avant de réémètre
    sendTime : temps ou le noeud à pour la dernière fois émis
    TX : tableau des rapport puisance et milliAmpère-Heure
    algo : objet corespondant a l'algorithme permètant les choix SF / puissance
    active : booléen signifiant si le noeud emmet ou non
    battery : objet corespondant à la batterie du noeud
    waitPacket : liste des packet en attente /! pas utilisé
    """

    def __init__(self, nodeId: int, period: int, sensi, TX, packetLen=20, cr=1, bw=125, sf=7, power=14, coord=None,
                 radius=200, algo=Static()):
        if coord is None:
            coord = aleaCoord(radius)
        self.nodeId = nodeId
        self.period = period
        self.sf = sf
        self.cr = cr
        self.bw = bw
        self.coord = coord
        self.power = power
        self.packetLen = packetLen
        self.freq = random.choice([860000000, 864000000, 868000000])
        self.packetSent = 0
        self.firstSentPacket = 0
        self.packetLost = 0
        self.packetTotalLost = 0
        self.validCombination = self.checkCombination(sensi)
        self.waitTime = 0
        self.sendTime = 0
        self.TX = TX
        self.algo = algo
        self.algo.start(n_arms=len(self.validCombination))
        if isinstance(self.algo, Static) or isinstance(self.algo, RandChoise):
            self.sf = sf
            self.power = power
        else:
            self.sf = self.validCombination[0][0]
            self.power = self.validCombination[0][1]
        self.active = False
        self.battery = Battery(10000000)
        self.waitPacket = []

    # construction de la liste contenant les combinaisons de paramètre valide (SF + Power)
    # sensi : tableau des sensibilité de l'antenne
    def checkCombination(self, sensi=[]):
        lTemp = []
        maxDist = calcDistMax(sensi)
        for i in range(len(maxDist)):
            for j in range(len(maxDist[i])):
                if maxDist[i][j] > math.sqrt((self.coord.x - 0) ** 2 + (self.coord.y - 0) ** 2):
                    lTemp.append([i + 7, j + 2])
        return lTemp

    def __str__(self):
        return "node : {:<4d} sf : {:<3d} packetSent : {:<6d} packetLost : {:<6d} messageLost : {:<6d} power : {:<3d}".format(
            self.nodeId, self.sf, self.packetSent, self.packetLost, self.messageLost, self.power)

    # Création d'un paquet corespondant aux paramètres de la node
    def createPacket(self, idPacket) -> Packet:
        p = Packet(self.nodeId, self.packetLen, self.sf, self.cr, self.bw, self.coord, self.power, self.TX, idPacket, self.freq)
        return p

    # définit le temps d'attente minimum avant le prochain envoie (99 fois le temps d'envoie)
    # time : temps ou le noeud à précédament été utilisé
    # sendTime : temps actuelle de la simulation
    def setWaitTime(self, time: float, sendTime: float):
        self.waitTime = 99 * time
        self.sendTime = sendTime
