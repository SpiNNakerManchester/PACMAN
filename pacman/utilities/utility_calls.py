from pacman.model.constraints.abstract_constraints.abstract_placer_constraint import \
    AbstractPlacerConstraint
from pacman.exceptions import PacmanInvalidParameterException
from pacman.exceptions import PacmanConfigurationException
from pacman.utilities import constants


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

    :param constrained_vertices: a list of constrained vertices which each has \
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
    """ Helper method for all placers.\
        It takes the subverts of a subgraph and orders them into a list\
        with a order based off rank on the constraint\
        NOT TO BE CALLED OUTSIDE IMPLEMTATIONS OF THIS CLASS
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
            #only store ranks for placer contraints and ones that are better
            #than already seen
            if (isinstance(constraint, AbstractPlacerConstraint) and
                    constraint.rank >= max_rank_so_far):
                max_rank_so_far = constraint.rank
        if not max_rank_so_far in rank_to_object_mapping.keys():
            rank_to_object_mapping[max_rank_so_far] = list()
        rank_to_object_mapping[max_rank_so_far].append(current_object)

    #collected them all
    ordered_keys = \
        sorted(rank_to_object_mapping.keys(), key=int, reverse=True)
    ordered_objects = list()
    for ordered_key in ordered_keys:
        object_list = rank_to_object_mapping[ordered_key]
        for current_object in object_list:
            ordered_objects.append(current_object)
    return ordered_objects


def deduce_size_from_mask(mask):
    """ from the mask, returns the max_number of neurons it covers

    :param mask: the mask to deduce the number of neurons from
    :return: the max_neurons deduced from the mask
    """
    position = 0
    size = 0
    while position < constants.BITS_IN_KEY:
        temp_mask = mask >> position
        temp_mask &= 0xF
        if temp_mask != 0xF:
            size += (temp_mask << position)
        position += 4
    return size