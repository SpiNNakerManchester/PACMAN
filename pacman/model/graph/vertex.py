from abc import ABCMeta
from abc import abstractmethod
from six import add_metaclass

from pacman.model.constraints.abstract_constraint import AbstractConstraint
from pacman.exceptions import PacmanInvalidParameterException

@add_metaclass(ABCMeta)
class Vertex(object):
    """ Represents a Vertex of a graph, which contains a number of atoms, and\
        which can be partitioned into a number of subvertices, such that the\
        total number of atoms in the subvertices adds up to the number of atoms\
        in the vertex
    """
    
    def __init__(self, n_atoms, label=None, constraints=None):
        """

        :param n_atoms: The number of atoms that the vertex can be split into
        :type n_atoms: int
        :param label: The name of the vertex
        :type label: str
        :param constraints: The constraints of the vertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
                    * If the number of atoms is less than 1
        """
        if n_atoms < 1:
            raise PacmanInvalidParameterException(
                    "n_atoms", n_atoms, 
                    "Must be at least one atom in the vertex")
        
        self._label = label
        self._n_atoms = n_atoms
        self._constraints = list()

        self.add_constraints(constraints)
        
    @classmethod
    def __subclasshook__(cls, othercls):
        """ Checks if all the abstract methods are present on the subclass
        """
        for C in cls.__mro__:
            for key in C.__dict__:
                item = C.__dict__[key]
                if hasattr(item, "__isabstractmethod__"):
                    if not any(key in B.__dict__ for B in othercls.__mro__):
                        return NotImplemented
        return True

    def add_constraint(self, constraint):
        """ Add a new constraint to the collection of constraints for the vertex

        :param constraint: constraint to add
        :type constraint:\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    constraint is not valid
        """
        if (constraint is None 
                or not isinstance(constraint, AbstractConstraint)):
            raise PacmanInvalidParameterException(
                    "constraint", constraint, "Must be a pacman.model"
                        ".constraints.abstract_contsraint.AbstractConstraint")
        self._constraints.append(constraint)

    def add_constraints(self, constraints):
        """ Add an iterable of constraints to the collection of constraints for\
            the vertex

        :param constraints: iterable of constraints to add
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of the\
                    constraints is not valid
        """
        if constraints is not None:
            for next_constraint in constraints:
                self.add_constraint(next_constraint)

    def set_constraints(self, constraints):
        """ Set the constraints of the vertex to be exactly the given iterable\
            of constraints, overwriting any previously added constraints

        :param constraints: iterable of constraints to set
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of the\
                    constraints is not valid
        """
        self._constraints = list()
        self.add_constraints(constraints)
        
    @abstractmethod
    def get_maximum_resources_used_by_atoms(self, lo_atom, hi_atom):
        """ Get the maximum resources that are used by a range of atoms
        
        :param lo_atom: The first atom in the range
        :type lo_atom: int
        :param hi_atom: The last atom in the range
        :type hi_atom: int
        :return: An iterable of the various resource types used
        :rtype: iterable of :py:class:`pacman.model.resources.abstract_resource.AbstractResource`
        """
        pass
    
    def create_subvertex(self, lo_atom, hi_atom, label=None, 
            additional_constraints=None):
        """ Creates a subvertex of this vertex.  Can be overridden in vertex\
            subclasses to create an subvertex instance that contains detailed\
            information
            
        :param lo_atom: The first atom in the subvertex
        :type lo_atom: int
        :param hi_atom: The last atom in the subvertex
        :type hi_atom: int
        :param label: The label to give the subvertex.  If not given, and the\
                    vertex has no label, no label will be given to the\
                    subvertex.  If not given and the vertex has a label, a\
                    default label will be given to the subvertex
        :type label: str
        :param additional_constraints: An iterable of constraints from the\
                    subvertex over-and-above those of the vertex
        :type additional_constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If lo_atom or hi_atom are out of range
                    * If one of the constraints is invalid
        """
        pass

    @property
    def label(self):
        """ The label of the vertex

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
    
    @property
    def n_atoms(self):
        """ The number of atoms in the vertex

        :return: The number of atoms
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._n_atoms
    
    @property
    def constraints(self):
        """ An iterable constraints for the vertex

        :return: iterable of constraints
        :rtype: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :raise None: Raises no known exceptions
        """
        return self._constraints
