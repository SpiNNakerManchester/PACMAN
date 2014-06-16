__author__ = 'stokesa6,daviess'

class Vertex(object):
    """ a vertex object """

    
    def __init__(self, label, n_atoms, constraints=None):
        """ Create a new vertex
        :param label: The name of the vertex
        :type label: str 
        :param n_atoms: The number of atoms that the vertex can be split into
        :type n_atoms: int
        :param constraints: The constraints for partitioning and placement
        :type constraints: list of Constraint objects
        :return: a Vertex object
        :rtype: pacman.graph.vertex.Vertex
        :raises None: Raises no known exceptions
        """
        pass
    
    @property
    def label(self):
        """ Get the label of the vertex
        :return: The name of the vertex
        :rtype: str
        :raises None: Raises no known exceptions
        """
        pass
    
    @property
    def n_atoms(self):
        """ Get the number of atoms in the vertex
        :return: The number of atoms in the vertex
        :rtype: int
        :raises None: Raises no known exceptions
        """
        pass
    
    @property
    def constraints(self):
        """ 
        
        """
        pass