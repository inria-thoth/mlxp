Introduction
------------

  
In this tutorial, we will go through the three main functionalities: Launching, Logging, and Reading and explain these are easily handled by MLXP. 
Then we will see how to enhance reproducibility of experiments using the git-based version manager provided by MLXP and how to submit several jobs to a cluster in a single command using the MLXP's scheduler. 

To make things concrete, we will consider a simple use-case where we are interested in training a neural network on a regression task. You can find code for reproducing this tutorial by following this link https://github.com/MichaelArbel/mlxp/tree/master/tutorial.

The working example 
^^^^^^^^^^^^^^^^^^^
We will now give a quick overview of our working example, where we present the directory structure of the code and its main content. 

The first step is to create a directory 'tutorial' containing the code needed for this project. The directory is structured as follow:

.. code-block:: text
   :caption: tutorial/

   tutorial/
   ├── configs/
   │   └── config.yaml
   ├── core.py
   ├── main.py
   └── results.py

The directory contains three files: 'core.py', 'main.py' and 'results.py'. It also contains a directory 'configs' that will be used later by MLXP. For now, we will only have a look at the 'core.py' and 'main.py' files.


The 'core.py' file
""""""""""""""""""

The file 'core.py' contains a PyTorch implementation of a one hidden layer network 'OneHiddenLayer' as well as a simple data loader 'DataLoader' that we will use during training. In the rest of the tutorial, we will not need to worry about the content of 'core.py', but let's just have a quick look at this file:


.. code-block:: python
    :caption: main.py

    import torch
    import torch.nn as nn

    def train_epoch(dataloader,
                    model,
                    optimizer):
        for data in dataloader:
            x,y = data
            pred = model(x)
            train_err = torch.mean((pred-y)**2)
            train_err.backward()
            optimizer.step()
        return train_err

    class Dataset(torch.utils.data.Dataset):

        def __init__(self, d_int, device):
            self.network = OneHiddenLayer(d_int, 5)
            self.device = device
            dtype = torch.float
            self.X = torch.normal(mean= torch.zeros(N_samples,d_int,dtype=dtype,device=device),std=1.)
            self.total_size = N_samples
            with torch.no_grad():
                self.Y = self.network(self.X)

        def __len__(self):
            return self.total_size 
        def __getitem__(self,index):
            return self.X[index,:],self.Y[index,:]

    def DataLoader(d_int, device):
        dataset = Dataset(d_int, device)
        return [(dataset.X, dataset.Y)]



    class OneHiddenLayer(nn.Module):
        def __init__(self,d_int, n_units):
            super(OneHiddenLayer,self).__init__()
            self.linear1 = torch.nn.Linear(d_int, n_units,bias=True)
            self.linear2 = torch.nn.Linear( 1, n_units, bias=False)
            self.non_linearity = torch.nn.SiLU()
            self.d_int = d_int
            self.n_units = n_units

        def forward(self, x):
            x = self. non_linearity(self.linear1(x))
            return torch.einsum('hi,nh->ni',self.linear2.weight,x)/self.n_units


.. _old_main_file:

The 'main.py' file
""""""""""""""""""

The file 'main.py' contains code for training the model 'OneHiddenLayer' on data provided by the 'DataLoader'. Training is performed using the function 'train': 

.. code-block:: python
    :caption: main.py

    import torch
    from core import DataLoader, OneHiddenLayer

    def train(d_int = 10,
              num_units = 100,
              num_epoch = 10,
              lr = 10.,
              device = 'cpu'):

        # Building model, optimizer and data loader.
        model = OneHiddenLayer(d_int=d_int, n_units = num_units)
        model = model.to(device)
        optimizer = torch.optim.SGD(model.parameters(),lr=lr)
        dataloader = DataLoader(d_int,device)         

        # Training
        for epoch in range(num_epoch):

            train_err = train_epoch(dataloader,
                                    model,
                                    optimizer)

            print({'loss': train_err.item(),
                  'epoch': epoch})

        print(f"Completed training with learing rate: {lr}")

    if __name__ == "__main__":
        train()


Training the model
""""""""""""""""""

If we execute the function 'main.py', we can see that the training performs 10 'epochs' and then prints a message confirming that the training is complete. 

.. code-block:: console

    $ python main.py
    {'loss': 0.030253788456320763, 'epoch': 0}
    {'loss': 0.02899891696870327, 'epoch': 1}
    {'loss': 0.026649776846170425, 'epoch': 2}
    {'loss': 0.023483652621507645, 'epoch': 3}
    {'loss': 0.019827445968985558, 'epoch': 4}
    {'loss': 0.01599641889333725, 'epoch': 5}
    {'loss': 0.012259905226528645, 'epoch': 6}
    {'loss': 0.008839688263833523, 'epoch': 7}
    {'loss': 0.005932427477091551, 'epoch': 8}
    {'loss': 0.003738593542948365, 'epoch': 9}
    Completed training with learing rate: 10.0


In this basic example, we have not used any specific tool for launching or logging. 
Next, we will see how you can use MLXP to keep track of all options, results, and code versions seamlessly! 

