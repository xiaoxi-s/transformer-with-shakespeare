import pickle
import torch
import os

import numpy as np

from os import listdir
from os.path import isfile, join

from .dataloader import BabyShakespeareDataset

def read_corpus(file_path):
    """Read file, return a list of list of words."""
    play_in_string = ''
    with open(file_path, 'r', encoding='utf-8') as infile:
        play_in_string = infile.read()
    
    # for i in range(10):
    #     for j in range(30):
    #         print(my_str[i*30+j], end='')
    #     input()
    play_in_string = play_in_string.strip()

    return play_in_string


def get_char_type(c):
    """Get the type of the character."""
    if c.isalpha():
        return 'alpha'
    elif c.isdigit():
        return 'digit'
    elif c == ' ':
        return 'space'
    elif c == '\n':
        return 'newline'
    elif c.isspace():
        return 'otherspaces'
    else:
        return 'other'


def tokenize_play_with_char(play_string, vocab_to_ind):
    """Tokenize the play string."""
    tokens = []
    for c in play_string:
        tokens.append(vocab_to_ind[c])

    return tokens

def tokenize_play_with_word(play_string, vocab_to_ind):
    """Tokenize the play string."""

    play_length = len(play_string)
    i = 0
    tokens = [vocab_to_ind['<start>']]
    while i < play_length:
        token = ''
        c_type = get_char_type(play_string[i])
        j = i
        while j < play_length and get_char_type(play_string[j]) == c_type:
            j += 1
        token = play_string[i:j]
        tokens.append(vocab_to_ind[token])
        i = j
    tokens.append(vocab_to_ind['<stop>'])

    return tokens


def generate_dataset_from_tokens(play_tokens, block_size):
    """Generate a sequence of tokens from the play token."""
    data = []
    for i in range(len(play_tokens) - block_size - 1): 
        # training_data = (play_tokens[i:i + block_size], play_tokens[i + 1: i + block_size + 1])
        data.append((play_tokens[i:i + block_size], play_tokens[i + 1: i + block_size + 1]))
        # data.append(training_data)
        
        # if i % 10000 == 0:
        #     print(f"Generated data at location: {i}, total number of tokens: {len(play_tokens)}")

    return data 


def load_pickled_data(file_name, picked_data_path='./data/'):
    with open(join(picked_data_path, file_name), 'rb') as infile:
        vocab_to_ind = pickle.load(infile)
    
    return vocab_to_ind


def pickle_data(data, file_name, picked_data_path='./data/'):
    """Pickle the data."""
    with open(join(picked_data_path, file_name), 'wb') as outfile:
        pickle.dump(data, outfile)


def load_all_data(vocab_to_ind, tokenizer, factor, dataset_name, plays, block_size=8, data_path='./data/'):
    data_file_name = f"{tokenizer}_data_{dataset_name}.pt"
    if tokenizer == 'char':
        tokenizer_func = tokenize_play_with_char
    elif tokenizer == 'word':
        tokenizer_func = tokenize_play_with_word
    data_path = os.path.join(data_path, data_file_name)
    block_size = block_size
    data = []
    if not isfile(data_path):
        data = []
        for p in plays:
            print("Play: ", p)
            print("  Reading...")
            play_in_string = read_corpus(p)
            print("  Tokenizing...")
            play_tokens = tokenizer_func(play_in_string, vocab_to_ind)
            print("  Generating dataset from tokens...")
            # dataset_from_one_play = generate_dataset_from_tokens(play_tokens, vocab_to_ind, block_size)
            # print("  Dataset length: ", len(dataset_from_one_play))
            data += play_tokens
        data = torch.tensor(data, dtype=torch.long)
        torch.save(data, data_path)

    # data = np.load(data_path, allow_pickle=True)['arr_0']    
    data = torch.load(data_path)
    print("corpus token size: ", data.size())
    end_of_selected_data = int(len(data) * factor)
    print("Selected corpus token size: ", end_of_selected_data)
    return data[0: end_of_selected_data]


def get_train_and_test_dataset(vocab_to_ind, dataset_name, plays, tokenizer, factor, device='cpu', block_size=8):
    """Get the training and testing dataset."""
    print("Loading data...")
    data = load_all_data(vocab_to_ind, tokenizer, factor, dataset_name, plays, block_size)
    data = data.to(device)
    # train, test, finetune, validation ratio: 0.7, 0.1, 0.1, 0.1
    train_ind = int(len(data) * 0.7)
    test_ind = int(len(data) * 0.8)
    finetune_ind = int(len(data) * 0.9)
    train_data = data[:train_ind]
    test_data = data[train_ind:test_ind]
    finetune_data = data[test_ind:finetune_ind]
    validation_data = data[finetune_ind:]

    del data

    train_dataset = BabyShakespeareDataset(generate_dataset_from_tokens(train_data, block_size), device)
    test_dataset = BabyShakespeareDataset(generate_dataset_from_tokens(test_data, block_size), device)
    finetune_dataset = BabyShakespeareDataset(generate_dataset_from_tokens(finetune_data, block_size), device)
    validation_dataset = BabyShakespeareDataset(generate_dataset_from_tokens(validation_data, block_size), device)
    return train_dataset, test_dataset, finetune_dataset, validation_dataset

def generate_contents(model, vocab_to_ind, ind_to_vocab, device='cpu', max_num_of_tokens=1000):
    """Generate contents from the model."""

    output = None
    token_indx = [0] 
    with torch.no_grad():
        for i in range(max_num_of_tokens):
            input = torch.tensor(token_indx).unsqueeze(0).to(device)
            output = model(input, input)
            output = output[:, -1, :]
            output = torch.softmax(output, dim=-1) #[1, vocab_size]
            output = torch.multinomial(output, num_samples=1)
            token_indx.append(output.item())
            print(ind_to_vocab[output.item()], end='')
