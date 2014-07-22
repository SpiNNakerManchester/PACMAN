from pacman.model.constraints.abstract_constraint import AbstractConstraint
from pacman.exceptions import PacmanInvalidParameterException


class Subvertex(object):
    """ Represents a sub-set of atoms from a Vertex
    """
    def __init__(self, lo_atom, hi_atom, label=None, constraints=None):
        """

        :param lo_atom: The id of the first atom in the subvertex with\
                        reference to the atoms in the vertex
        :type lo_atom: int
        :param hi_atom: The id of the last atom in the subvertex with\
                        reference to the atoms in the vertex
        :type hi_atom: int
        :param label: The name of the subvertex, or None if no name
        :type label: str
        :param constraints: The constraints of the subvertex
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise pacman.exceptions.PacmanInvalidParameterException:
                    * If one of the constraints is not valid
                    * If lo_atom is less than 0
                    * If hi_atom is less than lo_atom
        """
        if lo_atom < 0:
            raise PacmanInvalidParameterException(
                "lo_atom", str(lo_atom), "Cannot be less than 0")
        if hi_atom < lo_atom:
            raise PacmanInvalidParameterException(
                "hi_atom", str(hi_atom), "Cannot be less than lo_atom")
        
        self._label = label
        self._lo_atom = lo_atom
        self._hi_atom = hi_atom
        self._constraints = list()

        self.add_constraints(constraints)

    def add_constraint(self, constraint):
        """ Add a new constraint to the collection of constraints for the\
            subvertex

        :param constraint: constraint to add
        :type constraint:\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If the\
                    constraint is not valid
        """
        if (constraint is None 
                or not isinstance(constraint, AbstractConstraint)):
            raise PacmanInvalidParameterException(
                "constraint",
                constraint,
                "Must be a pacman.model"
                ".constraints.abstract_constraint.AbstractConstraint")
        self._constraints.append(constraint)

    def add_constraints(self, constraints):
        """ Add an iterable of constraints to the collection of constraints for\
            the subvertex

        :param constraints: iterable of constraints to add
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of the\
                    constraints is not valid
        """
        if constraints is not None:
            for next_constraint in constraints:
                self.add_constraint(next_constraint)

    def set_constraints(self, constraints):
        """ Set the constraints of the subvertex to be exactly the given\
            iterable of constraints, overwriting any previously added\
            constraints

        :param constraints: iterable of constraints to set
        :type constraints: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :return: None
        :rtype: None
        :raise pacman.exceptions.PacmanInvalidParameterException: If one of the\
                    constraints is not valid
        """
        self._constraints = list()
        self.add_constraints(constraints)

    @property
    def label(self):
        """ The label of the subvertex

        :return: The label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label
    
    @property
    def n_atoms(self):
        """ The number of atoms in the subvertex

        :return: The number of atoms
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return (self._hi_atom - self._lo_atom) + 1
    
    @property
    def constraints(self):
        """ An iterable constraints for the subvertex

        :return: iterable of constraints
        :rtype: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint\
                    .AbstractConstraint`
        :raise None: Raises no known exceptions
        """
        return self._constraints
    
    @property
    def lo_atom(self):
        """ The id of the first atom in the subvertex

        :return: The id of the first atom
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._lo_atom

    @property
    def hi_atom(self):
        """ The id of the last atom in the subvertex

        :return: The id of the last atom
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._hi_atom
