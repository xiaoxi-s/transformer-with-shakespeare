import torch
import torch.nn as nn

# dq, dk, dv, dmodel = 64, 64, 64, 512

class Attention(nn.Module):
    def __init__(self, block_size, dmodel=512, dk=64, dv=64, mask=False):
        super(Attention, self).__init__()
        self.dmodel = dmodel 
        self.dk = dk
        self.dv = dv
        self.block_size = block_size
    
        self.WQ = nn.Linear(dmodel, self.dk)
        self.WK = nn.Linear(dmodel, self.dk)
        self.WV = nn.Linear(dmodel, self.dv)
        if mask:
            m = torch.triu(torch.ones((self.block_size, self.block_size)), diagonal=1)
            m.masked_fill_(m==1, float('-inf'))
            self.register_buffer('mask', m)
        else:
            m = torch.zeros((self.block_size, self.block_size))
            self.register_buffer('mask', m)
        
        self.mask.requires_grad = False

    def forward(self, XQ, XK, XV):
        # Q: (batch_size, seq_len, dq)
        # K: (batch_size, seq_len, dk)
        # V: (batch_size, seq_len, dv)
        # print(Q.shape, K.shape, V.shape)

        Q = self.WQ(XQ)
        K = self.WK(XK)
        V = self.WV(XV)
        _, seq_len, _ = Q.size()
    
        output = Q @ K.mT / (self.dk**0.5)

        output = torch.softmax((output + self.mask[:seq_len, :seq_len].to(output.device)), dim=-1)
        return output @ V


class MultiHeadAttention(nn.Module):
    def __init__(self, block_size, dmodel, num_heads, mask=False):
        super(MultiHeadAttention, self).__init__()
        self.dmodel = dmodel 
        self.num_heads = num_heads
        self.dk = dmodel // num_heads
        self.dv = self.dk
        self.block_size = block_size

        self.heads = nn.ModuleDict({
            f'head_{i}': Attention(self.block_size, self.dmodel, self.dk, self.dv, mask)
            for i in range(self.num_heads)
        })

        self.linear = nn.Linear(self.num_heads * self.dv, self.dmodel)

    def forward(self, Q, K, V):
        output = torch.cat([head(Q, K, V) for head in self.heads.values()], dim=-1)
        output = self.linear(output)
        return output 


class AttentionLayer(nn.Module):
    def __init__(self, block_size, dmodel, num_heads, mask=False, attention_dropout=0.1):
        super(AttentionLayer, self).__init__()
        self.block_size = block_size
        self.dmodel = dmodel
        self.num_heads = num_heads
        self.mask = mask

        self.attention = MultiHeadAttention(self.block_size, self.dmodel, self.num_heads, self.mask)
        self.layer_norm = nn.LayerNorm(self.dmodel)
        self.dropout_1 = nn.Dropout(attention_dropout)

    def forward(self, Q, K, V):
        # Q, K, V: (batch_size, seq_len, dmodel)
        output = self.attention(Q, K, V)
        output = self.dropout_1(output)
        output = self.layer_norm(Q + output)

        return output
    

class FeedForwardLayer(nn.Module):
    def __init__(self, dmodel, dropout=0.1):
        super(FeedForwardLayer, self).__init__()
        self.dmodel = dmodel

        self.fully_connected = nn.Sequential(
            nn.Linear(self.dmodel, 2048),
            nn.ReLU(),
            nn.Linear(2048, self.dmodel)
        )
        self.layer_norm = nn.LayerNorm(self.dmodel)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        # x: (batch_size, seq_len, dmodel)
        output = self.fully_connected(x)
        output = self.dropout(output)
        output = self.layer_norm(output + x)
        return output
