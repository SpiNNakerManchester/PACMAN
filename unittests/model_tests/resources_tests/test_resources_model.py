"""
test for the resources model
"""

import unittest
from pacman.model.resources import SDRAMResource, CPUCyclesPerTickResource
from pacman.model.resources import DTCMResource, ResourceContainer
from pacman.model.resources import IPtagResource, ReverseIPtagResource
from pacman.model.resources import \
    SpecificBoardIPtagResource, SpecificBoardReverseIPtagResource


class TestResourceModels(unittest.TestCase):
    """
    unit tests on the resources object
    """

    def test_sdram(self):
        """
        test that adding a sdram resource to a resoruce container works
        correctly
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
        """
        sdram = SDRAMResource(128 * (2**20))
        dtcm = DTCMResource(128 * (2**20) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**20) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(container.sdram.get_value(), 128 * (2**20))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**20) + 1)
        self.assertEqual(container.cpu_cycles.get_value(), 128 * (2**20) + 2)

        sdram = SDRAMResource(128 * (2**19))
        dtcm = DTCMResource(128 * (2**19) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**19) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(container.sdram.get_value(), 128 * (2**19))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**19) + 1)
        self.assertEqual(container.cpu_cycles.get_value(), 128 * (2**19) + 2)

        sdram = SDRAMResource(128 * (2**21))
        dtcm = DTCMResource(128 * (2**21) + 1)
        cpu = CPUCyclesPerTickResource(128 * (2**21) + 2)

        container = ResourceContainer(dtcm, sdram, cpu)
        self.assertEqual(container.sdram.get_value(), 128 * (2**21))
        self.assertEqual(container.dtcm.get_value(), 128 * (2**21) + 1)
        self.assertEqual(container.cpu_cycles.get_value(), 128 * (2**21) + 2)

    def test_tags_resources(self):
        IPtagResource("1", 2, 3)  # Minimal args
        iptr = IPtagResource("1.2.3.4", 2, 3, 4, 5)
        self.assertEqual(iptr.ip_address, "1.2.3.4")
        self.assertEqual(iptr.port, 2)
        self.assertEqual(iptr.strip_sdp, 3)
        self.assertEqual(iptr.tag, 4)
        self.assertEqual(iptr.traffic_identifier, 5)
        self.assertEqual(iptr.get_value(), ['1.2.3.4', 2, 3, 4, 5])
        self.assertEqual(str(iptr),
                         "IPTagResource(ip_address=1.2.3.4, port=2, "
                         "strip_sdp=3, tag=4, traffic_identifier=5)")

        ReverseIPtagResource()  # Minimal args
        riptr = ReverseIPtagResource(1, 2, 3)
        self.assertEqual(riptr.port, 1)
        self.assertEqual(riptr.sdp_port, 2)
        self.assertEqual(riptr.tag, 3)
        self.assertEqual(riptr.get_value(), [1, 2, 3])
        self.assertEqual(str(riptr),
                         "ReverseIPTagResource(port=1, sdp_port=2, tag=3)")

        b = "4.3.2.1"

        SpecificBoardIPtagResource(b, "1", 2, 3)  # Minimal args
        iptr = SpecificBoardIPtagResource(b, "1.2.3.4", 2, 3, 4, 5)
        self.assertEqual(iptr.board, b)
        self.assertEqual(iptr.ip_address, "1.2.3.4")
        self.assertEqual(iptr.port, 2)
        self.assertEqual(iptr.strip_sdp, 3)
        self.assertEqual(iptr.tag, 4)
        self.assertEqual(iptr.traffic_identifier, 5)
        self.assertEqual(iptr.get_value(), [b, '1.2.3.4', 2, 3, 4, 5])
        self.assertEqual(str(iptr),
                         "IPTagResource(board_address=" + b + ", "
                         "ip_address=1.2.3.4, port=2, strip_sdp=3, tag=4, "
                         "traffic_identifier=5)")

        SpecificBoardReverseIPtagResource(b)  # Minimal args
        riptr = SpecificBoardReverseIPtagResource(b, 1, 2, 3)
        self.assertEqual(riptr.board, b)
        self.assertEqual(riptr.port, 1)
        self.assertEqual(riptr.sdp_port, 2)
        self.assertEqual(riptr.tag, 3)
        self.assertEqual(riptr.get_value(), [b, 1, 2, 3])
        self.assertEqual(str(riptr),
                         "ReverseIPTagResource(board=" + b + ", port=1, "
                         "sdp_port=2, tag=3)")


if __name__ == '__main__':
    unittest.main()
