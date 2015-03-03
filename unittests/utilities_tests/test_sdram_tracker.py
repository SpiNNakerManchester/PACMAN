import unittest
from pacman.utilities.resource_tracker import ResourceTracker
from spinn_machine.sdram import SDRAM


class TestSDRAMTracker(unittest.TestCase):
    def test_new_sdram_tracker(self):
        sdram = SDRAM(128*(2**20))
        sdram2 = SDRAM(104*(2**20))
        sdram_tracker = ResourceTracker()
        # Add new values to tracker
        sdram_tracker.add_usage(0, 0, sdram.size)
        sdram_tracker.add_usage(1, 0, sdram2.size)
        sdram_tracker.add_usage(0, 1, sdram.size)
        sdram_tracker.add_usage(1, 1, sdram2.size)
        for i in range(2):
            for j in range(2):
                if i == 0:
                    self.assertEqual(sdram_tracker.get_usage(i, j), sdram.size)
                else:
                    self.assertEqual(sdram_tracker.get_usage(i, j), sdram2.size)

        # Add value to existing key
        sdram_tracker.add_usage(0, 0, sdram2.size)
        self.assertEqual(sdram_tracker.get_usage(0, 0),
                         sdram.size + sdram2.size)


if __name__ == '__main__':
    unittest.main()
