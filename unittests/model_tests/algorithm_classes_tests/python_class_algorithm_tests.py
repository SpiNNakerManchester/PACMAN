from pacman.executor.algorithm_classes.python_class_algorithm \
    import PythonClassAlgorithm

# general imports
import unittest

class TestPythonClassAlgorithm(unittest.TestCase):
    """
    tests which test the application graph object
    """

    def test_python_module(self):
        python_module = "Foo"
        alg = PythonClassAlgorithm("algorithm_id", [], [], [],
            python_module, "python_function")
        self.assertEquals(python_module, alg._python_module)