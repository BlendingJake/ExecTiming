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


if __name__ == "__main__":
    unittest.main()
