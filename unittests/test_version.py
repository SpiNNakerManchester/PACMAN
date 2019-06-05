import unittest
import spinn_utilities
import spinn_machine
import pacman


class Test(unittest.TestCase):
    """ Tests for the SCAMP version comparison
    """

    def test_compare_versions(self):
        spinn_utilities_parts = spinn_utilities.__version__.split('.')
        spinn_machine_parts = spinn_machine.__version__.split('.')
        pacman_parts = pacman.__version__.split('.')

        self.assertEquals(spinn_utilities_parts[0], pacman_parts[0])
        self.assertLessEqual(spinn_utilities_parts[1], pacman_parts[1])

        self.assertEquals(spinn_machine_parts[0], pacman_parts[0])
        self.assertLessEqual(spinn_machine_parts[1], pacman_parts[1])
