import collections
import numpy as np
import math
import random

"""
La node ne change pas les paramètre de la Node
Sert également de classe de base pour la hiérachie des object qui permettent le choix des paramètres
"""
class Static:
    def chooseParameter(self, power=0, SF=7, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        return SF, power

    def start(self, n_arms):
        pass

    def select_arm(self, useless):
        pass


# Si collision, les paramètre sont tirés aléatoirement dans les paramètres valides
class RandChoice(Static):
    def chooseParameter(self, power=0, SF=7, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        if lostPacket:
            if not validCombination:
                return 7, 0
            return random.choice(validCombination)
        else:
            return SF, power


# Un ADR approximatif qui augmente la puissance en priorité, puis la sf si la puissance a atteint son maximum
class ADR(Static):

    def __init__(self):
        self.power = np.random.randint(0, 20)
        self.sf = np.random.randint(7,12)
        self.twenty = False
        self.snr = collections.deque(maxlen=20)
        self.margin = 0
        self.required = [-7.5, -10, -12.5, -15, -17.5, -20]
        self.noise = 6  # bruit définit au hasard
        self.counter = 0

    def computeGain(self, SF):
        Rc = 125000
        Rb = SF * 1 / ((2 ** SF) * 125000)
        return 10 * np.log10(Rc / Rb)

    # Calcul du Signal To Noise Ratio
    def computeSNR(self, power, SF):
        val = 20 * np.log(power / self.noise)
        self.snr.append(val)

    def computemargin(self, SF):
        return max(self.snr) - self.required[SF % 7] - self.margin

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        if not lostPacket:
            Gp = 0#self.computeGain(SF)
            self.computeSNR(power + Gp, SF)
            Nstep = round(self.computemargin(SF) / 3)
            if Nstep < 0:
                if power < 17:
                    power += 3
                elif power < 20:
                    power += 20 - power
            else:
                if power > 0:
                    power -= 1
                elif SF > 7:
                    SF -= 1
        if lostPacket:
            if power < 17:
                power += 3
            elif power < 20:
                power += (20 - power)
            if SF < 11:
                SF += 1

        return SF, power


class UCB1(Static):

    def __init__(self):
        super().__init__()
        self.counts = []
        self.values = []

    def start(self, n_arms=0):
        self.counts = [0 for col in range(n_arms)]
        self.values = [1 for col in range(n_arms)]
        print(n_arms)
        self.n_arms = n_arms
        self.old_arm = 0
        self.select_arm()

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        cost = (energyCost / 0.046)  # + 0.5 * (self.chosen[self.old_arm]/self.iteration)  # + int(definitelyLost)
        reward = 1-cost if not lostPacket else -1 # 1-(self.packet.energyCost/0.7)
        self.update(chosen_arm=self.old_arm, reward=reward)
        arm = self.select_arm()
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self):
        """ Selectionne le bras avec la valeur de l'estimateur la plus haute"""
        # Parcours des choix qui n'ont pas encore été visités
        for arm in range(self.n_arms):
            if self.counts[arm] == 0:
                self.old_arm = arm
                return arm
        ucb_values = [0.0 for arm in range(self.n_arms)]
        total_counts = sum(self.counts)
        # Calcul des valeurs d'UCB1 pour les différents choix
        for arm in range(self.n_arms):
            bonus = math.sqrt(2*(math.log(total_counts)) / float(self.counts[arm]))
            ucb_values[arm] = self.values[arm] + 0.05 * bonus
        # On choisit celui avec la valeur la plus élevée
        value_max = max(ucb_values)
        self.old_arm = ucb_values.index(value_max)
        return self.old_arm

    def update(self, chosen_arm, reward):
        self.counts[chosen_arm] += 1
        n = self.counts[chosen_arm]
        value = self.values[chosen_arm]
        new_value = ((n - 1) / float(n)) * value + (1 / float(n)) * reward
        self.values[chosen_arm] = new_value



# Version d'Exp3 trouvée sur internet et qui donne des résultats différents de ma version
class Exp3(Static):

    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        self.n_arms = n_arms
        self.counts = [0 for col in range(n_arms)]
        self.G = [0 for col in range(n_arms)]
        self.t = 0
        self.old_arm = 0
        self.select_arm(0.1)

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        cost = (energyCost / 0.046)  # + int(definitelyLost)
        reward = 1-cost if not lostPacket else -10 # 1-(self.packet.energyCost/0.7)
        self.update(self.old_arm, reward)
        arm = self.select_arm(0.01)
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self, eta):
        def tirage_aleatoire_avec_proba(proba_vect):
            valeur_test = random.uniform(0, 1)
            arm_chosen = -1
            i = 0
            sum_partiel = 0
            while i <= len(proba_vect) and arm_chosen == -1:
                sum_partiel += (proba_vect[i])
                if sum_partiel > valeur_test:
                    arm_chosen = i
                i += 1
            return arm_chosen

        self.proba_vect = [0 for col in range(self.n_arms)]

        #####################################
        # ALGO CALCUL DU Pi
        max_G = max(self.G)
        sum_exp_eta_x_Gjt_max_G = 0
        self.t += 1

        for i in range(len(self.G)):
            sum_exp_eta_x_Gjt_max_G += math.exp(eta * (self.G[i] - max_G))
        for i in range(len(self.proba_vect)):
            self.proba_vect[i] = math.exp(eta * (self.G[i] - max_G)) / float(sum_exp_eta_x_Gjt_max_G)

        ######################################

        arm_chosen = tirage_aleatoire_avec_proba(self.proba_vect)
        self.old_arm = arm_chosen
        return arm_chosen

    def update(self, chosen_arm, reward):
        self.counts[chosen_arm] += 1
        if self.counts[chosen_arm] != 1:
            if self.proba_vect[chosen_arm] != 0:
                if self.proba_vect[chosen_arm] < 0.01:  # Pour eviter les problemes de limite de calcul
                    self.G[chosen_arm] = float(self.G[chosen_arm]) + (float(reward) / 0.01)
                else:
                    self.G[chosen_arm] = float(self.G[chosen_arm]) + (
                            float(reward) / float(self.proba_vect[chosen_arm]))
        else:
            self.G[chosen_arm] = reward

