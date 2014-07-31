
def locate_constrants_of_type(constraints, constraint_type):
    """locates all constraints of a given type out of a list

    :param constraints: a iterable of
     pacman.model.constraints.AbstractConstraint.AbstractConstraint
    :type constraints: a iterable object
    :param constraint_type: a impliemntation of a
    pacman.model.constraint.abstract_partitioner_constrant.AbstractpartitionConstraint
    :type constraint_type: a impliemntation of a
    pacman.model.constraint.abstract_partitioner_constrant.AbstractpartitionConstraint
    :return: a list containing only
    pacman.model.constraints.partitioner_maximum_size_constraint constraints
    or a empty list if none exist
    :rtype: iterable object
    :raises None: no known exceptions
    """
    passed_constraints = list()
    for constrant in constraints:
        if issubclass(type(constrant) , type(constraint_type)):
            passed_constraints.append(constrant)

    return passed_constraints