from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanConfigurationException
from pacman.exceptions import PacmanValueError

from pacman.model.constraints.abstract_constraints.\
    abstract_placer_constraint \
    import AbstractPlacerConstraint
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_iptag_constraint \
    import TagAllocatorRequireIptagConstraint
from pacman.model.constraints.tag_allocator_constraints\
    .tag_allocator_require_reverse_iptag_constraint \
    import TagAllocatorRequireReverseIptagConstraint


def locate_constraints_of_type(constraints, constraint_type):
    """ Locates all constraints of a given type out of a list

    :param constraints: The constraints to filter
    :type constraints: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :param constraint_type: The type of constraints to return
    :type constraint_type:\
                :py:class:`pacman.model.constraint.abstract_partitioner_constraint.AbstractPartitionConstraint`
    :return: The constraints of constraint_type that are\
                found in the constraints given
    :rtype: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :raises None: no known exceptions
    """
    passed_constraints = list()
    for constraint in constraints:
        if isinstance(constraint, constraint_type):
            passed_constraints.append(constraint)
    return passed_constraints


def check_algorithm_can_support_constraints(
        constrained_vertices, supported_constraints, abstract_constraint_type):
    """ Helper method to find out if an algorithm can support all the\
        constraints given the objects its expected to work on

    :param constrained_vertices: a list of constrained vertices which each has\
                constraints given to the algorithm
    :type constrained_vertices: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :param supported_constraints: The constraints supported
    :type supported_constraints: iterable of\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :param abstract_constraint_type: The overall abstract constraint type\
                supported
    :type constraints:\
                :py:class:`pacman.model.constraints.AbstractConstraint.AbstractConstraint`
    :return: Nothing is returned
    :rtype: None
    :raise pacman.exceptions.PacmanInvalidParameterException: when the\
                algorithm cannot support the constraints demanded of it
    """
    for constrained_vertex in constrained_vertices:
        for constraint in constrained_vertex.constraints:
            if isinstance(constraint, abstract_constraint_type):
                found = False
                for supported_constraint in supported_constraints:
                    if isinstance(constraint, supported_constraint):
                        found = True
                        break

                if not found:
                    raise PacmanInvalidParameterException(
                        "constraints", constraint.__class__,
                        "Constraints of this class are not supported by this"
                        " algorithm")


def sort_objects_by_constraint_authority(objects):
    """ Takes the subverts of a subgraph and orders them into a list\
        with a order based off rank on the constraint\
    :param objects: The objects to be sorted. need to have a constraints
    :type objects: iterable of soem object with constraints
    :return: A list of ordered objects
    :rtype: list of objects
    :raise None: this method does not raise any known exceptions
    """
    rank_to_object_mapping = dict()
    for current_object in objects:
        if not hasattr(current_object, "constraints"):
            raise PacmanConfigurationException(
                "the object given to the "
                "sort_objects_by_constraint_authority method does not "
                "contain constraints. Every object must have at least a "
                "max atoms per core constraint")
        max_rank_so_far = 0
        for constraint in current_object.constraints:
            # only store ranks for placer contraints and ones that are better
            # than already seen
            if (isinstance(constraint, AbstractPlacerConstraint) and
                    constraint.rank >= max_rank_so_far):
                max_rank_so_far = constraint.rank
        if max_rank_so_far not in rank_to_object_mapping.keys():
            rank_to_object_mapping[max_rank_so_far] = list()
        rank_to_object_mapping[max_rank_so_far].append(current_object)

    # collected them all
    ordered_keys = sorted(rank_to_object_mapping.keys(), reverse=True)
    ordered_objects = list()
    for ordered_key in ordered_keys:
        object_list = rank_to_object_mapping[ordered_key]
        for current_object in object_list:
            ordered_objects.append(current_object)
    return ordered_objects


def _check_constrained_value(value, current_value):
    """ Checks that the current value and a new value match

    :param value: The value to check
    :param current_value: The existing value
    """
    if (current_value is not None and value is not None
            and value != current_value):
        raise PacmanValueError(
            "Multiple constraints with conflicting values")
    if value is not None:
        return value
    return current_value


def get_chip_and_core(constraints, chips=None):
    """ Get an assigned chip and core from a set of constraints

    :param constraints: The set of constraints to get the values from.  Note\
                that any type of constraint can be in the list but only those\
                relevant will be used
    :type constraints: iterable of\
                :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
    :param chips: Optional list of tuples of (x, y) coordinates of chips,\
                restricting the allowed chips
    :type chips: iterable of (int, int)
    :return: tuple of iterable of chip coordinates, and processor id, both of\
                which might be None
    :rtype: (iterable of (int, int), int)
    """
    x = None
    y = None
    p = None
    for constraint in constraints:
        if isinstance(constraint, PlacerChipAndCoreConstraint):
            x = _check_constrained_value(constraint.x, x)
            y = _check_constrained_value(constraint.y, y)
            p = _check_constrained_value(constraint.p, p)

    if chips is not None and x is not None and y is not None:
        if (x, y) not in chips:
            raise PacmanInvalidParameterException(
                "x, y and chips",
                "{}, {} and {}".format(x, y, chips),
                "The constraint cannot be met with the given chips")
    if x is not None and y is not None:
        chips = [(x, y)]
    return (chips, p)


def get_ip_tag_info(constraints):
    """ Get the ip tag constraint information from the constraints

    :param constraints: The set of constraints to get the values from.  Note\
                that any type of constraint can be in the list but only those\
                relevant will be used
    :type constraints: iterable of\
                :py:class:`pacman.model.constraints.abstract_constraint.AbstractConstraint`
    :return: A tuple of board address, iterable of ip tag constraints and \
                iterable of reverse ip tag constraints
    :rtype: (str, iterable of\
                :py:class:`pacman.model.constraints.tag_allocator_constraints.tag_allocator_require_iptag_constraint.TagAllocatorRequireIptagConstraint`,
                iterable of\
                :py:class:`pacman.model.constraints.tag_allocator_constraints.tag_allocator_require_reverse_iptag_constraint.TagAllocatorRequireReverseIptagConstraint`)
    """
    board_address = None
    ip_tags = list()
    reverse_ip_tags = list()
    for constraint in constraints:
        if isinstance(constraint,
                      TagAllocatorRequireIptagConstraint):
            board_address = _check_constrained_value(
                constraint.board_address, board_address)
            ip_tags.append(constraint)
        if isinstance(constraint,
                      TagAllocatorRequireReverseIptagConstraint):
            board_address = _check_constrained_value(
                constraint.board_address, board_address)
            reverse_ip_tags.append(constraint)
    return board_address, ip_tags, reverse_ip_tags