#Fonction Thompson Sampling
#Basé sur la distribution bêta
class ThompsonSampling(Static):
    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        self.a = [1 for arm in range(n_arms)]
        self.b = [1 for arm in range(n_arms)]
        self.n_arms = n_arms
        self.modified = True
        self.first = [True for arm in range(n_arms)]
        self.all_draws = [0 for i in range(n_arms)]
        self.old_arm = 0
        self.select_arm(0.1)

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0, nodeID=1,
                        rectime=0):
        cost = float(energyCost / 0.046)  # + 0.5 * (self.chosen[self.old_arm]/self.iteration)  # + int(definitelyLost)
        reward = 1 - cost if not lostPacket else 0  # 1-(self.packet.energyCost/0.7)
        self.update(self.old_arm, reward)
        arm = self.select_arm(0.1)
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self, useless):
        """Thompson Sampling : sélection de bras"""
        if self.modified:
            # On groupe toutes les paires de a et b et on tire une valeur selon distribution béta
            self.all_draws = np.random.beta(self.a, self.b,
                                            size=(1, self.n_arms))
            self.all_draws = np.concatenate(self.all_draws, axis=0)
            self.old_arm = np.argmax(self.all_draws)
        return self.old_arm

    def update(self, chosen_arm, reward):
        """Choix du bras à mettre à jour"""
        # epsilon correpsond à la probabilité de mettre à jour a et b (basé sur Adaptative rate Thomspon Sampling de Basu et Ghosh)
        epsilon = 1
        omega = random.random()
        if omega <= epsilon:
            # a est basé sur les succès
            self.a[chosen_arm] = self.a[chosen_arm] + reward
            # b est basé sur les échecs
            self.b[chosen_arm] = self.b[chosen_arm] + (1 - reward)
            self.modified = True
        else:
            self.modified = False

