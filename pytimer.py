from time import perf_counter
from typing import Union, Tuple, List, TextIO
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

        # MEASURE
        for _ in range(runs):
            st = StaticTimer._time()
            new_args, new_kwargs = args, kwargs
            for _ in range(iterations_per_run):
                if callable(block):
                    if call_callable_args:
                        new_args, new_kwargs = StaticTimer._call_callable_args(args, kwargs)

                    if log_arguments:
                        arguments.append((new_args, new_kwargs))

                    value = block(*args, **kwargs)
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


class Iteration:
    def __init__(self, label: str, time: float, args: list=(), kwargs: dict=()):
        self.label = label
        self.time = time
        self.args = args
        self.kwargs = kwargs


class Run:
    def __init__(self):
        self.iterations: List[Iteration] = []

    def add_iteration(self, iteration: Iteration):
        self.iterations.append(iteration)

    def time(self) -> float:
        if self.iterations:
            return sum(i.time for i in self.iterations)
        else:
            return 0


class Split:
    def __init__(self, label: str="Split"):
        self.runs: List[Run] = []
        self.label = label

    def add_run(self, run: Run):
        self.runs.append(run)

    def average(self) -> float:
        if self.runs:
            return sum(i.time() for i in self.runs) / len(self.runs)
        else:
            return 0


class Timer(BaseTimer):
    def __init__(self, display=True, output_stream: TextIO=stdout):
        self.display = display
        self.output_stream: TextIO = output_stream
        self.splits: List[Split] = []

    def decorate(self, runs=1, iterations_per_run=1, call_callable_args=False, log_arguments=False) -> callable:
        """
        A decorator that will time a function and then immediately output the timing results either to logging.info
        or print
        :param runs: the number of runs to measure the time for
        :param iterations_per_run: how many iterations to do in each of those runs
        :param call_callable_args: whether to call any arguments and pass those values instead
        :param log_arguments: whether to keep track of the arguments and display them in the output
        :return: a function wrapper
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> Union[any, Tuple[any, float], Tuple[any, List[float]]]:
                pass

            return inner_wrapper
        return wrapper
