__author__ = 'daviess'

from pacman.constraints.abstract_constraint import AbstractConstraint


class Subvertex(object):
    """ Create a new subvertex object related to a vertex """

    def __init__(self, vertex, lo_atom, hi_atom, label=None, constraints=None):
        """

        :param vertex: The vertex to which this subvertex refers
        :param lo_atom: The id of the first atom in the subvertex with\
                        reference to the atoms in the vertex
        :param hi_atom: The id of the last atom in the subvertex with\
                        reference to the atoms in the vertex
        :param label: The name of the subvertex
        :param constraints: The constraints for partitioning and placement
        :type vertex: pacman.graph.vertex.Vertex
        :type lo_atom: int
        :type hi_atom: int
        :type label: str or None
        :type constraints: list of Constraint objects
        :return: a Vertex object
        :rtype: pacman.graph.vertex.Vertex
        :raise None: Raises no known exceptions
        """
        self._label = label
        self._vertex = vertex
        self._lo_atom = lo_atom
        self._hi_atom = hi_atom
        self._constraints = list()

        self.add_constraints(constraints)

    def add_constraint(self, constraint):
        """
        Adds a new constraint to the collection of constraints for the subvertex

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
        Adds a list of constraints to the collection of constraints for the subvertex

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
        constraints to the collection of constraints for the subvertex

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
        Returns the label of the subvertex

        :return: The name of the subvertex
        :rtype: str or None
        :raise None: Raises no known exceptions
        """
        return self._label

    @property
    def n_atoms(self):
        """
        Returns the number of atoms in the subvertex

        :return: The number of atoms in the subvertex
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return (self._hi_atom - self._lo_atom) + 1

    @property
    def lo_atom(self):
        """
        Returns the id of the first atom in the subvertex

        :return: The id of the first atom in the subvertex
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._lo_atom

    @property
    def hi_atom(self):
        """
        Returns the id of the last atom in the subvertex

        :return: The id of the last atom in the subvertex
        :rtype: int
        :raise None: Raises no known exceptions
        """
        return self._hi_atom

    @property
    def constraints(self):
        """
        Returns the list of constraints for the particular subvertex

        :return: the list of constraints
        :rtype: list of pacman.constraints.abstract_constraint.AbstractConstraint
        :raise None: Raises no known exceptions
        """
        return self._constraints

    @property
    def vertex(self):
        """
        Returns the vertex object to which the subvertex refers

        :return: The vertex object to which the subvertex refers
        :rtype: pacman.graph.vertex.Vertex
        :raise None: Raises no known exceptions
        """
        return self._vertex
