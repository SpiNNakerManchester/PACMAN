"""Represent and work with vertices and netlists.
"""


class Net(object):
    """A net represents connectivity from one vertex to many vertices.

    Attributes
    ----------
    source : vertex
        The vertex which is the source of the net.
    sinks : list
        A list of vertices that the net connects to.
    """

    def __init__(self, source, sinks):
        """Create a new Net.

        Parameters
        ----------
        source : vertex
        sinks : list or vertex
            If a list of vertices is provided then the list is copied, whereas
            if a single vertex is provided then this used to create the list of
            sinks.
        """
        self.source = source

        # If the sinks is a list then copy it, otherwise construct a new list
        # containing the sink we were given.
        if isinstance(sinks, list):
            self.sinks = sinks[:]
        else:
            self.sinks = [sinks]

    def __contains__(self, vertex):
        """Test if a supplied vertex is a source or sink of this net."""
        return vertex == self.source or vertex in self.sinks

    def __iter__(self):
        """Iterate over all vertices in the net, starting with the source."""
        yield self.source
        for vertex in self.sinks:
            yield vertex
