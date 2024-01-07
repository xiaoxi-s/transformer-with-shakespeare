import torch

from torch.utils.data import Dataset 
from .utils import load_pickled_data, read_corpus, tokenize_play, generate_dataset_from_tokens, pickle_data

from os import listdir
from os.path import isfile, join

class BabyShakespeareDataset(Dataset):
    def __init__(self, vocab_to_ind, block_size=8, shakespeare_path='./shakespeare/shakespeare-db/', dataset_size=None, device='cpu'):
        self.vocab_to_ind = vocab_to_ind 
        # self.ind_to_vocab = load_pickled_data('ind_to_vocab.pkl')

        self.plays = [join(shakespeare_path, f) for f in listdir(shakespeare_path) if isfile(join(shakespeare_path, f))]
        self.block_size = block_size

        self.data = [] 

        if not isfile('./data/data.pkl'):
            for p in self.plays:
                print("Play: ", p)
                print("  Reading...")
                play_in_string = read_corpus(p)
                print("  Tokenizing...")
                play_tokens = tokenize_play(play_in_string, self.vocab_to_ind)
                print("  Generating dataset from tokens...")
                dataset_from_one_play = generate_dataset_from_tokens(play_tokens, self.vocab_to_ind, self.block_size)
                print("  Dataset length: ", len(dataset_from_one_play))
                self.data = self.data + dataset_from_one_play
            
            pickle_data(self.data, 'data.pkl')
        else:
            self.data = load_pickled_data('data.pkl')

        if dataset_size is not None:
            # for test purpose
            self.data = self.data[:dataset_size]
        
        for i in range(len(self.data)):
            self.data[i] = (torch.tensor(self.data[i][0]).to(device), torch.tensor(self.data[i][1]).to(device))

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()
        return self.data[idx]