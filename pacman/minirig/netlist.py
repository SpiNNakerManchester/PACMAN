"""Represent and work with vertices and netlists.
"""


class Net(object):
    """A net represents connectivity from one sourcexy to many vertices.

    Attributes
    ----------
    source : vertex
        The vertex which is the source of the net.
    sinks : list
        A list of vertices that the net connects to.
    """

    def __init__(self, sourcexy, post_vertexes):
        """Create a new Net.

        Parameters
        ----------
        source : vertex
        sinks : list or vertex
            If a list of vertices is provided then the list is copied, whereas
            if a single vertex is provided then this used to create the list of
            sinks.
        """
        self.sourcexy = sourcexy
        self.post_vertexes = post_vertexes
