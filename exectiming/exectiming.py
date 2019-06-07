# ExecTiming - A Python packaged for measuring the execution time of code
# Copyright (C) <2019>  <Jacob Morris>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from time import perf_counter
from typing import Union, Tuple, List, TextIO, Dict, Set
from functools import wraps
from sys import stdout
from .data_structures import Run, Split
from contextlib import contextmanager

try:
    import matplotlib.pyplot as plt
    MISSING_MAT_PLOT = False
except ImportError:
    MISSING_MAT_PLOT = True


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
    def _convert_time(time: float, unit: str, round_it=True) -> float:
        """
        Convert and round a time from BaseTimer._time to the unit specified
        :param time: the amount of time, in fractional seconds if using perf_counter()
        :param unit: the unit to convert to, in BaseTimer.[S | MS | US | NS]
        :param round_it: whether to round or not
        :return: the converted and rounded time
        """
        if round_it:
            return round(time * BaseTimer._conversion[unit], BaseTimer.ROUNDING)
        else:
            return time * BaseTimer._conversion[unit]

    @staticmethod
    def _display_message(message: str, output_stream: TextIO=stdout):
        """
        Display the message to the proper output
        :param message: the message to display
        :param output_stream: the file-like object to write any output to
        """
        output_stream.write(message + "\n")

    @staticmethod
    def _format_output(label: str, runs: int, iterations_per_run: int, time: float, time_unit: str,
                       args: Union[None, list]=(), kwargs: Union[None, dict]=(), message: str="") -> str:
        """
        Build up a string message based on the input parameters
        :param label: the name of the function, part of the string being timed, or label of the call
        :param runs: the number of runs
        :param iterations_per_run: the number of iterations
        :param time: the measured time value
        :param time_unit: the unit the time value needs to be displayed in
        :param args: if it was a function, the positional arguments that were passed when it was called
        :param kwargs: if it was a function, the keyword arguments that were passed when it was called
        :param message: a message to display if there is one
        :return: a string: <time> <unit> - <name>[(args, kwargs)] [runs=<runs>, iterations=<iterations>] <message>
        """
        if args or kwargs:
            arguments = "".join((
                ", ".join(str(arg) for arg in args),
                ", " if args and kwargs else "",
                ", ".join("{}={}".format(key, value) for key, value in kwargs.items()) if kwargs else "",
            ))
        else:
            arguments = ""

        if arguments:
            name_part = "{:42.42}".format("{}({})".format(label, arguments[:25]))
        else:
            name_part = "{:42.42}".format(label)

        if message:
            message = "| {}".format(message)

        return "{:>10.5f} {:2} - {} [runs={:3}, iterations={:3}] {:<20.20}".format(
            BaseTimer._convert_time(time, time_unit),
            time_unit,
            name_part,
            runs,
            iterations_per_run,
            message
        )


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

    All of these timing functions have the keyword arguments 'time_unit' and 'display'.
        If 'display' is true, then the measured time is written to a file output stream. By default, this is 'stdout',
            but it can configured to any file-like object by setting 'output_stream' in any of the function calls

        'time_unit' specifies which time unit to use when returning or displaying the measured time. Possible options
            are StaticTimer.[S, MS, US, NS], which correspond to seconds, milliseconds, microseconds, and nanoseconds,
            respectively.
    """
    _elapsed_time = None

    @staticmethod
    @contextmanager
    def context(*args, runs=1, iterations_per_run=1, label="Context", time_unit=BaseTimer.MS,
                output_stream: TextIO=stdout, **kwargs):
        """
        Provides a context manager that can be used with a `with` statement as `with StaticTimer.context():`. The only
        option is to output the measured time.
        :param args: any arguments to log with the run
        :param runs: the number of runs that were performed. THIS IS ONLY FOR LOGGING PURPOSES.
        :param iterations_per_run: the number of iterations that were performed. THIS IS ONLY FOR LOGGING PURPOSES.
        :param label: the label for the run
        :param time_unit: the time unit to use for the output
        :param output_stream: the file-like object to write the output to
        :param kwargs: any keyword arguments to log with the run
        """
        tm = StaticTimer._time()
        yield

        dif = StaticTimer._time() - tm
        StaticTimer._display_message(
            StaticTimer._format_output(label=label, time=dif, runs=runs, iterations_per_run=iterations_per_run,
                                       args=list(args), kwargs=kwargs, time_unit=time_unit),
            output_stream=output_stream
        )

    @staticmethod
    def decorate(runs=1, iterations_per_run=1, average_runs=True, display=True, time_unit=BaseTimer.MS,
                 output_stream: TextIO=stdout, call_callable_args=False, log_arguments=False) -> callable:
        """
        A decorator that will time a function and then either output the results to `output_stream` if `display`.
        Otherwise, the measured time(s) will be returned along with the return value of the wrapped function
        :param runs: how many times the execution time of the wrapped function will be measured
        :param iterations_per_run: how many times the wrapped function will be called for each run. The time for the
                    run will the sum of the times of iterations
        :param average_runs: whether to average the measured times from all the runs together or not
        :param display: whether to display the measured time or to return it as
                    `Tuple[function return value: any, times: Union[float, List[float]]]`
        :param time_unit: the time scale to output the values in
        :param output_stream: the file-like object to write any output to if `display`
        :param call_callable_args: If True, then any `callable` arguments/parameters that are passed into the wrapped
                    function will be replaced with their return value. So `wrapped(callable)` will actually be
                    `wrapped(callable())`
        :param log_arguments: whether to keep track of the arguments so they can be displayed if `display`
        :return: a function wrapper
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
                """
                :return: If 'display', just the return value of calling/executing 'block' is returned. Otherwise, a
                            tuple of  the return value and the measured time(s) is returned. If 'average', then a
                            single time value is returned, otherwise, a list of time values, one for each run, is
                            returned. Any returned times will be in 'time_unit'
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
                                                                time_unit, args=arguments[0][0],
                                                                kwargs=arguments[0][1])
                        else:
                            string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                                time_unit)

                        StaticTimer._display_message(string, output_stream=output_stream)
                        return value  # any
                    else:
                        return value, StaticTimer._convert_time(average, time_unit)  # Tuple[any, float]
                else:
                    if display:
                        for i in range(len(run_totals)):
                            if log_arguments:
                                string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                    time_unit, message="Run {}".format(i+1),
                                                                    args=arguments[i][0], kwargs=arguments[i][1])
                            else:
                                string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                    time_unit, message="Run {}".format(i+1))

                            StaticTimer._display_message(string, output_stream=output_stream)

                        return value  # any
                    else:
                        # Tuple[any, List[float]]
                        return value, [StaticTimer._convert_time(time, time_unit) for time in run_totals]

            return inner_wrapper
        return wrapper

    @staticmethod
    def elapsed(display=True, time_unit=BaseTimer.MS, output_stream: TextIO=stdout, label="Elapsed",
                reset=False) -> Union[None, float]:
        """
        Determine how much time has elapsed since the last call to `.start()` or `.elasped(reset=True). `.start()` must
        be called before `.elasped()` can be. The elapsed time will either be displayed if `display` or otherwise will
        be returned as a float.
        :param display: whether to display the measured time or to return it
        :param time_unit: the unit to display the measured time in
        :param output_stream: the file-like object to write any output to if `display`
        :param label: the label to use if displaying the measured time
        :param reset: call `.start()` after calculating the elapsed time. Removes the need to call `.start()` again and
                    so `.elapsed()` can be called successively.
        :return: If `display`, then None is returned. Otherwise, the elapsed time is returned as a float in
                `time_unit`
        """
        if StaticTimer._elapsed_time is None:
            raise RuntimeWarning("StaticTimer.start() must be called before StaticTimer.elapsed()")
        else:
            dif = StaticTimer._time() - StaticTimer._elapsed_time

            if reset:
                StaticTimer.start()

            if display:
                string = StaticTimer._format_output(label, 1, 1, dif, time_unit)
                StaticTimer._display_message(string, output_stream=output_stream)

                return None
            else:
                return StaticTimer._convert_time(dif, time_unit)

    @staticmethod
    def start():
        """
        Log the current time so `.elapsed()` can be called. Must be called before `.elapsed()` can be called for the
        first time.
        """
        StaticTimer._elapsed_time = StaticTimer._time()

    @staticmethod
    def time_it(block: Union[str, callable], *args, runs=1, iterations_per_run=1, average_runs=True, display=True,
                time_unit=BaseTimer.MS, output_stream: TextIO=stdout, call_callable_args=False, log_arguments=False,
                globals: dict=(), locals: dict=(), **kwargs) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
        """
        Measure the execution time of a function are string. Positional and keyword arguments can be passed through to
        `block` if it is a function. `eval` is used if `block` is a string and so a namespace can be passed to it by
        setting `globals` and/or `locals`.
        :param block: either a callable or a string
        :param args: any positional arguments to pass into `block` if it is callable
        :param runs: the number of times to measure the execution time
        :param iterations_per_run: the number of times to execute the function for each run
        :param average_runs: whether to average the runs together or not
        :param display: whether to display the measured time or to return it
        :param time_unit: the unit to display the measured time in if `display`
        :param output_stream: the file-like object to write any output to if `display`
        :param call_callable_args: If True, then any `callable` values in `args` and `kwargs` will be
                    replaced with their return value. So `time_it(func, callable1, something=callable2` will become
                    `func(callable1(), something=callable2())`. Only useful if `block` is callable
        :param log_arguments: whether to keep track of the arguments so they can be displayed if `display`.
                    Only valid if `block` is callable
        :param globals: a global namespace to pass to `eval` if `block` is a string
        :param locals: a local namespace to pass to `eval` if `block` is a string
        :param kwargs: any keyword arguments to pass into `block` if it is callable
        :return: If `display`, then just the return value of calling/evaluating `block` is returned. Otherwise, a
                    tuple of the return value and the measured time(s) is returned. If `average`, then a single time
                    value is returned. Otherwise, a list of time values, one for each run, is returned.
                    Any returned times will be in `time_unit`
        """
        run_totals = []
        arguments = []
        value = None
        new_args, new_kwargs = args, kwargs
        globals = globals if globals else {}
        locals = locals if locals else {}

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
                    value = eval(block, globals, locals)

            run_totals.append(StaticTimer._time() - st)

        # DETERMINE TIME, DISPLAY OR RETURN
        if average_runs:
            average = sum(run_totals) / len(run_totals)

            if display:
                if callable(block) and log_arguments:
                    string = StaticTimer._format_output(block.__name__, runs, iterations_per_run, average, time_unit,
                                                        args=arguments[0][0], kwargs=arguments[0][1])
                elif callable(block):
                    string = StaticTimer._format_output(block.__name__, runs, iterations_per_run, average, time_unit)
                else:
                    string = StaticTimer._format_output(block, runs, iterations_per_run, average, time_unit)

                StaticTimer._display_message(string, output_stream=output_stream)
                return value  # any
            else:
                return value, StaticTimer._convert_time(average, time_unit)  # Tuple[any, float]
        else:
            if display:
                for i in range(runs):
                    if callable(block) and log_arguments:
                        string = StaticTimer._format_output(block.__name__, 1, iterations_per_run, run_totals[i],
                                                            time_unit, args=arguments[i][0], kwargs=arguments[i][1],
                                                            message="Run {}".format(i+1))
                    elif callable(block):
                        string = StaticTimer._format_output(block.__name__, 1, iterations_per_run, run_totals[i],
                                                            time_unit, message="Run {}".format(i+1))
                    else:
                        string = StaticTimer._format_output(block, runs, iterations_per_run, run_totals[i], time_unit,
                                                            message="Run {}".format(i+1))

                    StaticTimer._display_message(string, output_stream=output_stream)

                return value  # any
            else:
                # Tuple[any, List[float]]
                return value, [StaticTimer._convert_time(time, time_unit) for time in run_totals]


class Timer(BaseTimer):
    """
    Timer provides many of the same features as StaticTimer, but stores the measured times instead of outputting them
    immediately. Storing the data allows features like determining the best fit curve for a split where arguments were
    logged. Additionally, statistics can be output for any of the splits recorded.

    Data is stored in Runs which are collected together into Splits.
    """

    def __init__(self, output_stream: TextIO=stdout, split: bool=False, label: str= "Split", indent: str= "    ",
                 start: bool=False):
        """
        Create a new timer.
        :param output_stream: the file-like object to write any output to. Must have a `.write(str)` method.
        :param split: automatically create a split. Needed if the first calls will be to `.start()` and `.log()` as
                    `.time_it()` and `.decorate()` create new splits for themselves by default
        :param label: the label for the new split if `split`
        :param indent: the amount to indent lines when outputting data
        :param start: go ahead and call `.start()` to allow `.log()` to be called immediately. Only use if a minimal
                    amount of time will pass between timer creation the first call to `.log()`
        """
        self.output_stream: TextIO = output_stream
        self.splits: List[Split] = []
        self.indent = indent
        self.log_base_point = None

        if split:
            self.splits.append(Split(label=label))

        if start:
            self.start()

    def __str__(self):
        return self._str()

    def _adjust_split_index(self, split_index: Union[int, str]) -> Union[None, int]:
        """
        Take a split index or label and verify it is within bounds or convert it to an index, respectively.
        :param split_index: the label or index of the split to adjust and verify
        :return: None if out of bounds or it doesn't exist, otherwise, an integer
        """
        adjusted_index = None
        if isinstance(split_index, int) and 0 <= split_index < len(self.splits):
            adjusted_index = split_index
        else:
            for i in range(len(self.splits)):
                if self.splits[i].label == split_index:
                    adjusted_index = i
                    break

        return adjusted_index

    def _str(self, split_index: Union[int, str]=all, time_unit=BaseTimer.MS,
             transformers: Dict[Union[str, int], Dict[Union[str, int], callable]]=()) -> str:
        """
        Generate a string containing all splits or a specific one designated by index or label. List all runs for each
        split.
        :param split_index: the split index or label to output. Defaults to all
        :param time_unit: the time scale unit to output times in
        :param transformers: a dict mapping a split index or label to a dict mapping a keyword argument name or
                    positional argument index to a function. That function will be called and passed the argument and
                    the return value will be used to generate the output
        :return: a formatted string containing split and run information
        """
        string = []
        for i in range(len(self.splits)):
            split = self.splits[i]
            if split_index != all and i != split_index and split.label != split_index:
                continue

            if not split.runs:  # skip splits with no logged times
                continue

            string.append("{}:\n".format(split.label))

            for run in split.runs:
                if transformers and (i in transformers or split.label in transformers):
                    if i in transformers:
                        split_transformers = transformers[i]
                    else:
                        split_transformers = transformers[split.label]

                    args, kwargs = run.args[:], dict(run.kwargs)

                    for j in range(len(args)):
                        if j in split_transformers:
                            args[j] = split_transformers[j](args[j])

                    for key in kwargs:
                        if key in split_transformers:
                            kwargs[key] = split_transformers[key](kwargs[key])
                else:
                    args, kwargs = run.args, run.kwargs

                string.append("{}{}\n".format(
                    self.indent,
                    self._format_output(label=run.label, runs=run.runs, iterations_per_run=run.iterations_per_run,
                                        time=run.time, time_unit=time_unit, args=args, kwargs=kwargs)
                ))

            string.append("\n")

        return "".join(string)

    def best_fit_curve(self, curve_type: str=any, exclude_args: Set[int]=(), exclude_kwargs: set=(),
                       split_index: Union[int, str]=-1, transformers: Dict[Union[str, int], callable]=()
                       ) -> Union[None, Tuple[str, dict]]:
        """
        Determine the best fit curve for a split using logged arguments as the independent variable and the measured
        time as the dependent variable. By default, the most recent split is used. All non-excluded arguments must have
        integer values to allow curve calculation. If the values are not integers, then they must be transformed.
        :param curve_type: specify a specific curve type to determine the parameters for
        :param exclude_args: the indices of the positional arguments to exclude when performing curve calculation
        :param exclude_kwargs: the keys of the keyword arguments to exclude when performing curve calculation
        :param split_index: The index or name of the split to determine the best fit curve for
        :param transformers: functions that take an argument and return an integer, as integers are needed for
                determining the best fit curve. Positional arguments are denoted with integer keys denoting the position
                and keyword arguments are denoted by the key itself. Example, `func(list)` would need
                `transformers={0: len}` where `len` can be replaced with any function that returns an integer
        :return: None if there is no best fit curve. Otherwise, the name of the curve and any parameters
        """
        adjusted_index = -1 if split_index == -1 else self._adjust_split_index(split_index)
        if adjusted_index is not None:
            return self.splits[adjusted_index].determine_best_fit(curve_type=curve_type, exclude_args=exclude_args,
                                                                  exclude_kwargs=exclude_kwargs,
                                                                  transformers=transformers)
        else:
            raise RuntimeWarning("The split index/label {} is out of bounds/could not be found".format(adjusted_index))

    @contextmanager
    def context(self, *args, runs=1, iterations_per_run=1, label="Context", **kwargs):
        """
        Provides a context manager that can be used with a `with` statement as `with Timer.context():`. The measured
        time is logged and is not returned. If there is no split, then a RuntimeWarning will be raised.
        :param args: any arguments to log with the run
        :param runs: the number of runs that were performed. THIS IS ONLY FOR LOGGING PURPOSES.
        :param iterations_per_run: the number of iterations that were performed. THIS IS ONLY FOR LOGGING PURPOSES.
        :param label: the label for the run
        :param kwargs: any keyword arguments to log with the run
        """
        if not self.splits:
            raise RuntimeWarning("There must be a split created before any times can be logged.")

        tm = self._time()
        yield

        dif = self._time() - tm
        self.splits[-1].add_run(Run(label=label, time=dif, runs=runs, iterations_per_run=iterations_per_run,
                                    args=args, kwargs=kwargs))

    def decorate(self, runs=1, iterations_per_run=1, call_callable_args=False, log_arguments=False, split=True,
                 split_label: str=None) -> callable:
        """
        A decorator that will time a function and store the measured time
        :param runs: the number times to measure the execution time
        :param iterations_per_run: how many times to execute the function for each run
        :param call_callable_args: If True, then any `callable` arguments/parameters that are passed into the wrapped
                    function will be replaced with their return value. So `wrapped(callable)` will actually be
                    `wrapped(callable())`
        :param log_arguments: whether to keep track of the arguments so they can be displayed at a later point or used
                    for curve calculation
        :param split: create a split that will be used to store any runs created
        :param split_label: what the name of the new split will be. If None, then func.__name__ will be used
        :return: a function wrapper
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> any:
                value = None
                new_args, new_kwargs = args, kwargs

                if split:
                    self.split(label=func.__name__ if split_label is None else split_label)
                elif not self.splits:
                    raise RuntimeWarning("No split exists. Do .split(), decorate(split=True), or Timer(split=True)")

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

                return value

            return inner_wrapper
        return wrapper

    def log(self, *args, runs=1, iterations_per_run=1, label="Log", reset=True, time_unit=BaseTimer.MS, **kwargs
            ) -> float:
        """
        Log the amount of time since the last call to `Timer(start=True)`, `.start()`, or to `.log(reset=True)`.
        Arguments can be stored by adding them to the function call. Will automatically call `.start()` again unless
        `reset=False`
        :param args: any arguments to store with this run
        :param runs: how many runs this log point is for
        :param iterations_per_run: how many iterations for each run this log point is for
        :param label: the label/name for the log point
        :param reset: whether to call `.start()` again or not
        :param time_unit: the time unit that will be used for the returned value
        :param kwargs: any keyword arguments to store with the run
        :return: the amount of time in `time_unit` since the timer was started
        """
        if self.log_base_point is None:
            raise RuntimeWarning("start() must be called before log() can be")

        if not self.splits:
            raise RuntimeWarning("A split does not exist to log this time in! " +
                                 "Create one with .split() or on timer creation with Timer(split=True)")

        tm = self._time() - self.log_base_point
        run = Run(label=label, time=tm, runs=runs, iterations_per_run=iterations_per_run, args=args, kwargs=kwargs)
        self.splits[-1].add_run(run)

        if reset:
            self.start()

        return self._convert_time(tm, time_unit, round_it=False)

    def output(self, split_index: Union[int, str]=all, time_unit=BaseTimer.MS,
               transformers: Dict[Union[int, str], Union[callable, Dict[Union[int, str], callable]]]=()):
        """
        Output all the logged runs for all of the splits or just the specified one. Transformers can be passed that will
        be used to transform how logged arguments appear in the output.
        :param split_index: the split index/name to output. Defaults to all
        :param time_unit: the time unit to output times in
        :param transformers: either a map of a split index or label to a map or just a map of a keyword
                    argument name or positional argument index to a function. That function will be called and passed
                    the argument and the return value will be used to generate the output. If this is
                    str/int -> callable, then split_index must be specified
        """
        if split_index != all:
            adjusted_index = self._adjust_split_index(split_index)

            if adjusted_index is not None:
                transformers = {adjusted_index: transformers}
            else:
                raise RuntimeWarning("The split index '{}' is not a valid index or label".format(split_index))

        # not a split index/label -> dict situation
        if transformers and callable(next(iter(transformers.values()))) and split_index == all:
            raise RuntimeWarning(
                "'split_index' must be specified when 'transformers' is Dict[Union[str, int], callable]"
            )

        self.output_stream.write(self._str(split_index=split_index, time_unit=time_unit, transformers=transformers))

    def plot(self, split_index: Union[str, int]=-1, key: Union[str, int]=None, transformer: callable=None,
             time_unit=BaseTimer.MS, y_label: str="Time", x_label: str=None, title: str=None, plot_curve: bool=False,
             curve: Tuple[str, dict]=None, curve_steps: int=100, equation_rounding: int=8):
        """
        Plot the runs in the specified split or the most recent split if none is specified. If there is more than one
        argument logged for the runs, then a key needs to be provided to use as the independent variable. The argument's
        value must be an integer or a transformer must be provided.
        :param split_index: the label or index of the split to plot
        :param key: the integer position or keyword name of the argument to use as the independent variable
        :param transformer: a transformer to make the independent variable an integer
        :param time_unit: the time unit to use when plotting
        :param y_label: the label for the y-axis, defaults to "Time"
        :param x_label: the label for the x-axis, default to None
        :param title: the title of the plot, defaults to the label of the split
        :param plot_curve: plot the best fit curve. If `curve=None`, then the best fit curve will be determined.
                    Otherwise, `curve` will be used. If the split has more than one logged argument or that argument is
                    not an integer, then the curve will need to be determined separately.
        :param curve: the curve to plot, must be formatted (curve type, params), which is how `.best_fit_curve()`
                    returns it
        :param curve_steps: the number of points used when drawing the best fit curve, if `plot_curve`
        :param equation_rounding: the number of decimal places to round the equation to if `plot_curve`
        """
        if MISSING_MAT_PLOT:
            raise RuntimeWarning("matplotlib is needed for plotting and it couldn't be found")
        if not self.splits:
            raise RuntimeWarning("There are not splits to plot")

        adjusted_index = -1 if split_index == -1 else self._adjust_split_index(split_index)
        if adjusted_index is None:
            raise RuntimeWarning("{} is not a valid split label or index".format(adjusted_index))

        x_values, y_values = [], []
        for run in self.splits[adjusted_index].runs:
            if len(run.args) + len(run.kwargs) > 1:  # need to look at key
                if key is None:
                    raise RuntimeWarning("There must be a key specified when there are more than one arguments")

                if isinstance(key, int):
                    value = run.args[key]
                else:
                    value = run.kwargs[key]
            elif run.args:
                value = run.args[0]
                key = 0
            elif run.kwargs:
                key = next(iter(run.kwargs.keys()))
                value = run.kwargs[key]
            else:
                raise RuntimeWarning("All runs in a split must have at least one argument to be plotted")

            if transformer is not None:
                value = transformer(value)

            x_values.append(value)
            y_values.append(self._convert_time(run.time, time_unit))

        plt.plot(x_values, y_values, "ro")

        if title is None:
            plt.title(self.splits[adjusted_index].label)
        else:
            plt.title(title)

        # CURVE
        if plot_curve:
            if curve is None:
                curve = self.best_fit_curve(split_index=split_index)

                if curve is None:
                    raise RuntimeWarning("Could not generate a best fit curve, so it could not be plotted")

            lower_x, upper_x = plt.xlim()
            _, upper_y = plt.ylim()

            # GENERATE CURVE POINTS
            step_value = (upper_x - lower_x) / curve_steps
            curve_x_values, curve_y_values = [], []
            for _ in range(curve_steps+1):
                curve_x_values.append(lower_x)
                curve_y_values.append(self._convert_time(
                    Split.best_fit_curves[curve[0]].calculate_point({key: lower_x}, curve[1]),
                    time_unit)
                )
                lower_x += step_value

            # PLOT CURVE
            plt.plot(
                curve_x_values,
                curve_y_values,
                label=Split.best_fit_curves[curve[0]].equation(
                    dict((key, self._convert_time(value, time_unit, False)) for key, value in curve[1].items()),
                    rounding=equation_rounding
                )
            )
            plt.legend()

        # LABELS
        plt.ylabel("{} ({})".format(y_label, time_unit))
        if x_label is not None:
            plt.xlabel(x_label)

        plt.show()

    def sort_runs(self, split_index: Union[str, int]=all, reverse: bool=False,
                  keys: Union[str, int, Dict[Union[str, int], Union[str, int]]]=None,
                  transformers: Union[callable, Dict[Union[str, int], callable]]=()):
        """
        Sort the runs in a given split, or in all splits. Sorting will default to be by time. Otherwise, it will sort
        by the value of the positional argument or keyword argument specified by the key(s).
        :param split_index: the name or label of the split to sort
        :param reverse: whether to reverse the sort order of the runs or not
        :param keys: either a string name of a keyword argument or an integer index of a positional argument or a map
                    of split indexes/labels to a string name or index position of the argument to sort on
        :param transformers: either a callable or a map of split indexes/labels to callables, where the key will be
                    used to get a value which will then be passed to this callable and the return value will be used
                    when sorting.
        """
        identity = lambda item: item

        for i in range(len(self.splits)):
            split = self.splits[i]

            if split_index == all or i == split_index or split.label == split_index:
                # get correct key for this split
                cur_key = None  # there is no key, so default to time
                if keys is not None:
                    if isinstance(keys, dict):  # if we have split indexes -> keys
                        if i in keys:
                            cur_key = keys[i]
                        elif split.label in keys:
                            cur_key = keys[split.label]
                    else:
                        cur_key = keys

                # get correct transformer
                cur_transformer = identity
                if transformers:
                    if isinstance(transformers, dict):
                        if i in transformers:
                            cur_transformer = transformers[i]
                        elif split.label in transformers:
                            cur_transformer = transformers[split.label]
                    else:
                        cur_transformer = transformers

                if cur_key is None:
                    split.runs.sort(reverse=reverse, key=lambda item: item.time)
                else:
                    if isinstance(cur_key, int):
                        split.runs.sort(reverse=reverse, key=lambda item: cur_transformer(item.args[cur_key]))
                    else:
                        split.runs.sort(reverse=reverse, key=lambda item: cur_transformer(item.kwargs[cur_key]))

    def start(self):
        """
        Start the elapsed time. Must be called before `.log()` unless `Timer(start=True)`.
        """
        self.log_base_point = self._time()

    def statistics(self, split_index: Union[int, str]=all, time_unit=BaseTimer.MS):
        """
        Output statistics for each split or for a specified split. The statistics are the number of runs, total time,
        average, standard deviation, and variance
        :param split_index: the index or label of the split to output statistics for, defaults to all
        :param time_unit: the time unit to output times in
        """
        for i in range(len(self.splits)):
            split = self.splits[i]
            if split_index != all and i != split_index and split.label != split_index:
                continue

            if not split.runs:  # skip splits with no logged times
                continue

            self.output_stream.write("{}:\n".format(split.label))

            # STATISTICS
            self.output_stream.write("{}{:<20}{}\n".format(self.indent, "Runs", len(split.runs)))
            self.output_stream.write("{}{:<20}{} {}\n".format(
                self.indent,
                "Total Time",
                self._convert_time(sum(run.time for run in split.runs), time_unit),
                time_unit
            ))
            self.output_stream.write("{}{:<20}{} {}\n".format(
                self.indent,
                "Average",
                self._convert_time(split.average(), time_unit),
                time_unit
            ))
            self.output_stream.write("{}{:<20}{} {}\n".format(
                self.indent,
                "Standard Deviation",
                self._convert_time(split.standard_deviation(), time_unit),
                time_unit
            ))
            self.output_stream.write("{}{:<20}{} {}\n".format(
                self.indent,
                "Variance",
                self._convert_time(split.variance(), time_unit),
                time_unit
            ))

            self.output_stream.write("\n")

    def split(self, label: str="Split"):
        """
        Create a new split that will be used for subsequent runs
        :param label: the label of the new split
        """
        self.splits.append(Split(label=label))

    def time_it(self, block: Union[str, callable], *args, runs=1, iterations_per_run=1, call_callable_args=False,
                log_arguments=False, split=True, split_label=None, globals: dict=(), locals: dict=(), **kwargs
                ) -> any:
        """
        Measure the execution time of a function are string. Positional and keyword arguments can be passed through to
        `block` if it is a function. `eval` is used if `block` is a string and so a namespace can be passed to it by
        setting `globals` and/or `locals`.
        :param block: either a callable or a string
        :param args: any positional arguments to pass into `block` if it is callable
        :param runs: the number of times to measure the execution time
        :param iterations_per_run: the number of times to call/evaluate `block` for each run
        :param call_callable_args: If True, then any `callable` in `args` or `kwargs` will be replaced with their
                    return value. So `time_it(func, callable1, something=callable2)` will become
                    `func(callable1(), something=callable2())`. Only useful if `block` is callable
        :param log_arguments: whether to keep track of the arguments so they can be displayed at a later point or used
                    for curve calculation. Only useful if `block` is callable
        :param split: create a split that will be used for any runs created measuring the execution time of `block`
        :param split_label: what the name of the new split will be. If None, then the label will be `block.__name__` if
                    `block` is callable. Otherwise, it will be the block itself.
        :param globals: a global namespace to pass to `eval` if `block` is a string
        :param locals: a local namespace to pass to `eval` if `block` is a string
        :param kwargs: any keyword arguments to pass into `block` if it is callable
        :return: a return/result value of calling/evaluating `block`
        """
        value = None
        new_args, new_kwargs = args, kwargs
        globals = globals if globals else {}
        locals = locals if locals else {}

        if split:
            if split_label is None:
                self.split(label=block.__name__ if callable(block) else block)
            else:
                self.split(label=split_label)
        elif not self.splits:
            raise RuntimeWarning("No split exists. Do .split(), decorate(split=True), or Timer(split=True)")

        # MEASURE
        for _ in range(runs):
            if callable(block) and call_callable_args:
                new_args, new_kwargs = self._call_callable_args(args, kwargs)

            st = StaticTimer._time()
            for _ in range(iterations_per_run):
                if callable(block):
                    value = block(*new_args, **new_kwargs)
                else:
                    value = eval(block, globals, locals)

            run = Run(label=block.__name__ if callable(block) else block, time=self._time() - st,
                      runs=1, iterations_per_run=iterations_per_run)

            if log_arguments:
                run.args = new_args
                run.kwargs = new_kwargs

            self.splits[-1].add_run(run)

        return value
