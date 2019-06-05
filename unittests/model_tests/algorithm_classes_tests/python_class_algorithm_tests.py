import unittest
from pacman.executor.algorithm_classes import PythonClassAlgorithm


class TestPythonClassAlgorithm(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_python_module(self):
        python_module = "Foo"
        alg = PythonClassAlgorithm("algorithm_id", [], [], [],
                                   python_module, "python_function")
        self.assertEqualss(python_module, alg._python_module)
