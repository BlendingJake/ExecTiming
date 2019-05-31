from math import sqrt
from time import perf_counter
from typing import Union, Tuple, List, TextIO, Dict
from functools import wraps
import logging
from sys import stdout


class LoggingIO:
    """
    Provides a basic wrapper around logging.info to allow it to act like a file-like object to be used
    as an output stream in some of the functions below.
    """
    @staticmethod
    def write(message: str):
        """
        Write a message to logging.info. If the message ends with a newline, remove it, as logging.info adds that itself
        :param message: the string message to log
        """
        if message[-1] == "\n":
            logging.info(message[:-1])
        else:
            logging.info(message)


class BaseTimer:
    S, MS, US, NS = "s", "ms", "us", "ns"
    ROUNDING = 5
    _conversion = {S: 1, MS: 10**3, US: 10**6, NS: 10**9}
    _time = perf_counter

    @staticmethod
    def _call_callable_args(args: tuple, kwargs: dict) -> Tuple[list, dict]:
        """
        If any value in args or kwargs is callable, then replace it with the result of calling the value
        :param args: a list of positional arguments
        :param kwargs: a dict of keyword arguments
        :return: a new list and dict containing values replaced with the result of calling them if applicable
        """
        out_args = []
        for arg in args:
            if callable(arg):
                out_args.append(arg())
            else:
                out_args.append(arg)

        out_kwargs = {}
        for key, value in kwargs.items():
            if callable(value):
                out_kwargs[key] = value()
            else:
                out_kwargs[key] = value

        return out_args, out_kwargs

    @staticmethod
    def _convert_time(time: float, unit: str) -> float:
        """
        Convert and round a time from BaseTimer._time to the unit specified
        :param time: the amount of time, in fractional seconds if using perf_counter()
        :param unit: the unit to convert to, in BaseTimer.[S | MS | US | NS]
        :return: the converted and rounded time
        """
        return round(time * BaseTimer._conversion[unit], BaseTimer.ROUNDING)

    @staticmethod
    def _display_message(message: str, output_stream: TextIO=stdout):
        """
        Display the message to the proper output
        :param message: the message to display
        :param output_stream: the file-like object to write any output to
        """
        output_stream.write(message + "\n")

    @staticmethod
    def _format_output(label: str, runs: int, iterations: int, time: float, unit: str, args: list=(), kwargs: dict=(),
                       message: str="") -> str:
        """
        Build up a string message based on the input parameters
        :param label: the name of the function, part of the string being timed, or label of the call
        :param runs: the number of runs
        :param iterations: the number of iterations
        :param time: the measured time value
        :param unit: the unit the time value needs to be displayed in
        :param args: if it was a function, the positional arguments that were passed when it was called
        :param kwargs: if it was a function, the keyword arguments that were passed when it was called
        :param message: a message to display if there is one
        :return: a string: <time> <unit> - <name>[(args, kwargs)] [runs=<runs>, iterations=<iterations>] <message>
        """
        if args or kwargs:
            arguments = "".join((
                ", ".join(str(arg) for arg in args),
                ", " if args and kwargs else "",
                ", ".join("{}={}".format(key, value) for key, value in kwargs.items()),
            ))
        else:
            arguments = ""

        if arguments:
            name_part = "{:42.42}".format("{}({})".format(label, arguments[:25]))
        else:
            name_part = "{:42.42}".format(label)

        if message:
            message = "| {}".format(message)

        return "{:>10.5f} {:2} - {} [runs={:3}, iterations={:3}] {:<20.20}".format(BaseTimer._convert_time(time, unit),
                                                                                   unit, name_part, runs, iterations,
                                                                                   message)


