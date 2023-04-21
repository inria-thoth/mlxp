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


def DataLoader(d_int, device):
	dataset = Dataset(d_int, device)
	return [(dataset.X, dataset.Y)]

class Dataset(torch.utils.data.Dataset):

	def __init__(self, d_int, device, normalize=False):
		self.network = OneHiddenLayer(d_int, 5)
		self.device = device
		N_samples = 1000
		dtype = torch.float
		self.X = torch.normal(mean= torch.zeros(N_samples,d_int,dtype=dtype,device=device),std=1.)

		if normalize:			
			inv_norm = 1./tr.norm(self.X,dim=1)
			self.X = tr.einsum('nd,n->nd',self.X,inv_norm)

		self.total_size = N_samples
		

		with torch.no_grad():
			self.Y = self.network(self.X)

	def __len__(self):
		return self.total_size 
	def __getitem__(self,index):
		return self.X[index,:],self.Y[index,:]






class OneHiddenLayer(nn.Module):
	def __init__(self,d_int, n_units, non_linearity = torch.nn.SiLU() ,bias=True):
		super(OneHiddenLayer,self).__init__()
		self.linear1 = torch.nn.Linear(d_int, n_units,bias=bias)
		self.linear2 = torch.nn.Linear( 1,n_units, bias=False)
		self.non_linearity = non_linearity
		self.d_int = d_int
		self.n_units = n_units

	def forward(self, x):
		x = self. non_linearity(self.linear1(x))
		return torch.einsum('hi,nh->ni',self.linear2.weight,x)/self.n_units

