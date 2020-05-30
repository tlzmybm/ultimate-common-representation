import torch
import torch.nn as nn
from tqdm import tqdm
from cifar10 import CNN
from data_cifar10 import *

class SimpleConv(nn.Module):
    def __init__(self, index1, index2):
        super(SimpleConv, self).__init__()
        tmp = CNN()
        self.conv_layers = tmp.conv_layers[index1:index2]
        self.convs = nn.Sequential(*self.conv_layers)

    def forward(self, x):
        for layer in self.conv_layers:
            x = layer(x)
        return x

class Ensemble(nn.Module):
    def __init__(self, model1, model2, index1, index2, conv):
        super(Ensemble, self).__init__()
        self.conv_layers = model1.conv_layers[:index1] + conv.conv_layers + model2.conv_layers[index2:]
        self.convs = nn.Sequential(*self.conv_layers)
        self.out = model2.out

    def forward(self, x):
        for layer in self.conv_layers:
            x = layer(x)
        output = self.out(x).view(-1, 10)
        return output

if __name__ == '__main__':
    device = torch.device('cuda')

    model1 = CNN().to(device)
    model2 = CNN().to(device)
    
    model1.load_state_dict(torch.load('./models/CIFAR10_no_dropout/advsc/model_epoch_9_1.pt'))
    model2.load_state_dict(torch.load('./models/CIFAR10_no_dropout/advsc/model_epoch_9_2.pt'))

    model1.eval()
    model2.eval()

    INDEX1 = 1
    INDEX2 = 3

    conv12 = SimpleConv(INDEX1, INDEX2).to(device)
    conv12.train()

    optimizer = torch.optim.Adam(list(conv12.parameters()))
    loss_f = nn.MSELoss()

    EPOCH = 20

    for epoch in range(EPOCH):
        run_loss = 0
        for x, y in tqdm(train_loader, desc = 'Epoch {:d}/{:d}'.format(epoch, EPOCH)):
            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad()            
            model1(x)
            model2(x)
            f11 = model1.feat[INDEX1 - 1].detach()
            f22 = model2.feat[INDEX2 - 1].detach()

            optimizer.zero_grad()
            pred_f22 = conv12(f11)
            loss = loss_f(pred_f22, f22)
            loss.backward()
            optimizer.step()
            run_loss += loss.item()

        print('Train Loss of Converter: {:.5f}'.format(run_loss / len(train_loader)))
