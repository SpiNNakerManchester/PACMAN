from pacman.model.graphs.application import ApplicationVertex
from pacman.model.graphs.machine import SimpleMachineVertex
from pacman.model.resources \
    import ResourceContainer, CPUCyclesPerTickResource, DTCMResource, \
    SDRAMResource


def get_resources_used_by_atoms(lo_atom, hi_atom, vertex_in_edges):
    vertex = Vertex(1, None)
    cpu_cycles = vertex.get_cpu_usage_for_atoms(lo_atom, hi_atom)
    dtcm_requirement = vertex.get_dtcm_usage_for_atoms(lo_atom, hi_atom)
    sdram_requirement = vertex.get_sdram_usage_for_atoms(
        lo_atom, hi_atom, vertex_in_edges)
    return ResourceContainer(
        cpu_cycles=CPUCyclesPerTickResource(cpu_cycles),
        dtcm=DTCMResource(dtcm_requirement),
        sdram=SDRAMResource(sdram_requirement))


class Vertex(ApplicationVertex):
    def __init__(self, n_atoms, label):
        super(Vertex, self).__init__(label=label, max_atoms_per_core=256)
        # What to do with n_atoms?
        self._model_based_max_atoms_per_core = 256

    def get_cpu_usage_for_atoms(self, lo_atom, hi_atom):
        return 10 * (hi_atom - lo_atom)

    def get_dtcm_usage_for_atoms(self, lo_atom, hi_atom):
        return 200 * (hi_atom - lo_atom)

    def get_sdram_usage_for_atoms(
            self, vertex_slice, graph):
        return 4000 + 50 * (vertex_slice.hi_atom - vertex_slice.lo_atom)


class MachineVertex(SimpleMachineVertex):
    def __init__(self, lo_atom, hi_atom, resources_required, label=None,
                 constraints=None):
        super(MachineVertex, self).__init__(
            lo_atom, hi_atom, resources_required, label=label,
            constraints=constraints)
        self._model_based_max_atoms_per_core = 256
