def intersect(key_a, mask_a, key_b, mask_b):
    """Return if key-mask pairs intersect (i.e., would both match some of the
    same keys).

    For example, the key-mask pairs ``00XX`` and ``001X`` both match the keys
    ``0010`` and ``0011`` (i.e., they do intersect)::

        >>> intersect(0b0000, 0b1100, 0b0010, 0b1110)
        True

    But the key-mask pairs ``00XX`` and ``11XX`` do not match any of the same
    keys (i.e., they do not intersect)::

        >>> intersect(0b0000, 0b1100, 0b1100, 0b1100)
        False

    Parameters
    ----------
    key_a : int
    mask_a : int
        The first key-mask pair
    key_b : int
    mask_b : int
        The second key-mask pair

    Returns
    -------
    bool
        True if the two key-mask pairs intersect otherwise False.
    """
    return (key_a & mask_b) == (key_b & mask_a)
