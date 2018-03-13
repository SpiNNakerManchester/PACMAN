import hashlib


def hash(string):  # @ReservedAssignment
    """ Get the MD5 hash of the given string.

    :type string: str
    :rtype: str
    """
    return hashlib.md5(string.encode()).hexdigest()


def ident(object):  # @ReservedAssignment
    """ Get the ID of the given object.

    :type object: object
    :rtype: str
    """
    return str(id(object))
