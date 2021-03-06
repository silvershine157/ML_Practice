import torch
import torch.nn as nn

# Glow with additive coupling layer & no LU decomposition

class coupling_NN(nn.Module):
	def __init__(self, C_half):
		super(coupling_NN, self).__init__()
		self.layers = nn.Sequential(
			nn.Conv2d(C_half, 512, 3, padding=1),
			nn.ReLU(),
			nn.Conv2d(512, 512, 1),
			nn.ReLU(),
			nn.Conv2d(512, C_half, 3, padding=1)
		)
	def forward(self, nn_in):
		'''
		nn_in: [B, C_half, S, S]
		---
		nn_out: [B, C_half, S, S]
		'''
		nn_out = self.layers(nn_in)
		return nn_out

def additive_coupling(h_in):
	'''
	h_in: [B, C, S, S]
	---
	h_out: [B, C, S, S]
	'''
	_, C, S, _ = h_in.shape
	assert C%2 == 0
	net = coupling_NN(C//2)
	first_half = h_in[:, :C//2, :, :]
	nn_out = net(first_half)
	h_out = h_in.clone()
	h_out[:, C//2:, :, :] += nn_out
	return h_out

def invertible_1x1_conv(h_in):
	'''
	h_in: [B, C, S, S]
	---
	h_out: [B, C, S, S]
	'''
	_, C, _, _ = h_in.shape
	W = torch.randn(C, C) # param
	h_out = torch.einsum('ji,bihw->bjhw', W, h_in)
	return h_out

def actnorm(h_in):
	'''
	h_in: [B, C, S, S]
	---
	h_out: [B, C, S, S]
	'''
	_, C, _, _ = h_in.shape
	scale = torch.randn(1, C, 1, 1) # param
	bias = torch.randn(1, C, 1, 1) # param
	h_out = scale * h_in + bias # broadcasting
	return h_out

def step_of_flow(h_in):
	'''
	h_in: [B, C, S, S]
	---
	h_out: [B, C, S, S]
	'''
	h1 = actnorm(h_in)
	h2 = invertible_1x1_conv(h1)
	h_out = additive_coupling(h2)
	return h_out

def squeeze(h_in):
	'''
	h_in: [B, C, S, S]
	---
	h_out: [B, 4*C, S//2, S//2]
	'''
	B, C, S, _ = h_in.shape
	assert S%2 == 0
	temp = h_in.view(B, C, S//2, 2, S//2, 2)
	temp = temp.transpose(2, 3) # [B, C, 2, S//2, S//2, 2]
	temp = temp.transpose(4, 5) # [B, C, 2, S//2, 2, S//2]
	temp = temp.transpose(3, 4) # [B, C, 2, 2, S//2, S//2]
	h_out = temp.contiguous().view(B, 4*C, S//2, S//2)
	return h_out

def multiscale(x, K, L):
	'''
	x: [B, C, S, S]
	---
	z: [B, C * S * S]
	'''
	B, C, _, _ = x.shape
	h = squeeze(x) # [B, 4*C, S//2, S//2]
	for k in range(K):
		h = step_of_flow(h) # still [B, 4*C, S//2, S//2]
	if L == 1:
		z = h.contiguous().view(B, -1) # [B, C * S * S]
		return z
	else:
		# split
		x_prop = h[:, 2*C:, :, :] # [B, 2*C, S//2, S//2]
		z_current = h[:, :2*C, :, :].contiguous().view(B, -1) # [B, C * S * S//2]
		# recursively obtain result of smaller scale
		z_rest = multiscale(x_prop, K, L-1) # [B, C * S * S//2]
		z = torch.cat([z_current, z_rest], dim=1) # [B, C * S * S]
		return z

def test1():
	x = torch.randn((7, 3, 32, 32))
	K = 32
	L = 3
	z = multiscale(x, K, L)
	print(z.shape)

test1()