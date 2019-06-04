from pytimer.pytimer import StaticTimer, Timer
import unittest
from io import StringIO
from time import sleep


class TestStaticBasic(unittest.TestCase):
    def test_decorate(self):
        out = StringIO()

        @StaticTimer.decorate(output_stream=out)
        def basic(val):
            return val + 1

        self.assertEqual(basic(5), 6)
        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format("basic", ""))

    def test_decorate_no_display(self):
        @StaticTimer.decorate(display=False, runs=5, average_runs=False)
        def basic(val):
            return val + 1

        response = basic(5)
        self.assertIsInstance(response, tuple)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0], 6)
        self.assertIsInstance(response[1], list)
        self.assertEqual(len(response[1]), 5)

    def test_decorate_no_display_averaged(self):
        @StaticTimer.decorate(display=False, runs=5)
        def basic(val):
            return val + 1

        response = basic(5)
        self.assertIsInstance(response, tuple)
        self.assertEqual(len(response), 2)
        self.assertEqual(response[0], 6)
        self.assertIsInstance(response[1], float)

    def test_decorate_log_arguments(self):
        out = StringIO()

        @StaticTimer.decorate(display=True, output_stream=out, log_arguments=True)
        def basic(val):
            return val+1

        self.assertEqual(basic(5), 6)
        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format("basic(5)", ""))

    def test_decorate_callable_args(self):
        out = StringIO()

        @StaticTimer.decorate(runs=2, output_stream=out, call_callable_args=True, log_arguments=True,
                              average_runs=False)
        def basic(val):
            return val + 1

        basic(lambda: 8)

        lines = out.getvalue().split("\n")
        self.assertEqual(lines[0][13:], " - {:42} [runs=  1, iterations=  1] {:<20}".format("basic(8)", "| Run 1"))
        self.assertEqual(lines[1][13:], " - {:42} [runs=  1, iterations=  1] {:<20}".format("basic(8)", "| Run 2"))

    def test_elapsed_basic(self):
        out = StringIO()

        StaticTimer.start_elapsed()
        sleep(0.001)
        StaticTimer.elapsed(output_stream=out)

        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format("Elapsed", ""))

    def test_elapsed_basic_no_display(self):
        StaticTimer.start_elapsed()
        sleep(0.001)
        result = StaticTimer.elapsed(display=False)
        self.assertIsInstance(result, float)

    def test_elapsed_with_no_start(self):
        StaticTimer._elapsed_time = None
        self.assertRaises(RuntimeWarning, StaticTimer.elapsed)

    def test_time_it_basic_callable(self):
        def basic(val):
            return val + 1

        out = StringIO()
        result = StaticTimer.time_it(basic, 5, output_stream=out)

        self.assertEqual(result, 6)
        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format("basic", ""))

    def test_time_it_callable_log_arguments(self):
        def basic(val):
            return val + 1

        out = StringIO()
        StaticTimer.time_it(basic, 5, log_arguments=True, output_stream=out)
        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format("basic(5)", ""))

    def test_time_it_basic_string(self):
        string = "len([i for i in range(100)])"

        out = StringIO()
        result = StaticTimer.time_it(string, output_stream=out)

        self.assertEqual(result, 100)
        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format(string, ""))

    def test_time_it_string_no_display(self):
        result = StaticTimer.time_it("len([i for i in range(100)])", display=False)

        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], 100)
        self.assertIsInstance(result[1], float)

    def test_time_it_bad_globals(self):
        self.assertRaisesRegex(NameError, r"name \'floor\' is not defined", StaticTimer.time_it, "floor(2.5432)")

    def test_time_it_globals(self):
        from math import floor
        self.assertEqual(StaticTimer.time_it("floor(2.5432)", globals={"floor": floor}, display=False)[0], 2)