"Le nombre de réémissions correspond aux états"
class qlearning(Static):

    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        n_reemit = 9
        self.q_matrix = []
        self.n_arms = n_arms
        one_vector = [0 for i in range(n_arms)]
        for i in range(n_reemit):
            self.q_matrix.append(one_vector)
        self.state = 0
        self.old_action = 0
        self.select_arm(0, 0.1)

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        if lostPacket:
            cost = -1
        else:
            cost = -energyCost
        self.update(cost, self.state, self.old_action, nbSend)
        arm = self.select_arm(state=nbSend, lostPacket=lostPacket, epsilon=0.1)
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self, state, lostPacket, epsilon=1):
        self.state = state
        self.old_action = np.argmax(self.q_matrix[state])
        if (random.uniform(0, 1) < epsilon):
            self.old_action = random.randint(0, self.n_arms - 1)
        return self.old_action

    def update(self, reward, state, action, newstate):
        gamma = 0.6
        alpha = 0.1
        newaction = np.argmax(self.q_matrix[newstate])
        self.q_matrix[state][action] = self.q_matrix[state][action] + alpha * (
                reward + gamma * self.q_matrix[newstate][newaction] - self.q_matrix[state][action])

############################################ Méthodes expérimentales(pas forcément utile) ##############################################

#Parcours toutes les stratégies et fait une moyenne
class AB(Static):
    def __init__(self, k=0, n_arms=0):
        # bras actuel
        self.index = 0
        # taille du batch
        self.k = k
        self.utilities = [0.0 for col in range(n_arms)]
        self.n_arms = n_arms

    def select_arm(self, lr):
        """ Selectionne le bras avec la valeur de recommandation la plus haute"""
        old_index = self.index
        self.index = self.index + 1
        if old_index < self.k:
            return old_index % self.n_arms
        else:
            return self.utilities.index(max(self.utilities))

    def update(self, chosen_arm, reward):
        self.utilities[chosen_arm] += reward

#Fonction Exp3 basée sur d'autres articles
class MyExp3(Static):

    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        # poids attribués par bras
        self.weights = [1 for i in range(0, n_arms)]
        # probabilité d'utiliser
        self.proba = [1 for i in range(0, n_arms)]
        # nombre de bras
        self.n_arms = n_arms
        # paramètre à régler
        self.gamma = 1
        self.old_arm = 0
        self.select_arm(0.1)

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        if lostPacket:
            reward = -10
        else:
            cost = energyCost
            reward = -cost  # -energyCost#0.2 #- (cost / 1.7)  # 1-(self.packet.energyCost/0.7)
        self.update(self.old_arm, reward)
        arm = self.select_arm(0.1)
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self, lr=0):
        # Mise à jour de la probabilité des bras
        for i in range(0, self.n_arms):
            self.proba[i] = (1 - self.gamma) * (self.weights[i] / np.sum(self.weights)) + self.gamma / self.n_arms
        # Sélection d'un bras selon la distribution
        tmpSum = 0
        randomVal = random.random()
        for i in range(self.n_arms):
            tmpSum += self.proba[i]
            if randomVal <= tmpSum:
                self.old_arm = i
                return i
        self.old_arm = self.proba[self.n_arms - 1]
        return self.proba[self.n_arms - 1]

    def update(self, chosen_arm, reward):
        estimated = reward / self.proba[chosen_arm]
        self.weights[chosen_arm] = self.weights[chosen_arm] * np.exp((self.gamma / self.n_arms) * estimated)
        self.weights /= sum(self.weights)


