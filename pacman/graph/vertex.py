__author__ = 'stokesa6,daviess'


class Vertex(object):
    """ Creates a new vertex object """
    
    def __init__(self, label, n_atoms, constraints=None):
        """

        :param label: The name of the vertex
        :type label: str 
        :param n_atoms: The number of atoms that the vertex can be split into
        :type n_atoms: int
        :param constraints: The constraints for partitioning and placement
        :type constraints: list of Constraint objects
        :return: a Vertex object
        :rtype: pacman.graph.vertex.Vertex
        :raise None: Raises no known exceptions
        """
        pass
    
    @property
    def label(self):
        """
        Returns the label of the vertex

        :return: The name of the vertex
        :rtype: str
        :raise None: Raises no known exceptions
        """
        pass
    
    @property
    def n_atoms(self):
        """
        Returns the number of atoms in the vertex

        :return: The number of atoms in the vertex
        :rtype: int
        :raise None: Raises no known exceptions
        """
        pass
    
    @property
    def constraints(self):
        """ 
        
        """
        pass
