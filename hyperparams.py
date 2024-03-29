import torch

block_size = 128
batch_size = 256 
dmodel = 256 
learning_rate = 0.00001
cuda_available = torch.cuda.is_available()
dropout = 0.4
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")