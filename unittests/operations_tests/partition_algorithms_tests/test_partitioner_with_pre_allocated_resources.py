from pacman.exceptions import PacmanInvalidParameterException, \
    PacmanValueError, PacmanPartitionException
from pacman.model.constraints.placer_constraints import \
    ChipAndCoreConstraint
from pacman.model.graphs.application import ApplicationGraph
from pacman.model.resources import CoreResource
from pacman.model.resources import SpecificCoreResource
from pacman.model.resources import SpecificChipSDRAMResource
from pacman.model.resources import PreAllocatedResourceContainer
from pacman.operations.partition_algorithms import PartitionAndPlacePartitioner
from spinn_machine import VirtualMachine
from uinit_test_objects.test_vertex import TestVertex


class TestPartitionerWithPreAllocatedResources(object):
    """ tests the interaction of the pre allocated res with the partitioner\
     and place partitioner
    """

    def test_1_chip_over_pre_allocated(self):
        machine = VirtualMachine(width=8, height=8)
        graph = ApplicationGraph("Test")
        partitioner = PartitionAndPlacePartitioner()

        # add graph vertices which reside on 0,0
        for _ in range(0, 13):
            graph.add_vertex(TestVertex(
                constraints=[ChipAndCoreConstraint(x=0, y=0)],
                n_atoms=1))

        # add pre-allocated resources for cores on 0,0
        core_pre = CoreResource(chip=machine.get_chip_at(0, 0), n_cores=5)
        pre_allocated_res = PreAllocatedResourceContainer(
            core_resources=[core_pre])

        # run partitioner that should go boom
        try:
            partitioner(graph, machine, pre_allocated_res)
            raise Exception("should have blown up here")
        except PacmanInvalidParameterException:
            pass

    def test_1_chip_under_pre_allocated(self):
        machine = VirtualMachine(width=8, height=8)
        graph = ApplicationGraph("Test")
        partitioner = PartitionAndPlacePartitioner()

        # add graph vertices which reside on 0,0
        for _ in range(0, 13):
            graph.add_vertex(TestVertex(
                constraints=[ChipAndCoreConstraint(x=0, y=0)],
                n_atoms=1))

        # add pre-allocated resources for cores on 0,0
        core_pre = CoreResource(chip=machine.get_chip_at(0, 0), n_cores=4)
        pre_allocated_res = PreAllocatedResourceContainer(
            core_resources=[core_pre])

        # run partitioner that should go boom
        try:
            partitioner(graph, machine, pre_allocated_res)
        except Exception:
            raise Exception("should have blown up here")

    def test_1_chip_pre_allocated_same_core(self):
        machine = VirtualMachine(width=8, height=8)
        graph = ApplicationGraph("Test")
        partitioner = PartitionAndPlacePartitioner()

        # add graph vertices which reside on 0,0
        for p in range(0, 13):
            graph.add_vertex(TestVertex(
                constraints=[ChipAndCoreConstraint(x=0, y=0, p=p)],
                n_atoms=1))

        # add pre-allocated resources for cores on 0,0
        core_pre = SpecificCoreResource(
            chip=machine.get_chip_at(0, 0), cores=[4])
        pre_allocated_res = PreAllocatedResourceContainer(
            specific_core_resources=[core_pre])

        # run partitioner that should go boom
        try:
            partitioner(graph, machine, pre_allocated_res)
            raise Exception("should have blown up here")
        except PacmanValueError:
            pass
        except Exception:
            raise Exception("should have blown up here")

    def test_1_chip_pre_allocated_too_much_sdram(self):
        machine = VirtualMachine(width=8, height=8)
        graph = ApplicationGraph("Test")
        partitioner = PartitionAndPlacePartitioner()

        eight_meg = 8 * 1024 * 1024

        # add graph vertices which reside on 0,0
        for _ in range(0, 13):
            graph.add_vertex(TestVertex(
                constraints=[ChipAndCoreConstraint(x=0, y=0)],
                n_atoms=1,
                fixed_sdram_value=eight_meg))

        # add pre-allocated resources for cores on 0,0
        twenty_meg = 20 * 1024 * 1024
        core_pre = SpecificChipSDRAMResource(
            chip=machine.get_chip_at(0, 0), sdram_usage=twenty_meg)
        pre_allocated_res = PreAllocatedResourceContainer(
            specific_sdram_usage=[core_pre])

        # run partitioner that should go boom
        try:
            partitioner(graph, machine, pre_allocated_res)
            raise Exception("should have blown up here")
        except PacmanPartitionException:
            pass
        except Exception:
            raise Exception("should have blown up here")

    def test_1_chip_no_pre_allocated_too_much_sdram(self):
        machine = VirtualMachine(width=8, height=8)
        graph = ApplicationGraph("Test")
        partitioner = PartitionAndPlacePartitioner()

        eight_meg = 8 * 1024 * 1024

        # add graph vertices which reside on 0,0
        for _ in range(0, 13):
            graph.add_vertex(TestVertex(
                constraints=[ChipAndCoreConstraint(x=0, y=0)],
                n_atoms=1,
                fixed_sdram_value=eight_meg))

        # add pre-allocated resources for cores on 0,0
        pre_allocated_res = PreAllocatedResourceContainer()

        # run partitioner that should go boom
        try:
            partitioner(graph, machine, pre_allocated_res)
        except Exception:
            raise Exception("should have blown up here")


if __name__ == "__main__":

    test = TestPartitionerWithPreAllocatedResources()
    test.test_1_chip_over_pre_allocated()
    test.test_1_chip_under_pre_allocated()
    test.test_1_chip_pre_allocated_same_core()
    test.test_1_chip_pre_allocated_too_much_sdram()