#Amélioration supposée de Thompson Sampling, visant à renvoyer soit la meilleure, soit la deuxième meilleure action
class TopTwoThompsonSampling(Static):

    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        self.a = [1 for arm in range(n_arms)]
        self.b = [1 for arm in range(n_arms)]
        self.index = 0
        self.n_arms = n_arms
        self.previous_reward = 0
        self.modified = True
        self.all_draws = [0 for i in range(n_arms)]
        self.old_arm = 0
        self.select_arm(0.1)

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        if lostPacket:
            cost = 1
        else:
            cost = (energyCost / 0.046)
        # cost = (energyCost / 0.046) if not lostPacket == False else 0  # + int(definitelyLost)
        reward = 1 - cost  # 1-(self.packet.energyCost/0.7)
        self.update(self.old_arm, reward)
        arm = self.select_arm(0.1)
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self, useless):
        if self.modified:
            # Tirage aléatoire basée sur les paramètres a et b
            self.all_draws = np.random.beta(self.a, self.b,
                                            size=(1, self.n_arms))
            self.all_draws = np.concatenate(self.all_draws, axis=0)

        # On retourne la meilleure ou la deuxième meilleure action selon une loi uniforme
        self.old_arm = np.random.choice(self.all_draws.argsort()[::-1]
                                        [:2])
        return self.old_arm

    def update(self, chosen_arm, reward):
        epsilon = 1
        omega = random.random()
        if omega <= epsilon:
            self.a[chosen_arm] = self.a[chosen_arm] + reward
            self.b[chosen_arm] = self.b[chosen_arm] + (1 - reward)
            self.modified = True
        else:
            self.modified = False
        self.previous_reward = reward

#Qlearning ou le epsilon greedy est guidé. Si on a un échec de transmissions, l'exploration se fait vers les paramètres plus élevés, sinon ver les paramètres moins élevés
class qlearningCustom(Static):

    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        n_reemit = 9
        self.q_matrix = []
        self.n_arms = n_arms
        one_vector = [0 for i in range(n_arms)]
        for i in range(n_reemit):
            self.q_matrix.append(one_vector)
        self.state = 0
        self.old_action = 0
        self.select_arm(0, 0.1)

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        #cost = energyCost * (nbSend + 1) + int(lostPacket)
        reward = -energyCost  # 1 - cost / 7.5  # 1-(self.packet.energyCost/0.7)
        self.update(reward, self.state, self.old_action, nbSend)
        arm = self.select_arm(state=nbSend, lostPacket=lostPacket, epsilon=0.1)
        sf = validCombination[arm][0]
        power = validCombination[arm][1]
        return sf, power

    def select_arm(self, state, lostPacket, epsilon=1):
        self.state = state
        if (random.uniform(0, 1) < epsilon):
            if lostPacket:
                self.old_action = random.randint(self.old_action, self.n_arms - 1)
            else:
                self.old_action = random.randint(0, self.old_action)
        else:
            self.old_action = np.argmax(self.q_matrix[state])
        return self.old_action

    def update(self, reward, state, action, newstate):
        gamma = 0.6
        alpha = 0.1
        newaction = np.argmax(self.q_matrix[newstate])
        self.q_matrix[state][action] = self.q_matrix[state][action] + alpha * (
                reward + gamma * self.q_matrix[newstate][newaction] - self.q_matrix[state][action])

######################################Pour le DQN############################

"""
    Algortihme qui dispose d'un vecteur de stratégie trié par ordre croissant de portée
    On commence sur la première statégie (indice 0). En cas d'échec, on augmente l'indice
    La dernière stratégie doit être assurée de porter assez loin.
"""
class smartADR(Static):

    def __init__(self):
        super().__init__()

    def start(self, n_arms=0):
        self.n_arms = n_arms
        self.index = 0
        self.recommanded = True

    def chooseParameter(self, power=0, SF=0, lostPacket=False, validCombination=None, nbSend=0, energyCost=0):
        if lostPacket and (self.index < self.n_arms - 1):
            self.index += 1
        elif not lostPacket and self.index > 0:
            self.index -= 1
        if self.index == 0:
            self.recommanded = True
        else:
            self.recommanded = False
        sf = validCombination[self.index][0]
        power = validCombination[self.index][1]
        return sf, power
