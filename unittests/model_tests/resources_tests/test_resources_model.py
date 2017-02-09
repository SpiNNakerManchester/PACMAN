"""
test for the resources model
"""

import unittest
from pacman.model.resources.sdram_resource import SDRAMResource
from pacman.model.resources.cpu_cycles_per_tick_resource \
    import CPUCyclesPerTickResource
from pacman.model.resources.dtcm_resource import DTCMResource
from pacman.model.resources.resource_container import ResourceContainer


class TestResourceModels(unittest.TestCase):
    """
    unit tests on the resources object
    """

    def test_sdram(self):
        """
        test that adding a sdram resource to a resoruce container works
        correctly
        :return:
        """
        sdram = SDRAMResource(128 * (2**20))
        self.assertEqual(sdram.get_value(), 128 * (2**20))
        sdram = SDRAMResource(128 * (2**19))
        self.assertEqual(sdram.get_value(), 128 * (2**19))
        sdram = SDRAMResource(128 * (2**21))
        self.assertEqual(sdram.get_value(), 128 * (2**21))

    def test_dtcm(self):
        """
        test that adding a dtcm resource to a resoruce container works
        correctly
        :return:
        """
        dtcm = DTCMResource(128 * (2**20))
        self.assertEqual(dtcm.get_value(), 128 * (2**20))
        dtcm = DTCMResource(128 * (2**19))
        self.assertEqual(dtcm.get_value(), 128 * (2**19))
        dtcm = DTCMResource(128 * (2**21))
        self.assertEqual(dtcm.get_value(), 128 * (2**21))

    def test_cpu(self):
        """
        test that adding a cpu resource to a resoruce container works
        correctly
        :return:
        """
        cpu = CPUCyclesPerTickResource(128 * (2**20))
        self.assertEqual(cpu.get_value(), 128 * (2**20))
        cpu = CPUCyclesPerTickResource(128 * (2**19))
        self.assertEqual(cpu.get_value(), 128 * (2**19))
        cpu = CPUCyclesPerTickResource(128 * (2**21))
        self.assertEqual(cpu.get_value(), 128 * (2**21))

    def test_resource_container(self):
        """
        tests that creating multiple resoruce containers doesnt cause issues.
        :return:
        """
        sdram = SDRAMResource(128 * (2**20))
        dtcm = DTCMResource(128 * (2**20) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**20) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(container.sdram.get_value(), 128 * (2**20))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**20) + 1)
        self.assertEqual(container.cpu.get_value(), 128 * (2**20) + 2)

        sdram = SDRAMResource(128 * (2**19))
        dtcm = DTCMResource(128 * (2**19) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**19) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(container.sdram.get_value(), 128 * (2**19))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**19) + 1)
        self.assertEqual(container.cpu.get_value(), 128 * (2**19) + 2)

        sdram = SDRAMResource(128 * (2**21))
        dtcm = DTCMResource(128 * (2**21) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**21) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(container.sdram.get_value(), 128 * (2**21))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**21) + 1)
        self.assertEqual(container.cpu.get_value(), 128 * (2**21) + 2)


if __name__ == '__main__':
    unittest.main()
