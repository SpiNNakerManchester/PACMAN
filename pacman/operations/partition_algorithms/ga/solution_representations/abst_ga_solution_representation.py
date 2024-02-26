class AbstractGASolutionRepresentation:
    def convert_from_common_representation(self, solution):
        raise NotImplementedError
    
    def get_npy_data(self):
        raise NotImplementedError
    
    def __str__(self):
        return "abst_rep"