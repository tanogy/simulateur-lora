import os
import torch as T
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy as np

class DeepQNetwork(nn.Module):
    def __init__(self, lr, n_actions, name, input_dims, chkpt_dir):
        super(DeepQNetwork, self).__init__()
        self.checkpoint_dir = chkpt_dir
        self.checkpoint_file = os.path.join(self.checkpoint_dir, name)
        print("lr = ", lr)
        self.fc1 = nn.Linear(*input_dims, 96)
        self.activation1 = nn.Tanh()
        self.fc2 = nn.Linear(96, 96)
        self.activation2 = nn.Tanh()
        self.fc3 = nn.Linear(96, 96)
        self.activation3 = nn.Tanh()
        self.fc4 = nn.Linear(96, 96)
        self.activation4 = nn.Tanh()
        self.fc5 = nn.Linear(96, 96)
        self.activation5 = nn.Tanh()
        self.fc6 = nn.Linear(96, 96)
        self.activation6 = nn.SiLU()
        self.fc7 = nn.Linear(96, 96)
        self.activation7 = nn.SiLU()
        self.fc8 = nn.Linear(96, 96)
        self.activation8 = nn.SiLU()
        self.fc9 = nn.Linear(96, 96)
        self.activation9 = nn.SiLU()
        self.fc10 = nn.Linear(96, 96)
        self.activation10 = nn.SiLU()
        self.fc11 = nn.Linear(96, 96)
        #self.activation11 = nn.SiLU()
        self.V = nn.Linear(96, 1)
        self.A = nn.Linear(96, n_actions)
        self.optimizer = optim.AdamW(self.parameters(),lr=lr)
        self.loss = nn.MSELoss()
        self.device = T.device('cuda:0' if T.cuda.is_available() else 'cpu')
        self.to(self.device)

    def calculate_conv_output_dims(self, input_dims):
        state = T.zeros(1, *input_dims)
        dims = self.conv1(state)
        dims = self.conv2(dims)
        dims = self.conv3(dims)
        return int(np.prod(dims.size()))

    def forward(self, state):
        x = self.activation1(self.fc1(state))
        x = (self.fc4(x))
        x = self.activation7(self.fc11(x))
        #x8 = self.activation9(self.fc9(x7))
        #x9 = self.activation10(self.fc10(x8))
        #x10 = self.activation11(self.fc11(x9))
        V = self.V(x)
        A = self.A(x)
        return V, A

    def save_checkpoint(self):
        print('... saving checkpoint ...')
        T.save(self.state_dict(), 'network')

    def load_checkpoint(self):
        print('... loading checkpoint ...')
        self.load_state_dict(T.load('network'))