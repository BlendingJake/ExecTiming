from exectiming.exectiming import Timer
from exectiming.data_structures import Run
import unittest
from math import e, log


class TestConsistentFeatures(unittest.TestCase):
    def test_with_no_args(self):
        timer = Timer(split=True, start=True)
        timer.log()

        self.assertRaisesRegex(RuntimeWarning, "Arguments must have been logged", timer.best_fit_curve)

    def test_invalid_curve(self):
        timer = Timer(split=True, start=True)
        timer.log(5)

        self.assertRaisesRegex(RuntimeWarning, "Test is an invalid curve type", timer.best_fit_curve,
                               curve_type="Test")

    def test_specific(self):
        timer = Timer(split=True, start=True)
        timer.splits[-1].add_run(Run(time=e ** 2, runs=1, iterations_per_run=1, label=str(2), args=(2,)))
        timer.splits[-1].add_run(Run(time=e ** 5, runs=1, iterations_per_run=1, label=str(5), args=(5,)))
        timer.splits[-1].add_run(Run(time=e ** 8, runs=1, iterations_per_run=1, label=str(8), args=(8,)))

        # would normally return Exponential, make sure it doesn't
        self.assertEqual(timer.best_fit_curve(curve_type="Linear")[0], "Linear")


class TestExponential(unittest.TestCase):
    def test_basic(self):
        timer = Timer(split=True)

        for x in range(0, 10, 2):
            timer.splits[-1].add_run(Run(time=e**x, runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve(curve_type="Exponential")
        self.assertEqual(result[0], "Exponential")
        self.assertEqual(round(result[1]["a"], 4), 0)
        self.assertEqual(round(result[1]["b"], 4), 1)

    def test_complicated(self):
        timer = Timer(split=True)

        for x in range(0, 10, 2):
            timer.splits[-1].add_run(Run(time=3 + 2*e**x, runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve(curve_type="Exponential")
        self.assertEqual(result[0], "Exponential")
        self.assertEqual(round(result[1]["a"], 4), 3)
        self.assertEqual(round(result[1]["b"], 4), 2)

    def test_too_many_args(self):
        timer = Timer(split=True, start=True)
        timer.log(4, 6)

        self.assertRaisesRegex(RuntimeWarning, r"Exponential\'s poll method returned that is couldn\'t run.",
                               timer.best_fit_curve, curve_type="Exponential")


class TestLinear(unittest.TestCase):
    def test_flat(self):
        timer = Timer(split=True)

        for x, y in ((1, 4), (10, 4), (25, 4)):
            timer.splits[-1].add_run(Run(time=y, runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve()
        self.assertEqual(result[0], "Linear")
        self.assertEqual(result[1]["b"], 4)
        self.assertEqual(result[1][0], 0)

    def test_sloped(self):
        timer = Timer(split=True)

        for x, y in ((1, 1), (10, 10), (25, 25)):
            timer.splits[-1].add_run(Run(time=y, runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve()
        self.assertEqual(result[0], "Linear")
        self.assertEqual(result[1]["b"], 0)
        self.assertEqual(result[1][0], 1)


class TestLogarithmic(unittest.TestCase):
    def test_basic(self):
        timer = Timer(split=True)

        for x in range(0, 4):
            timer.splits[-1].add_run(Run(time=x, runs=1, iterations_per_run=1, label=str(x), args=(e**x,)))

        result = timer.best_fit_curve()
        self.assertEqual(result[0], "Logarithmic")
        self.assertEqual(round(result[1]["a"], 4), 0)
        self.assertEqual(round(result[1]["b"], 4), 1)

    def test_complicated(self):
        timer = Timer(split=True)

        for x in range(1, 5):
            timer.splits[-1].add_run(Run(time=2 + 3*log(x), runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve()
        self.assertEqual(result[0], "Logarithmic")
        self.assertEqual(round(result[1]["a"], 4), 2)
        self.assertEqual(round(result[1]["b"], 4), 3)


class TestPolynomial(unittest.TestCase):
    def test_basic(self):
        timer = Timer(split=True)

        for x in range(1, 4):
            timer.splits[-1].add_run(Run(time=1 + x + x**2, runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve()
        self.assertEqual(result[0], "Polynomial")
        self.assertEqual(round(result[1]["a"], 4), 1)
        self.assertEqual(round(result[1]["b"], 4), 1)
        self.assertEqual(round(result[1]["c"], 4), 1)

    def test_complicated(self):
        timer = Timer(split=True)

        for x in range(1, 4):
            timer.splits[-1].add_run(Run(time=4 + 2*x + 4*x**2, runs=1, iterations_per_run=1, label=str(x), args=(x,)))

        result = timer.best_fit_curve()
        self.assertEqual(result[0], "Polynomial")
        self.assertEqual(round(result[1]["a"], 4), 4)
        self.assertEqual(round(result[1]["b"], 4), 2)
        self.assertEqual(round(result[1]["c"], 4), 4)


if __name__ == "__main__":
    unittest.main()
