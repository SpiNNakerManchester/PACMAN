__author__ = 'stokesa6,daviess'

from pacman.constraints.abstract_constraint import AbstractConstraint


class Vertex(object):
    """ Creates a new vertex object """
    
    def __init__(self, n_atoms, label=None, constraints=None):
        """

        :param n_atoms: The number of atoms that the vertex can be split into
        :param label: The name of the vertex
        :param constraints: The constraints for partitioning and placement
        :type n_atoms: int
        :type label: str or None
        :type constraints: list of Constraint objects
        :return: a Vertex object
        :rtype: pacman.graph.vertex.Vertex
        :raise None: Raises no known exceptions
        """
        self._label = label
        self._n_atoms = n_atoms
        self._constraints = list()

        self.add_constraints(constraints)

    def add_constraint(self, constraint):
        """
        Adds a new constraint to the collection of constraints for the vertex

        :param constraint: constraint to add
        :type constraint: pacman.constraints.abstract_constraint.AbstractConstraint
        :return: None
        :rtype: None
        :raise None: Raises no known exceptions
        """
        if constraint is not None and isinstance(constraint, AbstractConstraint):
            self._constraints.append(constraint)

    def add_constraints(self, constraints):
        """
        Adds a list of constraints to the collection of constraints for the vertex

        :param constraints: list of constraints to add
        :type constraints: list of pacman.constraints.abstract_constraint.AbstractConstraint
        :return: None
        :rtype: None
        :raise None: Raises no known exceptions
        """
        if constraints is not None:
            for next_constraint in constraints:
                if isinstance(next_constraint, AbstractConstraint):
                    self._constraints.append(next_constraint)

    def set_constraints(self, constraints):
        """
        Clears the list of vertex constraints and after adds a list of\
        constraints to the collection of constraints for the vertex

        :param constraints: list of constraints to add
        :type constraints: list of pacman.constraints.abstract_constraint.AbstractConstraint
        :return: None
        :rtype: None
        :raise None: Raises no known exceptions
        """
        self._constraints = list()

        if constraints is not None:
            for next_constraint in constraints:
                if isinstance(next_constraint, AbstractConstraint):
                    self._constraints.append(next_constraint)

    @property
    def label(self):
        """
        Returns the label of the vertex

        :return: The name of the vertex
        :rtype: str or None
        :raise None: Raises no known exceptions
        """
        return self._label
    
    @property
    def n_atoms(self):
        """
        Returns the number of atoms in the vertex

        :return: The number of atoms in the vertex
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._n_atoms
    
    @property
    def constraints(self):
        """ 
        Returns the list of constraints for the particular vertex

        :return: the list of constraints
        :rtype: list of pacman.constraints.abstract_constraint.AbstractConstraint
        :raise None: Raises no known exceptions
        """
        return self._constraints
