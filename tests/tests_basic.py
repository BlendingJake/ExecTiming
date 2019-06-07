from random import randint
from exectiming.data_structures import Run
from exectiming.exectiming import StaticTimer, Timer
import unittest
from io import StringIO
from time import sleep


class TestStaticBasic(unittest.TestCase):
    def test_context(self):
        out = StringIO()

        with StaticTimer.context(output_stream=out):
            sleep(0.01)

        self.assertEqual(out.getvalue().rstrip()[11:],
                         "ms - Context                                    [runs=  1, iterations=  1]")

    def test_context_with_args(self):
        out = StringIO()

        with StaticTimer.context(7, 10, test="test_value", label="Sleep", output_stream=out):
            sleep(0.01)

        self.assertEqual(out.getvalue().rstrip()[11:],
                         "ms - Sleep(7, 10, test=test_value)              [runs=  1, iterations=  1]")

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

        StaticTimer.start()
        sleep(0.001)
        StaticTimer.elapsed(output_stream=out)

        self.assertEqual(out.getvalue()[13:], " - {:42} [runs=  1, iterations=  1] {:<20}\n".format("Elapsed", ""))

    def test_elapsed_basic_no_display(self):
        StaticTimer.start()
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
    def test_context(self):
        timer = Timer(split=True)

        with timer.context():
            sleep(0.01)

        self.assertEqual(timer.splits[-1].runs[-1].label, "Context")

    def test_context_with_args(self):
        timer = Timer(split=True)

        with timer.context(7, 10, test="test_value", label="Sleep"):
            sleep(0.01)

        self.assertEqual(timer.splits[-1].runs[-1].label, "Sleep")
        self.assertEqual(timer.splits[-1].runs[-1].args, (7, 10))
        self.assertEqual(timer.splits[-1].runs[-1].kwargs, {"test": "test_value"})

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

    def test_output_single_transformer(self):
        out = StringIO()

        timer = Timer(split=True, output_stream=out)
        timer.splits[-1].add_run(Run(time=1, label="Test", runs=1, iterations_per_run=1, args=([1, 3, 2], )))

        timer.output(transformers=sum, time_unit=timer.S)
        self.assertIn("1.00000 s  - Test(6)", out.getvalue())

    def test_output_multiple_transformers(self):
        out = StringIO()

        timer = Timer(split=True, output_stream=out)
        timer.splits[-1].add_run(Run(time=1, label="Test", runs=1, iterations_per_run=1, args=(4, [1, 3, 2]),
                                     kwargs={"test": [1, 4]}))

        timer.output(transformers={1: sum, "test": len}, time_unit=timer.S)
        self.assertIn("1.00000 s  - Test(4, 6, test=2)", out.getvalue())

    def test_output_multiple_split_transformers(self):
        out = StringIO()

        timer = Timer(split=True, output_stream=out, label="test1")
        timer.splits[-1].add_run(Run(time=1, label="Test1", runs=1, iterations_per_run=1, kwargs={"test": [1, 4]}))

        timer.split(label="test2")
        timer.splits[-1].add_run(Run(time=1, label="Test2", runs=1, iterations_per_run=1, args=(4, [1, 3, 2])))

        timer.output(transformers={"test1": {"test": sum}, "test2": {1: len}}, time_unit=timer.S)
        self.assertIn("1.00000 s  - Test1(test=5)", out.getvalue())
        self.assertIn("1.00000 s  - Test2(4, 3)", out.getvalue())

    def test_predict_invalid(self):
        timer = Timer()
        self.assertRaisesRegex(RuntimeWarning, "test is not a valid curve type", timer.predict, ("test", {}))

    def test_predict_linear(self):
        timer = Timer()
        result = timer.predict(
            ("Linear", {"b": 4, "x_0": 2, "x_test": 4}),
            2,
            test=3,
            time_unit=timer.S
        )

        self.assertEqual(result, 2*2 + 4*3 + 4)

    def test_sort_basic(self):
        timer = Timer(split=True)

        ys = [randint(0, 100) for _ in range(5)]
        xs = [randint(0, 100) for _ in range(5)]

        for i in range(5):
            timer.splits[-1].add_run(Run(time=ys[i], runs=1, iterations_per_run=1, label=str(i), args=(xs[i],),
                                         kwargs={"test": ys[i]}))

        timer.sort_runs()
        ys.sort()
        for i in range(5):
            self.assertEqual(timer.splits[-1].runs[i].time, ys[i])

        timer.sort_runs(keys=0)
        xs.sort()
        for i in range(5):
            self.assertEqual(timer.splits[-1].runs[i].args[0], xs[i])

        timer.sort_runs(keys="test")
        for i in range(5):
            self.assertEqual(timer.splits[-1].runs[i].kwargs["test"], ys[i])

    def test_sort_transformers(self):
        timer = Timer(split=True)

        timer.splits[-1].add_run(Run(time=4, runs=1, iterations_per_run=1, label="1", args=(7,),
                                     kwargs={"test": [1, 2]}))
        timer.splits[-1].add_run(Run(time=3, runs=1, iterations_per_run=1, label="2", args=(9,),
                                     kwargs={"test": [1]}))

        timer.sort_runs()
        self.assertEqual(timer.splits[-1].runs[0].label, "2")
        self.assertEqual(timer.splits[-1].runs[1].label, "1")

        timer.sort_runs(keys=0)
        self.assertEqual(timer.splits[-1].runs[0].label, "1")
        self.assertEqual(timer.splits[-1].runs[1].label, "2")

        timer.sort_runs(keys="test", transformers=len)
        self.assertEqual(timer.splits[-1].runs[0].label, "2")
        self.assertEqual(timer.splits[-1].runs[1].label, "1")

    def test_sort_complicated(self):
        timer = Timer(split=True, label="First")

        timer.splits[-1].add_run(Run(time=4, runs=1, iterations_per_run=1, label="a1", kwargs={"test": [1, 2]}))
        timer.splits[-1].add_run(Run(time=3, runs=1, iterations_per_run=1, label="a2", kwargs={"test": [8]}))

        timer.split(label="Second")
        timer.splits[-1].add_run(Run(time=43, runs=1, iterations_per_run=1, label="b1", kwargs={"test": [1, 2]}))
        timer.splits[-1].add_run(Run(time=23, runs=1, iterations_per_run=1, label="b2", kwargs={"test": [4]}))

        timer.sort_runs(split_index="First")
        self.assertEqual(timer.splits[0].runs[0].label, "a2")
        self.assertEqual(timer.splits[0].runs[1].label, "a1")
        self.assertEqual(timer.splits[1].runs[0].label, "b1")
        self.assertEqual(timer.splits[1].runs[1].label, "b2")

        timer.sort_runs(keys="test", transformers={"First": sum, "Second": len})
        self.assertEqual(timer.splits[0].runs[0].label, "a1")
        self.assertEqual(timer.splits[0].runs[1].label, "a2")
        self.assertEqual(timer.splits[1].runs[0].label, "b2")
        self.assertEqual(timer.splits[1].runs[1].label, "b1")

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
