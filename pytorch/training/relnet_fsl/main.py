import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from skimage import io
import os
import random
import numpy as np

'''
Meta train set
- Sample set
- Query set
Meta test set
- Support set
- Test set
'''

EPISODES = 1000
LEARNING_RATE = 0.001

'''
network architecture is identical to the author's code:
https://github.com/floodsung/LearningToCompare_FSL/blob/master/omniglot/omniglot_train_one_shot.py
'''
class EmbeddingModule(nn.Module):
	def __init__(self):
		super(EmbeddingModule, self).__init__()

		# define architecture
		self.layer1 = nn.Sequential(
			nn.Conv2d(1, 64, kernel_size=3, padding=0),
			nn.BatchNorm2d(64, momentum=1, affine=True),
			nn.ReLU(),
			nn.MaxPool2d(2)
		)
		self.layer2 = nn.Sequential(
			nn.Conv2d(64, 64, kernel_size=3, padding=0),
			nn.BatchNorm2d(64, momentum=1, affine=True),
			nn.ReLU(),
			nn.MaxPool2d(2)
		)
		self.layer3 = nn.Sequential(
			nn.Conv2d(64, 64, kernel_size=3, padding=0),
			nn.BatchNorm2d(64, momentum=1, affine=True),
			nn.ReLU()
		)
		self.layer4 = nn.Sequential(
			nn.Conv2d(64, 64, kernel_size=3, padding=0),
			nn.BatchNorm2d(64, momentum=1, affine=True),
			nn.ReLU(),
		)

	def forward(self, img):
		# img: B x 1 x 28 x 28
		# out: B x C x D x D
		out = self.layer1(img)
		out = self.layer2(out)
		out = self.layer3(out)
		out = self.layer4(out)
		
		return out

class RelationModule(nn.Module):
	def __init__(self):
		super(RelationModule, self).__init__()
		
		input_size = 64
		hidden_size = 8

		# define architecture
		self.layer1 = nn.Sequential(
			nn.Conv2d(128, 64, kernel_size=3, padding=1),
			nn.BatchNorm2d(64, momentum=1, affine=True),
			nn.ReLU(),
			nn.MaxPool2d(2)
		)
		self.layer2 = nn.Sequential(
			nn.Conv2d(64, 64, kernel_size=3, padding=1),
			nn.BatchNorm2d(64, momentum=1, affine=True),
			nn.ReLU(),
			nn.MaxPool2d(2)
		)
		self.out_layer = nn.Sequential(
			nn.Linear(input_size, hidden_size),
			nn.ReLU(),
			nn.Linear(hidden_size, 1),
			nn.Sigmoid()
		)

	def forward(self, combined):
		# combined: B x 2C x D x D
		# out: B

		out = self.layer1(combined)
		out = self.layer2(out)
		out = out.view(out.size(0), -1)
		out = self.out_layer(out)
		return out

def get_class_dirs():

	# read all 1623 character class dir in omniglot
	data_dir = './data/omniglot_resized/'
	all_classes = []
	for family in os.listdir(data_dir):
		family_dir = os.path.join(data_dir, family)
		if not os.path.isdir(family_dir):
			continue
		for class_name in os.listdir(family_dir):
			class_dir = os.path.join(family_dir, class_name)
			if not os.path.isdir(class_dir):
				continue
			all_classes.append(class_dir)

	# split dataset
	num_train = 1200
	random.seed(1)
	random.shuffle(all_classes)
	meta_train_dirs = all_classes[:num_train] # 1200
	meta_val_dirs = all_classes[num_train:] # 423
	meta_test_dirs = meta_val_dirs # seems like the author's code is doing this

	return meta_train_dirs, meta_val_dirs, meta_test_dirs


class OmniglotOneshotDataset(Dataset):
	def __init__(self, dir_list):
		self.dir_list = dir_list

	def __len__(self):
		return len(self.dir_list)

	def __getitem__(self, idx):
		img_dir = self.dir_list[idx]
		imgs = []
		for img_name in os.listdir(img_dir):
			img = io.imread(os.path.join(img_dir, img_name))
			img = torch.from_numpy(img)
			img = img.unsqueeze(dim=0)
			img = img.type(torch.FloatTensor)
			img = img/255
			imgs.append(img)
		random.shuffle(imgs)
		sample = imgs.pop()
		query = torch.cat(imgs, dim=0)
		return {"sample":sample, "query":query}


def combine_pairs(sample_features, query_features):

	_, C, D, _ = sample_features.size()
	
	# generate labels
	sample_classes = torch.arange(5) # 5
	query_classes = sample_classes.unsqueeze(dim=1).expand(-1, 19) # 5 x 19

	# expand dimensions
	sample_classes = sample_classes.unsqueeze(dim=1).expand(-1, 95) # 5 x 95	
	query_classes = query_classes.contiguous().view(1, -1).expand(5, -1) # 5 x 95
	
	# generate target
	target = (sample_classes == query_classes).type(torch.FloatTensor)
	target = target.view(-1) # 475

	# expand for pairing
	sample_features = sample_features.unsqueeze(dim=1).expand(-1, 95, -1, -1, -1) # 5 x 95 x C x D x D
	query_features = query_features.unsqueeze(dim=0).expand(5, -1, -1, -1, -1) # 5 x 95 x C x D x D
	
	# concat in depth
	combined = torch.cat([sample_features, query_features], dim=2) # 5 x 95 x 2C x D x D
	combined = combined.view(-1, 2*C, D, D) # 475 x 2C x D x D
	
	return combined, target


def test():

	# setup data
	meta_train_dirs, meta_val_dirs, meta_test_dirs = get_class_dirs()
	dataset = OmniglotOneshotDataset(meta_train_dirs)
	dataloader = DataLoader(dataset, batch_size=5, shuffle=True)

	# construct model
	embed_net = EmbeddingModule()
	rel_net = RelationModule()
	criterion = nn.MSELoss()
	embed_opt = torch.optim.Adam(embed_net.parameters(), lr=LEARNING_RATE)
	rel_opt = torch.optim.Adam(rel_net.parameters(), lr=LEARNING_RATE)

	# training
	for episode in range(EPISODES):

		# form episode
		ep_data = next(iter(dataloader))
		sample = ep_data['sample'] # 5 x 1 x 28 x 28
		query = ep_data['query'] # 5 x 19 x 28 x 28
		query = query.view(-1, 1, 28, 28) # flattening, 95 x 1 x 28 x 28

		# forward pass
		sample_features = embed_net(sample) # 5 x C x D x D (avoid redundant computation)
		query_features = embed_net(query) # 95 x C x D x D 
		combined, score_target = combine_pairs(sample_features, query_features)
		score_pred = rel_net(combined)
		loss = criterion(score_pred, score_target)

		# backward pass & update
		embed_net.zero_grad()
		rel_net.zero_grad()
		loss.backward()
		embed_opt.step()

		print(loss.item())


test()
