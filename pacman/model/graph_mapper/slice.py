from pacman.exceptions import PacmanValueError
import collections


class Slice(collections.namedtuple('Slice',
                                   'lo_atom hi_atom n_atoms as_slice')):
    """ Represents a slice of a vertex.

    :attr int lo_atom: The lowest atom represented in the slice.
    :attr int hi_atom: The highest atom represented in the slice.
    :attr int n_atoms: The number of atoms represented by the slice.
    :attr as_slice: This slice represented as a :py:func:`slice` object (for
                    use in indexing lists, arrays, etc.)
    """
    def __new__(cls, lo_atom, hi_atom):
        """ Create a new Slice object.

        :param int lo_atom: Index of the lowest atom to represent.
        :param int hi_atom: Index of the highest atom to represent.
        :raises PacmanValueError: If the bounds of the slice are invalid.
        """
        if lo_atom < 0:
            raise PacmanValueError('lo_atom < 0')
        if hi_atom < lo_atom:
            raise PacmanValueError(
                'hi_atom {:d} < lo_atom {:d}'.format(hi_atom, lo_atom))

        # Number of atoms represented by this slice
        n_atoms = hi_atom - lo_atom + 1

        # Slice for accessing arrays of values
        as_slice = slice(lo_atom, hi_atom + 1)

        # Create the Slice object as a `namedtuple` with these pre-computed
        # values filled in.
        return super(cls, Slice).__new__(cls, lo_atom, hi_atom, n_atoms,
                                         as_slice)
