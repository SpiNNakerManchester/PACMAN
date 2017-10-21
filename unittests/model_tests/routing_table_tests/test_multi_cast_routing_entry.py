"""
TestMulticastrouting entry
"""

# spinnmanchine imports
from spinn_machine import MulticastRoutingEntry

# general imports
import unittest


class TestMultiCastRoutingEntry(unittest.TestCase):
    """
    tests for the routing table object
    """

    def test_new_multicast_routing_table_entry(self):
        """
        test that creating a multicast routing entry works
        """
        key_combo = 0xff00
        mask = 0xff00
        proc_ids = list()
        link_ids = list()
        for i in range(18):
            proc_ids.append(i)
        for i in range(6):
            link_ids.append(i)
        MulticastRoutingEntry(key_combo, mask, proc_ids, link_ids, True)


if __name__ == '__main__':
    unittest.main()
