from abc import ABCMeta
from six import add_metaclass

from pacman.model.partitionable_graph.abstract_partitionable_vertex \
    import AbstractPartitionableVertex
from pacman.model.constraints.placer_constraints\
    .placer_chip_and_core_constraint import PlacerChipAndCoreConstraint


@add_metaclass(ABCMeta)
class AbstractVirtualVertex(AbstractPartitionableVertex):

    def __init__(self, n_neurons, virtual_chip_coords, connected_node_coords,
                 connected_node_edge, machine_time_step, label,
                 max_atoms_per_core):
        AbstractPartitionableVertex.__init__(self, n_neurons, label,
                                             max_atoms_per_core)

        # set up virtual data structures
        self._virtual_chip_coords = virtual_chip_coords
        self._connected_chip_coords = connected_node_coords
        self._connected_chip_edge = connected_node_edge
        placement_constaint = \
            PlacerChipAndCoreConstraint(self._virtual_chip_coords['x'],
                                        self._virtual_chip_coords['y'])
        self.add_constraint(placement_constaint)

    @property
    def model_name(self):
        return "VirtualVertex:{}".format(self.label)

    # inherited from partitonable vertex
    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 0

    def get_sdram_usage_for_atoms(self, vertex_slice, vertex_in_edges):
        return 0

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 0