class StaticTimer(BaseTimer):
    """
    StaticTimer is a class containing only static methods that provide three basic timing functions:
        1. A function decorator
            Any wrapped function will have its execution time measured anytime the function is called.
        2. A function for timing the execution of strings or anything that is callable
            A string or callable object is passed to the function which then measures its execution time.
        3. A quick way to get the elapsed time
            StaticTimer.start_elapsed() must be called first. After that, StaticTimer.elapsed() can be called to
            display or return the amount of time since the call to start_elapsed(). elapsed() accepts an argument
            'update_elapsed', which if set to True, will call start_elapsed() automatically.

    All of these timing functions have the keyword arguments 'output_unit' and 'display'.
        If 'display' is true, then the measured time is written to a file output stream. By default, this is 'stdout',
            but it can configured to any file-like object by setting 'output_stream' in any of the function calls

        'output_unit' specifies which time unit to use when returning or displaying the measured time. Possible options
            are StaticTimer.[S, MS, US, NS], which correspond to seconds, milliseconds, microseconds, and nanoseconds,
            respectively.
    """
    _elapsed_time = None

    @staticmethod
    def decorate(runs=1, iterations_per_run=1, average_runs=True, display=True, output_unit=BaseTimer.MS,
                 output_stream: TextIO=stdout, call_callable_args=False, log_arguments=False) -> callable:
        """
        A decorator that will time a function and then immediately output the timing results either to logging.info
        or print
        :param runs: the number of runs to measure the time for
        :param iterations_per_run: how many iterations to do in each of those runs
        :param average_runs: whether to average the runs together or list them individually
        :param display: whether to display the measured time or to return it as ('block' return value, time(s))
        :param output_unit: the time scale to output the values in
        :param output_stream: the file-like object to write any output to if the message is being displayed
        :param call_callable_args: whether to call any arguments and pass those values instead
        :param log_arguments: whether to keep track of the arguments and display them in the output
        :return: a function wrapper
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
                """
                :return: If 'display', just the return value of calling/executing 'block' is returned. Otherwise, a
                            tuple of  the return value and the measured time(s) is returned. If 'average', then a
                            single time value is returned, otherwise, a list of time values, one for each run, is
                            returned. Any returned times will be in 'output_unit'
                """
                run_totals = []
                value = None
                new_args, new_kwargs = args, kwargs
                arguments = []

                # MEASURE
                for _ in range(runs):
                    # call any callable args and replace them with the result of the call
                    if call_callable_args:
                        new_args, new_kwargs = StaticTimer._call_callable_args(args, kwargs)

                    if log_arguments:
                        arguments.append((new_args, new_kwargs))

                    st = StaticTimer._time()
                    for _ in range(iterations_per_run):
                        value = func(*new_args, **new_kwargs)

                    run_totals.append(StaticTimer._time() - st)

                # DETERMINE TIME, DISPLAY OR RETURN
                if average_runs:
                    average = sum(run_totals) / len(run_totals)

                    if display:
                        if log_arguments:
                            string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                                output_unit, args=arguments[0][0],
                                                                kwargs=arguments[0][1])
                        else:
                            string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                                output_unit)

                        StaticTimer._display_message(string, output_stream=output_stream)
                        return value  # any
                    else:
                        return value, StaticTimer._convert_time(average, output_unit)  # Tuple[any, float]
                else:
                    if display:
                        for i in range(len(run_totals)):
                            if log_arguments:
                                string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                    output_unit, message="Run {}".format(i+1),
                                                                    args=arguments[i][0], kwargs=arguments[i][1])
                            else:
                                string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                    output_unit, message="Run {}".format(i+1))

                            StaticTimer._display_message(string, output_stream=output_stream)

                        return value  # any
                    else:
                        # Tuple[any, List[float]]
                        return value, [StaticTimer._convert_time(time, output_unit) for time in run_totals]

            return inner_wrapper
        return wrapper

    @staticmethod
    def elapsed(display=True, output_unit=BaseTimer.MS, output_stream: TextIO=stdout, label="Elapsed",
                update_elapsed=False) -> Union[None, float]:
        """
        Determine and display how much time has elapsed since the last call to 'start_elapsed'.
        :param display: whether to display the measured time or to return it
        :param output_unit: the unit to displayed the measured time in
        :param output_stream: the file-like object to write any output to if the message is being displayed
        :param label: the label to use when displaying the measured time
        :param update_elapsed: call 'start_elapsed' after displaying the measured time. Removes the need to call
                'start_elapsed' again and so 'elapsed' can just keep being called successively.
        :return: If 'display', then None is returned. Otherwise, the measured elapsed time is returned as a float in
                'output_unit'
        """
        if StaticTimer._elapsed_time is None:
            raise RuntimeWarning("StaticTimer.start_elapsed() must be called before StaticTimer.elapsed()")
        else:
            dif = StaticTimer._time() - StaticTimer._elapsed_time

            if update_elapsed:
                StaticTimer.start_elapsed()

            if display:
                string = StaticTimer._format_output(label, 1, 1, dif, output_unit)
                StaticTimer._display_message(string, output_stream=output_stream)

                return None
            else:
                return StaticTimer._convert_time(dif, output_unit)

    @staticmethod
    def start_elapsed():
        """
        Log the current time for use with 'elapsed'. Must be called before 'elapsed' can be called.
        """
        StaticTimer._elapsed_time = StaticTimer._time()

    @staticmethod
    def time_it(block: Union[str, callable], *args, runs=1, iterations_per_run=1, average_runs=True, display=True,
                output_unit=BaseTimer.MS, output_stream: TextIO=stdout, call_callable_args=False, log_arguments=False,
                **kwargs) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
        """
        Time a function or evaluate a string.
        :param block: either a callable or a string
        :param args: any positional arguments to pass into 'block' if it is callable
        :param runs: the number of runs
        :param iterations_per_run: the number of iterations for each run
        :param average_runs: whether to average the runs together or to display them separately
        :param display: whether to display the measured time or to return it as ('block' return value, time(s))
        :param output_unit: the unit to display the measured time in
        :param output_stream: the file-like object to write any output to if the message is being displayed
        :param call_callable_args: whether to replace any 'args' or 'kwargs' with the result of the function call if
                    the argument is callable. Only valid if 'block' is callable.
        :param log_arguments: whether to keep track of the arguments passed into 'block' so they can be displayed.
                    Only valid if 'block' is callable
        :param kwargs: any keyword arguments to pass into 'block' if it is callable
        :return: If 'display', just the return value of calling/executing 'block' is returned. Otherwise, a tuple of
                    the return value and the measured time(s) is returned. If 'average', then a single time value is
                    returned, otherwise, a list of time values, one for each run, is returned. Any returned times will
                    be in 'output_unit'
        """
        run_totals = []
        arguments = []
        value = None
        new_args, new_kwargs = args, kwargs

        # MEASURE
        for _ in range(runs):
            if callable(block) and call_callable_args:
                new_args, new_kwargs = StaticTimer._call_callable_args(args, kwargs)

            st = StaticTimer._time()
            for _ in range(iterations_per_run):
                if callable(block):
                    if log_arguments:
                        arguments.append((new_args, new_kwargs))

                    value = block(*new_args, **new_kwargs)
                else:
                    value = eval(block)

            run_totals.append(StaticTimer._time() - st)

        # DETERMINE TIME, DISPLAY OR RETURN
        if average_runs:
            average = sum(run_totals) / len(run_totals)

            if display:
                if callable(block) and log_arguments:
                    string = StaticTimer._format_output(block.__name__, runs, iterations_per_run, average, output_unit,
                                                        args=arguments[0][0], kwargs=arguments[0][1])
                elif callable(block):
                    string = StaticTimer._format_output(block.__name__, runs, iterations_per_run, average, output_unit)
                else:
                    string = StaticTimer._format_output(block, runs, iterations_per_run, average, output_unit)

                StaticTimer._display_message(string, output_stream=output_stream)
                return value  # any
            else:
                return value, StaticTimer._convert_time(average, output_unit)  # Tuple[any, float]
        else:
            if display:
                for i in range(runs):
                    if callable(block) and log_arguments:
                        string = StaticTimer._format_output(block.__name__, 1, iterations_per_run, run_totals[i],
                                                            output_unit, args=arguments[i][0], kwargs=arguments[i][1],
                                                            message="Run {}".format(i+1))
                    elif callable(block):
                        string = StaticTimer._format_output(block.__name__, 1, iterations_per_run, run_totals[i],
                                                            output_unit, message="Run {}".format(i+1))
                    else:
                        string = StaticTimer._format_output(block, runs, iterations_per_run, run_totals[i], output_unit,
                                                            message="Run {}".format(i+1))

                    StaticTimer._display_message(string, output_stream=output_stream)

                return value  # any
            else:
                # Tuple[any, List[float]]
                return value, [StaticTimer._convert_time(time, output_unit) for time in run_totals]


class BestFitBase:
    """
    An abstract class to be used as a template for best fit curves. The process is to first calculate the curve using
    calculated points and then check how accurate the curve is.
    """
    @staticmethod
    def calculate_curve(points: List[Tuple[Tuple[Tuple[int], Dict[str, int]]], float]) -> dict:
        """
        Take a list of tuples, each containing the arguments and the time value, and determines the parameters for this
        type of curve. All arguments must be integers.
        :param points: each entry is ((tuple of positional arguments, dict of keyword arguments), measured time)
        :return: a dict of the parameters of the curve
        """
        pass

    @staticmethod
    def calculate_point(arguments: Tuple[Tuple[Tuple[int], Dict[str, int]]], parameters: dict) -> float:
        """
        Take a tuple of arguments and calculate what the time should be for those arguments with the given parameters
        :param arguments: positional and keyword arguments. All values must be ints.
        :param parameters: the parameters of the calculated curve
        :return: the time value for the given arguments and parameters
        """
        pass


class BestFitExponential(BestFitBase):
    @staticmethod
    def calculate_curve(points: List[Tuple[Tuple[Tuple[int], Dict[str, int]]], float]) -> dict:
        """

        """
        pass

    @staticmethod
    def calculate_point(arguments: Tuple[Tuple[Tuple[int], Dict[str, int]]], parameters: dict) -> float:
        """

        """
        pass


class BestFitLine(BestFitBase):
    @staticmethod
    def calculate_curve(points: List[Tuple[Tuple[Tuple[int], Dict[str, int]]], float]) -> dict:
        """

        """
        pass

    @staticmethod
    def calculate_point(arguments: Tuple[Tuple[Tuple[int], Dict[str, int]]], parameters: dict) -> float:
        """

        """
        pass


class BestFitLogarithmic(BestFitBase):
    @staticmethod
    def calculate_curve(points: List[Tuple[Tuple[Tuple[int], Dict[str, int]]], float]) -> dict:
        """

        """
        pass

    @staticmethod
    def calculate_point(arguments: Tuple[Tuple[Tuple[int], Dict[str, int]]], parameters: dict) -> float:
        """

        """
        pass


class BestFitPolynomial(BestFitBase):
    @staticmethod
    def calculate_curve(points: List[Tuple[Tuple[Tuple[int], Dict[str, int]]], float]) -> dict:
        """

        """
        pass

    @staticmethod
    def calculate_point(arguments: Tuple[Tuple[Tuple[int], Dict[str, int]]], parameters: dict) -> float:
        """

        """
        pass


class Run:
    def __init__(self, label: str, time: float, runs: int, iterations_per_run: int, args: list=(), kwargs: dict=()):
        self.label: str = label
        self.time: float = time
        self.runs = runs
        self.iterations_per_run = iterations_per_run
        self.args: Union[None, list] = args if args else None
        self.kwargs: Union[None, dict] = kwargs if kwargs else None


class Split:
    best_fit_curves = {}

    def __init__(self, label: str="Split"):
        self.runs: List[Run] = []
        self.label = label

    def add_run(self, run: Run):
        self.runs.append(run)

    def average(self) -> float:
        if self.runs:
            return sum(i.time for i in self.runs) / len(self.runs)
        else:
            return 0

    def determine_best_fit(self, arg_transformers: Tuple[callable]=(), kwarg_transformers: Dict[str, callable]=()
                           ) -> Union[None, Tuple[str, dict]]:
        """
        Determine the best fit curve for the runs contained in this split.
        :return: A tuple of a string name for the best fit curve and a dict of the parameters for that curve
        """
        points = []
        for run in self.runs:
            if run.args is None and run.kwargs is None:
                raise RuntimeWarning("Arguments must have been logged to determine a best fit curve")

            # TRANSFORM ARGUMENTS
            new_args, new_kwargs = run.args, run.kwargs
            if arg_transformers:
                if len(arg_transformers) != len(run.args):
                    raise RuntimeWarning("There are {} arg transformers, but {} args".format(len(arg_transformers),
                                                                                             len(run.args)))

                new_args = []
                for i in range(len(run.args)):
                    new_args.append(arg_transformers[i](run.args[i]))

            if kwarg_transformers:
                if len(kwarg_transformers) != len(run.kwargs):
                    raise RuntimeWarning("There are {} kwarg transformers, but {} kwargs".format(
                        len(kwarg_transformers), len(run.kwargs)))

                new_kwargs = {}
                for key, value in run.kwargs.items():
                    if key in kwarg_transformers:
                        new_kwargs[key] = kwarg_transformers[key](value)
                    else:
                        raise RuntimeWarning("The key {} is not in kwarg transformers".format(key))

            points.append(((new_args, new_kwargs), run.time))

        best: Tuple[float, str, dict] = None  # tuple of distance, name, and parameters
        for bfc_name, bfc in self.best_fit_curves.items():
            params = bfc.calculate_curve(points)

            # DISTANCE
            distance = 0
            for point in points:
                distance += abs(point[1] - bfc.calculate_point(point[0]))

            if best is None or distance < best[0]:
                best = (distance, bfc_name, params)

        if best is not None:
            return best[1], best[2]
        else:
            return None

    def standard_deviation(self) -> float:
        """
        Calculate the standard deviation of the runs contained within this split where SD is:
        sqrt(sum (x - x_bar)**2 / n)
        :return: the standard deviation
        """
        if self.runs:
            avg = self.average()
            return sqrt(sum((run.time - avg) ** 2 for run in self.runs) / len(self.runs))
        else:
            return 0

    def variance(self) -> float:
        if self.runs:
            return self.standard_deviation() ** 2
        else:
            return 0


class Timer(BaseTimer):
    def __init__(self, output_stream: TextIO=stdout, initial_label: str="Split", indent: str="    "):
        """
        Create a new timer.
        :param output_stream: the file-like object to write any output to. Must have a .write(str) method.
        :param initial_label: the label to use for the first split which is created automatically
        :param indent: the amount to indent certain lines when outputting data
        """
        self.output_stream: TextIO = output_stream
        self.splits: List[Split] = [Split(label=initial_label)]
        self.indent = indent

    def __str__(self):
        return self._str()

    def _str(self, output_unit=BaseTimer.MS) -> str:
        """
        Generate a string containing all splits and all logged runs in those splits.
        :param output_unit: the time scale unit to output times in
        :return: a formatted string containing split and run information
        """
        string = []
        for split in self.splits:
            if not split.runs:  # skip splits with no logged times
                continue

            string.append("{}:\n".format(split.label))

            for run in split.runs:
                string.append("{}{}\n".format(
                    self.indent,
                    self._format_output(label=run.label, runs=run.runs, iterations=run.iterations_per_run,
                                        time=run.time, unit=output_unit, args=run.args, kwargs=run.kwargs)
                ))

            string.append("\n")

        return "".join(string)

    def decorate(self, runs=1, iterations_per_run=1, call_callable_args=False, log_arguments=False, split=True,
                 split_label="Split") -> callable:
        """
        A decorator that will time a function and then immediately output the timing results either to logging.info
        or print
        :param runs: the number of runs to measure the time for
        :param iterations_per_run: how many iterations to do in each of those runs
        :param call_callable_args: whether to call any arguments and pass those values instead
        :param log_arguments: whether to keep track of the arguments and display them in the output
        :param split: automatically make a new split after timing the function
        :param split_label: what the name of the new split will be
        :return: a function wrapper
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
                value = None
                new_args, new_kwargs = args, kwargs

                # MEASURE
                for _ in range(runs):
                    # call any callable args and replace them with the result of the call
                    if call_callable_args:
                        new_args, new_kwargs = self._call_callable_args(args, kwargs)

                    st = StaticTimer._time()
                    for _ in range(iterations_per_run):
                        value = func(*new_args, **new_kwargs)

                    run = Run(label=func.__name__, time=self._time() - st, runs=1,
                              iterations_per_run=iterations_per_run)

                    if log_arguments:
                        run.args = new_args
                        run.kwargs = new_kwargs

                    self.splits[-1].add_run(run)

                if split:
                    self.split(label=split_label)

                return value

            return inner_wrapper
        return wrapper

    def determine_best_fit(self, split_index: int=-1, *arg_transformers, **kwarg_transformers
                           ) -> Union[None, Tuple[str, dict]]:
        """
        Determine the best fit curve. By default, the best fit curve for the current split is returned.
        :param split_index: The index of the split to determine the best fit curve for
        :param arg_transformers: functions that take an argument and return an integer, as integers are needed for
                determining the best fit curve
        :param kwarg_transformers: functions that take a keyword argument and return an integer, as integers are needed
                for determining the best fit curve
        :return: either None if there is no best fit curve, otherwise, the name of the curve, and any parameters for it
        """
        if split_index == -1 or 0 <= split_index < len(self.splits):
            return self.splits[split_index].determine_best_fit(arg_transformers, kwarg_transformers)
        else:
            raise RuntimeWarning("The split index {} is out of bounds".format(split_index))

    def output(self, output_unit=BaseTimer.MS):
        """
        Output all splits and all logged runs
        :param output_unit: the time scale unit to output times in
        """
        self.output_stream.write(self._str(output_unit=output_unit))

    def statistics(self, output_unit=BaseTimer.MS):
        """
        Output statistics for each split. The statistics are the average, standard deviation, and variance
        :param output_unit: the time scale unit to output times in
        """
        for split in self.splits:
            if not split.runs:  # skip splits with no logged times
                continue

            self.output_stream.write("{}:\n".format(split.label))

            # STATISTICS
            self.output_stream.write("{}Average: {} {}\n".format(
                self.indent,
                self._convert_time(split.average(), output_unit),
                output_unit
            ))
            self.output_stream.write("{}Standard Deviation: {} {}\n".format(
                self.indent,
                self._convert_time(split.standard_deviation(), output_unit),
                output_unit
            ))
            self.output_stream.write("{}Variance: {} {}\n".format(
                self.indent,
                self._convert_time(split.variance(), output_unit),
                output_unit
            ))

            self.output_stream.write("\n")

    def split(self, label: str="Split"):
        """
        Create a new split that will be used for subsequent timings
        :param label: the label for the new split
        """
        self.splits.append(Split(label=label))

    def time_it(self, block: Union[str, callable], *args, runs=1, iterations_per_run=1, call_callable_args=False,
                log_arguments=False, split=True, split_label="Split", **kwargs
                ) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
        """
        Time a function or evaluate a string.
        :param block: either a callable or a string
        :param args: any positional arguments to pass into 'block' if it is callable
        :param runs: the number of runs
        :param iterations_per_run: the number of iterations for each run
        :param call_callable_args: whether to replace any 'args' or 'kwargs' with the result of the function call if
                    the argument is callable. Only valid if 'block' is callable.
        :param log_arguments: whether to keep track of the arguments passed into 'block' so they can be displayed.
                    Only valid if 'block' is callable
        :param split: automatically make a new split after timing the function
        :param split_label: what the name of the new split will be
        :param kwargs: any keyword arguments to pass into 'block' if it is callable
        :return: If 'display', just the return value of calling/executing 'block' is returned. Otherwise, a tuple of
                    the return value and the measured time(s) is returned. If 'average', then a single time value is
                    returned, otherwise, a list of time values, one for each run, is returned. Any returned times will
                    be in 'output_unit'
        """
        value = None
        new_args, new_kwargs = args, kwargs

        # MEASURE
        for _ in range(runs):
            if callable(block) and call_callable_args:
                new_args, new_kwargs = self._call_callable_args(args, kwargs)

            st = StaticTimer._time()
            for _ in range(iterations_per_run):
                if callable(block):
                    value = block(*args, **kwargs)
                else:
                    value = eval(block)

            run = Run(label=block.__name__ if callable(block) else block, time=self._time() - st,
                      runs=1, iterations_per_run=iterations_per_run)

            if log_arguments:
                run.args = new_args
                run.kwargs = new_kwargs

            self.splits[-1].add_run(run)

        if split:
            self.split(label=split_label)

        return value
