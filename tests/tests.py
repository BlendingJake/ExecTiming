import tests_basic
import tests_best_fit_curves
import unittest


if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromModule(tests_basic)
    suite.addTests(unittest.TestLoader().loadTestsFromModule(tests_best_fit_curves))

    unittest.TextTestRunner(verbosity=2).run(suite)
