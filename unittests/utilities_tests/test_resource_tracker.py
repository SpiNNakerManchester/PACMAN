import unittest
from spinn_machine import (
    virtual_machine, Chip, Router, SDRAM, machine_from_chips)
from pacman.model.resources import (
    ResourceContainer, ConstantSDRAM, PreAllocatedResourceContainer,
    CoreResource, SpecificCoreResource)
from pacman.exceptions import PacmanValueError
from pacman.utilities.utility_objs import ResourceTracker


class TestResourceTracker(unittest.TestCase):

    def test_n_cores_available(self):
        machine = virtual_machine(
            width=2, height=2, n_cpus_per_chip=18, with_monitors=True)
        chip = machine.get_chip_at(0, 0)
        preallocated_resources = PreAllocatedResourceContainer(
            specific_core_resources=[
                SpecificCoreResource(chip=chip, cores=[1])],
            core_resources=[
                CoreResource(chip=chip, n_cores=2)])
        tracker = ResourceTracker(
            machine, plan_n_timesteps=None,
            preallocated_resources=preallocated_resources)

        # Should be 14 cores = 18 - 1 monitor - 1 specific core - 2 other cores
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), None), 14)

        # Should be 0 since the core is already pre allocated
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), 1), 0)

        # Should be 1 since the core is not pre allocated
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), 2), 1)

        # Should be 0 since the core is monitor
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), 0), 0)

        # Allocate a core
        tracker._allocate_core(chip, (0, 0), 2)

        # Should be 13 cores as one now allocated
        self.assertEqual(tracker._n_cores_available(chip, (0, 0), None), 13)

    def test_deallocation_of_resources(self):
        machine = virtual_machine(
            width=2, height=2, n_cpus_per_chip=18, with_monitors=True)
        chip_sdram = machine.get_chip_at(1, 1).sdram.size
        res_sdram = 12345

        tracker = ResourceTracker(machine, plan_n_timesteps=None,
                                  preallocated_resources=None)

        sdram_res = ConstantSDRAM(res_sdram)
        resources = ResourceContainer(sdram=sdram_res)
        chip_0 = machine.get_chip_at(0, 0)

        # verify core tracker is empty
        if (0, 0) in tracker._core_tracker:
            raise Exception("shouldnt exist")

        # verify sdram tracker
        if tracker._sdram_tracker[0, 0] != chip_sdram:
            raise Exception("incorrect sdram of {}".format(
                tracker._sdram_tracker[0, 0]))

        # allocate some res
        chip_x, chip_y, processor_id, ip_tags, reverse_ip_tags = \
            tracker.allocate_resources(resources, [(0, 0)])

        # verify chips used is updated
        cores = list(tracker._core_tracker[(0, 0)])
        self.assertEqual(len(cores), chip_0.n_user_processors - 1)

        # verify sdram used is updated
        sdram = tracker._sdram_tracker[(0, 0)]
        self.assertEqual(sdram, chip_sdram-res_sdram)

        if (0, 0) not in tracker._chips_used:
            raise Exception("should exist")

        # deallocate res
        tracker.unallocate_resources(
            chip_x, chip_y, processor_id, resources, ip_tags, reverse_ip_tags)

        # verify chips used is updated
        if ((0, 0) in tracker._core_tracker and
                len(tracker._core_tracker[(0, 0)]) !=
                chip_0.n_user_processors):
            raise Exception("shouldn't exist or should be right size")

        if (0, 0) in tracker._chips_used:
            raise Exception("shouldnt exist")

        # verify sdram tracker
        if tracker._sdram_tracker[0, 0] != chip_sdram:
            raise Exception("incorrect sdram of {}".format(
                tracker._sdram_tracker[0, 0]))

    def test_allocate_resources_when_chip_used(self):
        router = Router([])
        sdram = SDRAM()
        empty_chip = Chip(
            0, 0, [], router, sdram, 0, 0, "127.0.0.1",
            virtual=False, tag_ids=[1])
        machine = machine_from_chips([empty_chip])
        resource_tracker = ResourceTracker(machine, plan_n_timesteps=None)
        with self.assertRaises(PacmanValueError):
            resource_tracker.allocate_resources(
                ResourceContainer(sdram=ConstantSDRAM(1024)))


if __name__ == '__main__':
    unittest.main()
