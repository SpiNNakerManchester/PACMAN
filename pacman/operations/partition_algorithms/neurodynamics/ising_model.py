import numpy as np
import os
class IsingModel2D:
    def __init__(self, neuron_count, J, H):
        self._J = J
        self._H = H
        self._neuron_count = neuron_count
        self.configuration = np.zeros((neuron_count))
    
    def set_J(self, J):
        self._J = J
    def set_H(self, H):
        self._H = H
    def get_J(self):
        return self._J
    def get_H(self):
        return self._H
    def set_J_element(self, i, j, value):
        self._J[i, j] = value
    def set_H_element(self, i, value):
        self._H[i] = value
    def get_neuron_count(self):
        return self._neuron_count

    
def load_neurodynamics_record(profiling_record_name, base_path="./"):
    print("load ising model parameter H from %s_H.npy" % profiling_record_name)
    recorded_H = np.load(os.path.join(base_path, "%s_H.npy" % profiling_record_name))
    print("load ising model parameter J from %s_J.npy" % profiling_record_name)
    recorded_J = np.load(os.path.join(base_path, "%s_J.npy" % profiling_record_name))
    print("load equilibration configuration from %s_eq.npy" % profiling_record_name)
    recorded_configuration = np.load(os.path.join(base_path, "%s_eq.npy" % profiling_record_name))
    print("load samples from %s.npy" % profiling_record_name)
    recorded_samples = np.load(os.path.join(base_path, "%s.npy" % profiling_record_name))

    neuron_count = len(recorded_H)
    ising_model = IsingModel2D(neuron_count, recorded_J, recorded_H)
    ising_model.configuration = recorded_configuration
    return ising_model, recorded_samples