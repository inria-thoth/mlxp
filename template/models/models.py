import torch

class LinearNNModel(torch.nn.Module):
    def __init__(self, input_dim, out_dim):
        super(LinearNNModel, self).__init__()
        self.linear = torch.nn.Linear(input_dim, out_dim)  # One in and one out

    def forward(self, x):
        x= x.reshape(x.shape[0],-1)
        y_pred = self.linear(x)
        return y_pred