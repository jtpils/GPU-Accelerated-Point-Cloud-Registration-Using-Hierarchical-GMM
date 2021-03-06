import six
import numpy as np
import transformations as trans
import abc
import transforms as tf
import so

import time


@six.add_metaclass(abc.ABCMeta)
class CostFunction():
	def __init__(self, tf_type):
		self._tf_type = tf_type

	@abc.abstractmethod
	def to_transformation(self, theta):
		return None

	@abc.abstractmethod
	def initial(self):
		return None

	@abc.abstractmethod
	def __call__(self, theta, *args):
		return None, None


def compute_l2_dist(mu_source, phi_source,
					mu_target, phi_target, sigma):
	#print(sigma)
	#print(mu_source.shape, mu_target.shape)
	z = np.power(2.0 * np.pi * sigma**2, mu_source.shape[1] * 0.5)
	#print("Z", z)
	gtrans = tf.GaussTransform(mu_target, np.sqrt(2.0) * sigma)
	phi_j_e = gtrans.compute(mu_source, phi_target / z)
	#print(phi_j_e)
	phi_mu_j_e = gtrans.compute(mu_source, phi_target * mu_target.T / z).T
	g = (phi_source * phi_j_e * mu_source.T - phi_source * phi_mu_j_e.T).T / (2.0 * sigma**2)
	return -np.dot(phi_source, phi_j_e), g


class RigidCostFunction(CostFunction):
	def __init__(self):
		self._tf_type = tf.RigidTransformation

	def to_transformation(self, theta):
		rot = trans.quaternion_matrix(theta[:4])[:3, :3]
		return self._tf_type(rot, theta[4:7])

	def initial(self):
		x0 = np.zeros(7)
		x0[0] = 1.0
		return x0

	def __call__(self, theta, *args):
		mu_source, phi_source, mu_target, phi_target, sigma = args
		tf_obj = self.to_transformation(theta)
		t_mu_source = tf_obj.transform(mu_source)
		t1 = time.time()
		f, g = compute_l2_dist(t_mu_source, phi_source,
							   mu_target, phi_target, sigma)
		t2 = time.time()
		#print(t2-t1)
		d_rot = so.diff_rot_from_quaternion(theta[:4])
		gtm0 = np.dot(g.T, mu_source)
		grad = np.concatenate([(gtm0 * d_rot).sum(axis=(1, 2)), g.sum(axis=0)])
		#print("inside", theta, f)
		return f, grad