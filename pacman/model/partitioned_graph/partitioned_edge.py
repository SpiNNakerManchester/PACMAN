class PartitionedEdge(object):
    """ Represents an edge between two PartitionedVertex instances
    """

    def __init__(self, pre_subvertex, post_subvertex, constraints=None,
                 label=None):
        """

        :param pre_subvertex: the subvertex at the start of the subedge
        :type pre_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param post_subvertex: the subvertex at the end of the subedge
        :type post_subvertex:\
                    :py:class:`pacman.model.partitioned_graph.subvertex.PartitionedVertex`
        :param constraints: The constraints of the vertex
        :type constraints: list of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        :param label: The name of the edge
        :type label: str
        :param n_keys: The number of distinct keys required by the partitioned\
                    edge for routing purposes
        :raise None: Raises no known exceptions
        """
        self._pre_subvertex = pre_subvertex
        self._post_subvertex = post_subvertex
        self._label = label
        self._constraints = constraints

    @property
    def pre_subvertex(self):
        """ The partitioned vertex at the start of the edge

        :return: the incoming partitioned vertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._pre_subvertex

    @property
    def post_subvertex(self):
        """ The partitioned vertex at the end of the edge

        :return: the outgoing partitioned vertex
        :rtype: :py:class:`pacman.model.subgraph.subvertex.PartitionedVertex`
        :raise None: Raises no known exceptions
        """
        return self._post_subvertex

    @property
    def constraints(self):
        """ The constraints of the edge

        :return: The constraints, or None if there are not constraints
        :rtype: iterable of\
                    :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        """
        return self._constraints

    def add_constraint(self, constraint):
        """ Adds a constraint to the edge

        :param constraint: The constraint to add
        :type constraint:\
            :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
        """
        if self._constraints is None:
            self._constraints = list([constraint])
        else:
            self._constraints.append(constraint)

    @property
    def label(self):
        """ The label of the edge

        :return: The name, or None if there is no label
        :rtype: str
        :raise None: Raises no known exceptions
        """
        return self._label

    def __str__(self):
        return "PartitionedEdge:{}->{}".format(self._pre_subvertex,
                                               self._post_subvertex)

    def __repr__(self):
        return self.__str__()
