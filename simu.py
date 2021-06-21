class Simu:
    def __init__(self):
        self.events = []
        self.simTime = 0
        self.envData = {}

    def __str__(self):
        ret = ""
        for ev in self.events:
            ret = ret + " " + str(ev)
        return ret

    #ajout d'un event dans l'échéancier
    def addEvent(self, event):
        if self.events:
            cont = len(self.events)
            while cont > 0 and self.events[cont-1].time < event.time:
                cont -= 1
            self.events.insert(cont, event)
        else:
            self.events.append(event)

    # méthode qui renvoie l'évènement suivant
    def nextEvent(self):
        if self.events:
            nextEvent = self.events.pop()
            if self.events:
                if nextEvent.time > self.events[-1].time:
                    print(nextEvent.time, "---", self.events[-1])
            nextEvent.exec()

    #ajoute une entrée dans le dictionnaire contenant les données de la simulation
    def addData(self, value, key):
        self.envData[key] = value

# super-class corespondant aux evenements
class Event:
    def __init__(self, time, env: Simu):
        self.time = time
        self.env = env

    def __lt__(self, other) -> bool:
        return self.time < other.time

    def __str__(self):
        return "time : " + str(self.time)

    def exec(self):
        print(self.time)
