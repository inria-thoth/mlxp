import math

import torch
import torch.nn as nn

import numpy as np

import csv
import sys
import os
import time
from datetime import datetime


# Don't forget to select GPU runtime environment in Runtime -> Change runtime type

import helpers as hp
#from pytorch_pretrained_biggan import BigGAN
#from  models.generator import BigGANwrapper

import models


from MLExp.experimentalist import Experimentalist
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec


class Trainer(Experimentalist):
    def __init__(self, args):
        super(Trainer, self).__init__(args)
        self.args = args
        #self.exp = Experiment(self.args)
        self.device = hp.assign_device(args.system.device)
        self.build_model()

    def build_model(self):

        self.train_loader, self.test_loader, self.valid_loader,self.num_classes = hp.get_data_loader(self.args.data,self.args.trainer.b_size, self.args.system.num_workers)
        dim_input = 3*32*32
        self.model = hp.get_model(self.args.model, dim_input, self.num_classes).to(self.device)
        # load models if path exists, define log partition if using kale and add to discriminator
        self.mode = 'train'
        if self.args.model.model_path is not None:
            self.load_model()
            self.model.eval()
        if self.mode == 'train':
            # optimizers
            self.optim = hp.get_optimizer(self.args.trainer.optimizer, self.model.parameters())
            # schedulers
            self.scheduler = hp.get_scheduler(self.args.trainer.scheduler, self.optim)
            self.criterion = torch.nn.CrossEntropyLoss()

            self.counter = 0
            self.loss = torch.tensor(0.)

        dev_count = torch.cuda.device_count()    
        if self.args.system.dataparallel and dev_count>1 :
            self.model = torch.nn.DataParallel(self.model,device_ids=list(range(dev_count)))

    def main(self):
        print(f'==> Mode: {self.mode}')
        if self.mode == 'train':
            self.train()
        elif self.mode == 'eval':
            self.eval()
        elif self.mode == 'sample':
            self.sample()

    def load_model(self):
        model = torch.load(self.args.model.model_path, map_location=self.device)
        self.model.load_state_dict(model)
        self.model = self.model.to(self.device)


    #### FOR TRAINING THE NETWORK
    def train(self):
        done =False 
        while not done:
            self.train_epoch()
            done = True
            #done =  self.counter >= self.args.trainer.total_iter


    def train_epoch(self):

        accum_loss = []

        for batch_idx, (data, target) in enumerate(self.train_loader):
            data = data.to(self.device).clone().detach()
            self.counter += 1
            self.loss = self.iteration(data, target)
            accum_loss.append(self.loss.item())

            if self.counter % self.args.metrics.checkpoint_freq == 0:
                #if self.args.train_mode in ['both', 'base'] and self.args.dataset_type=='images':
                    #images = self.sample_images(self.fixed_latents, self.args.sample_b_size)
                fig = make_grid_images(data)
                self.log_artifacts(fig, self.counter, art_type='figures')
                self.log_artifacts(self.model.state_dict(), self.counter, art_type='torch_models')
                acc_loss = np.array(accum_loss)
                accum_dict = {'losses':acc_loss, 'step':self.counter}
                self.log_artifacts(accum_dict, self.counter, art_type='arrays')

            if self.counter % self.args.metrics.disp_freq == 0:
                loss = np.asarray(accum_loss).mean()
                self.log_metrics({'loss':loss, 'loss_iter': self.counter})
                self.timer(self.counter, " loss: %.8f" % ( loss))
                accum_loss = []
    # take a step, and maybe train either the discriminator or generator. also used in eval
    def iteration(self, data, target):
        self.optim.zero_grad()
        # get data and run through discriminator
        pred = self.model(data)
        loss = self.criterion(pred, target) 
        loss.backward()
        self.optim.step()
        return loss

def make_grid_images(images, N_h=8,N_w=8):
    N_tot = images.shape[0]
    tot= min(N_h*N_w, N_tot)
    samples = images[:tot].cpu().numpy()
    fig = plt.figure(figsize=(N_h, N_w))
    gs = gridspec.GridSpec(N_h, N_w)
    gs.update(wspace=0.05, hspace=0.05)
    images_list = []
    for i, sample in enumerate(samples):
        ax = plt.subplot(gs[i])
        plt.axis('off')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_aspect('equal')
        sample_t = sample.transpose((1,2,0)) * 0.5 + 0.5
        images_list.append(sample_t)
        plt.imshow(sample_t)


    return fig
### Savers

    # just evaluate the performance (via KALE metric) during training
  