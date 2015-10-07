import unittest


class MyTestCase(unittest.TestCase):

    @unittest.skip("demonstrating skipping")
    def test_something(self):
        self.assertEqual(True, False, "Test not implemented yet")


if __name__ == '__main__':
    unittest.main()
