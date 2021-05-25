import random

import numpy as np

from LoRa.Event import sendPacketEvent, timmerEvent
from LoRa.Node import Node
from LoRa.simu import Simu

# tableau des sensitivity par sf (en fonction du bandwidth)
# variable de LoRaSim
sf7 = np.array([7, -126.5, -124.25, -120.75])
sf8 = np.array([8, -127.25, -126.75, -124.0])
sf9 = np.array([9, -131.25, -128.25, -127.5])
sf10 = np.array([10, -132.75, -130.25, -128.75])
sf11 = np.array([11, -134.5, -132.75, -128.75])
sf12 = np.array([12, -133.25, -132.25, -132.25])
sensi = np.array([sf7, sf8, sf9, sf10, sf11, sf12])
# tableau de distance maximum
TX = [22, 22, 22, 23,  # RFO/PA0: -2..1
      24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44,  # PA_BOOST/PA1: 2..14
      82, 85, 90,  # PA_BOOST/PA1: 15..17
      105, 115, 125]  # PA_BOOST/PA1+PA2: 18..20

s = Simu()
s.addData([], "nodes")
s.addData([], "packetsAtBS")
s.addData(sensi, "sensi")
s.addData(TX, "TX")
s.addData(200, "radius")
s.addData([[], [], [], [], [], [], []], "packetPerSF")

simTime = 1800000000
s.addEvent(timmerEvent(0, s, simTime))
for i in range(100):
    s.envData["nodes"].append(Node(0, 1800000, s.envData["sensi"], s.envData["TX"]))
    s.addEvent(sendPacketEvent(i, random.expovariate(1.0 / s.envData["nodes"][i].period), s))

while s.simTime < simTime:
    s.nextEvent()