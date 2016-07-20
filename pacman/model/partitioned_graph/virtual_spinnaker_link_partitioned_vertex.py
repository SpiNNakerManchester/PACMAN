from pacman.model.partitioned_graph.abstract_virtual_partitioned_vertex import \
    AbstractVirtualPartitionedVertex


class VirtualSpinnakerLinkPartitionedVertex(AbstractVirtualPartitionedVertex):

    def __init__(
            self, resources_required, label, spinnaker_link_id,
            constraints=None, board_address=None):

        AbstractVirtualPartitionedVertex.__init__(
            self, resources_required, label, board_address, constraints)

        self._spinnaker_link_id = spinnaker_link_id

    @property
    def spinnaker_link_id(self):
        """ The id of the spinnaker link being used
        """
        return self._spinnaker_link_id