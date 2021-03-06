import os

import numpy as np
import torch as T
from deep_q_network import DeepQNetwork
from replay_memory import ReplayBuffer

"""Agent qui va contenir le deep q network"""
class DQNAgent(object):
    def __init__(self, gamma, epsilon, lr, n_actions, input_dims,
                 mem_size, batch_size, eps_min=0.01, eps_dec=5e-7,
                 replace=1000, algo=None, env_name=None, chkpt_dir='tmp/dqn'):
        self.gamma = gamma
        self.epsilon = epsilon
        self.lr = lr
        self.n_actions = n_actions
        self.input_dims = input_dims
        self.batch_size = batch_size
        self.eps_min = eps_min
        self.eps_dec = eps_dec
        self.replace_target_cnt = replace
        self.algo = algo
        self.env_name = env_name
        self.chkpt_dir = chkpt_dir
        self.action_space = [i for i in range(n_actions)]
        self.learn_step_counter = 0
        self.print = True
        self.memory = ReplayBuffer(mem_size, input_dims, n_actions)

        self.q_eval = DeepQNetwork(self.lr, self.n_actions,
                                    input_dims=self.input_dims,
                                    name='q_eval',
                                    chkpt_dir=self.chkpt_dir)

        if os.path.isfile("network"):
            self.q_eval.load_state_dict(T.load('network'))

    """Enregistre les informations à l'état i"""
    def store_transition(self, state, action, reward, state_, done):
        self.memory.store_transition(state, action, reward, state_, done)

    """Tire un jeu d'informations au hasard parmi ceux enregistrés. Permet d'entrainer le réseau de neurones"""
    def sample_memory(self):
        state, action, reward, new_state, done = \
                                self.memory.sample_buffer(self.batch_size)

        states = T.tensor(state).to(self.q_eval.device)
        rewards = T.tensor(reward).to(self.q_eval.device)
        dones = T.tensor(done).to(self.q_eval.device)
        actions = T.tensor(action).to(self.q_eval.device)
        states_ = T.tensor(new_state).to(self.q_eval.device)

        return states, actions, rewards, states_, dones

    """Choisit une action selon epsilon soft (décroissant)"""
    def choose_action(self, observation):
        if np.random.random() > self.epsilon:
            state = T.tensor([observation],dtype=T.float).to(self.q_eval.device)
            _, advantage = self.q_eval.forward(state)
            action = T.argmax(advantage).item()
        else:
            action = np.random.choice(self.action_space)

        return action

    """Diminue la valeur d'epsilon à chaque étape"""
    def decrement_epsilon(self):
        self.epsilon = self.epsilon - self.eps_dec \
                         if self.epsilon > self.eps_min else self.eps_min
        if self.epsilon<0.1 and self.print:
            print("petit")
            self.print = False

    """Entraine le réseau de neurones à partir d'un jeu de données tirer au hasard"""
    def learn(self):
        if self.memory.mem_cntr < self.batch_size:
            return

        self.q_eval.optimizer.zero_grad()

        states, actions, rewards, states_, dones = self.sample_memory()

        V_s, A_s = self.q_eval.forward(states) # Deux valeurs prédites conformément au dueling Q-network

        indices = np.arange(self.batch_size)

        q_pred = T.add(V_s,
                        (A_s - A_s.mean(dim=1, keepdim=True)))[indices, actions]
        q_target = rewards


        loss = self.q_eval.loss(q_target, q_pred).to(self.q_eval.device)
        loss.backward()
        self.q_eval.optimizer.step()
        self.learn_step_counter += 1

        self.decrement_epsilon()
        self.decrement_epsilon()

    """Fait appel au save checkpoint de deep_q_network.py"""
    def save_models(self):
        self.q_eval.save_checkpoint()

    """Fait appel au load checkpoint de deep_q_network.py"""
    def load_models(self):
        self.q_eval.load_checkpoint()