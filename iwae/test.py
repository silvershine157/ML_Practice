from dataset import *
from model import *
from const import *
from main import *

def test1():
	data = preprocess_data()
	print(data["train_images"].dtype)
	print(data["train_images"].shape)
	print(data["train_labels"].dtype)
	print(data["train_labels"].shape)
	pass

def test2():
	data = preprocess_data()
	train_loader, val_loader, test_loader = get_dataloader(data, 4)
	net = Net()
	for b_i, batch in enumerate(train_loader):
		net(batch["image"])
		break

def test3():
	H = 28
	W = 28
	Dz = 10
	vae = VAE(H, W, Dz)
	vae.to(device)
	B = 4
	x2d = torch.zeros((B, H, W), device=device)
	loss = vae.loss(x2d)
	print(loss)

def test4():
	Dz = 3
	N = 5
	net = VAE(28, 28, Dz).to(device)
	z_grid = make_z_grid(Dz, N)
	show_img_grid(net, z_grid)

test4()
