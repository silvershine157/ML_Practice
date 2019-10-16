import numpy as np
import matplotlib.pyplot as plt
import matplotlib

## model dimensions
K = 3 # number of latent states
N = 100 # number of data points
D = 2 # dimension of a data point

def generate_data():
	## true model parameters
	# p(z_0): initial distribution
	PI = np.array([0.2, 0.5, 0.3])
	# p(z_n | z_{n-1}): transition matrix
	A = np.array([
		[0.85, 0.05, 0.1],
		[0.2, 0.7, 0.1],
		[0.1, 0.05, 0.85]
	])
	# p(x_n | z_n): D-dim gaussian
	PHI_MU = np.array([
		[0.3, 0.7],
		[0.3, 0.2],
		[0.7, 0.5]
	])
	PHI_SIGMA = 0.01*np.array([
		[[0.5, 0.4], [0.4, 0.5]],
		[[0.5, 0.0], [0.0, 0.2]],
		[[0.5, -0.4], [-0.4, 0.5]]
	])
	## generate data
	z = np.zeros((N), dtype=np.int16)
	x = np.zeros((N, D), dtype=np.float32)
	z[0] = np.random.choice(K, p=PI)
	x[0] = np.random.multivariate_normal(PHI_MU[z[0]], PHI_SIGMA[z[0]])
	for n in range(1, N):
		z[n] = np.random.choice(K, p=A[z[n-1], :])
		x[n] = np.random.multivariate_normal(PHI_MU[z[n]], PHI_SIGMA[z[n]])
	return x, z

def visualize_data(x, z=None):
	if z is not None:
		# color code latent variable
		colors = ['red', 'green', 'blue']
		plt.plot(x[:, 0], x[:, 1], color='black', zorder=1)
		plt.scatter(x[:, 0], x[:, 1], 
			c=z, cmap=matplotlib.colors.ListedColormap(colors), zorder=2)
		plt.show()
	else:
		# no color
		plt.plot(x[:, 0], x[:, 1])
		plt.scatter(x[:, 0], x[:, 1])
		plt.show()

def main():
	x, z = generate_data()
	old_params = init_params(x)
	new_params, p_x = em_step(old_params, x)
	#visualize_data(x, z=None)

def init_params(x):
	# TODO: use K-means to intiialize emission parameters
	pi = np.ones((K))/K
	A = np.ones((K, K))/K
	MU = np.random.random((K, D))
	#SIGMA = [np.expand_dims(np.eye(D), axis=0) for _ in range(K)]
	SIGMA = [0.1*np.eye(D) for _ in range(K)]
	SIGMA = np.stack(SIGMA, axis=0)
	params = (pi, A, MU, SIGMA)
	return params

def em_step(old_params, x):
	# E
	gamma, xi, p_x = forward_backward(old_params, x)
	# M
	new_params = None
	return new_params, p_x

def forward_backward(params, x):
	'''
	<input>
	params = (pi, A, MU, SIGMA)
		pi: (K)
		A: (K, K)
		MU: (K, D)
		SIGMA: (K, D, D)
	x: (N, D)
	<output>
	gamma: (N, K)
	xi: (N, K, K)
	'''
	alpha_ = np.zeros((N, K))
	beta_ = np.zeros((N, K))
	gamma = None
	xi = None
	p_x = None
	return gamma, xi, p_x

main()