class TestTimerBasic(unittest.TestCase):
    def test_decorate_basic(self):
        timer = Timer()

        @timer.decorate(runs=5, iterations_per_run=2, log_arguments=True)
        def basic(val):
            return val + 1

        self.assertEqual(basic(5), 6)
        self.assertEqual(timer.splits[0].label, "basic")
        self.assertEqual(len(timer.splits[0].runs), 5)
        self.assertEqual(timer.splits[0].runs[0].iterations_per_run, 2)
        self.assertEqual(timer.splits[0].runs[0].args, (5,))
        self.assertEqual(timer.splits[0].runs[0].kwargs, {})

    def test_decorate_no_split(self):
        timer = Timer()

        @timer.decorate(split=False)
        def basic(val):
            return val + 1

        self.assertRaisesRegex(RuntimeWarning, "No split exists.", basic, 8)

    def test_log_no_split(self):
        timer = Timer()
        timer.start()
        self.assertRaisesRegex(RuntimeWarning, "A split does not exist to log this time in!", timer.log)

    def test_log_not_started(self):
        timer = Timer(split=True)
        self.assertRaisesRegex(RuntimeWarning, r"start\(\) must be called before log\(\)", timer.log)

    def test_log_basic(self):
        timer = Timer(split=True)
        timer.start()
        sleep(0.001)
        timer.log(5, 6, label="Test", something=5, runs=2, iterations_per_run=2)

        self.assertEqual(timer.splits[0].runs[0].label, "Test")
        self.assertEqual(timer.splits[0].runs[0].runs, 2)
        self.assertEqual(timer.splits[0].runs[0].iterations_per_run, 2)
        self.assertEqual(timer.splits[0].runs[0].args, (5, 6))
        self.assertDictEqual(timer.splits[0].runs[0].kwargs, {"something": 5})

    def test_output_invalid_split(self):
        timer = Timer()
        self.assertRaisesRegex(RuntimeWarning, "The split index 'test' is not a valid index or label",
                               timer.output, "test")

    def test_output_simple_transformers_with_all_splits(self):
        timer = Timer()
        self.assertRaisesRegex(RuntimeWarning, "'split_index' must be specified when 'transformers' is",
                               timer.output, transformers={"test": len})

    def test_output_basic(self):
        out = StringIO()

        timer = Timer(output_stream=out, split=True, start=True)
        sleep(0.001)
        timer.log(label="Test")
        timer.output()

        lines = out.getvalue().split("\n")
        self.assertEqual(lines[0], "Split:")
        self.assertEqual(lines[1][17:], " - {:42} [runs=  1, iterations=  1] {:<20}".format("Test", ""))

    def test_output_transformers(self):
        out = StringIO()

        timer = Timer(output_stream=out, split=True, start=True)
        sleep(0.001)
        timer.log(5, 6, label="Test", array=[1, 2, 3, 4])
        timer.output(split_index=0, transformers={"array": sum})

        lines = out.getvalue().split("\n")
        self.assertEqual(lines[0], "Split:")
        self.assertEqual(lines[1][17:], " - {:42} [runs=  1, iterations=  1] {:<20}".format("Test(5, 6, array=10)", ""))

    def test_time_it_basic_callable(self):
        def basic(val):
            return val + 1

        timer = Timer()
        self.assertEqual(timer.time_it(basic, 7, runs=5), 8)
        self.assertEqual(len(timer.splits), 1)
        self.assertEqual(timer.splits[0].label, "basic")
        self.assertEqual(len(timer.splits[0].runs), 5)

    def test_time_it_basic_string(self):
        string = "len([i for i in range(100)])"
        timer = Timer()

        self.assertEqual(timer.time_it(string), 100)
        self.assertEqual(len(timer.splits), 1)
        self.assertEqual(timer.splits[0].label, string)

    def test_time_it_no_split(self):
        timer = Timer()
        self.assertRaisesRegex(RuntimeWarning, "No split exists.", timer.time_it, "1+1", split=False)


if __name__ == "__main__":
    unittest.main()
