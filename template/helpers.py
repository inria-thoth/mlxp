from torchvision.datasets import CIFAR10
import torchvision.transforms as transforms


import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim




from models.models import LinearNNModel


def get_data_loader(args,b_size,num_workers):
    transform_train = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    transform_test = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])
    if args.dataset == 'cifar10':
        spatial_size = 32

        trainset = CIFAR10(root='./data/', train=True, download=True, transform=transform_train)
        trainloader = torch.utils.data.DataLoader(trainset, batch_size=b_size, shuffle=True, num_workers=num_workers)
        n_classes=10
        testset = CIFAR10(root='./data/', train=False, download=True, transform=transform_test)
        testloader = torch.utils.data.DataLoader(testset, batch_size=b_size, shuffle=False, num_workers=num_workers)

    return trainloader,testloader, testloader, n_classes


def get_optimizer(args, params):
    if args.optimizer == 'Adam':
        optimizer = optim.Adam(params, lr=args.lr, weight_decay=args.weight_decay, betas = (args.beta_1,args.beta_2))
    elif args.optimizer == 'SGD':
        optimizer = optim.SGD(params, lr=args.lr, momentum=args.sgd_momentum, weight_decay=args.weight_decay)
    else:
        raise NotImplementedError('optimizer {} not implemented'.format(args.optimizer))
    return optimizer

# schedule the learning
def get_scheduler(args,optimizer):
    if args.scheduler=='MultiStepLR':
        if args.milestone is None:
            lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=[int(args.total_epochs*0.5), int(args.total_epochs*0.75)], gamma=args.lr_decay)
        else:
            milestone = [int(_) for _ in args.milestone.split(',')]
            lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(optimizer, milestones=milestone, gamma=args.lr_decay)
        return lr_scheduler
    elif args.scheduler=='ExponentialLR':
        return optim.lr_scheduler.ExponentialLR(optimizer, gamma=args.scheduler_gamma)

def get_model(args, input_dim, num_classes):
    if args.model=='linear':
        return LinearNNModel(input_dim, num_classes)

def assign_device(device):
    if device >-1:
        device = 'cuda:'+str(device) if torch.cuda.is_available() and device>-1 else 'cpu'
    elif device==-1:
        device = 'cuda'
    elif device==-2:
        device = 'cpu'
    return device


