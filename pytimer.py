from time import perf_counter
from typing import Union, Tuple
from functools import wraps
import logging


class BaseTimer:
    S, MS, US, NS = "s", "ms", "us", "ns"
    ROUNDING = 5
    _conversion = {S: 1, MS: 10**3, US: 10**6, NS: 10**9}
    _time = perf_counter

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
    def _display_message(message: str, use_logging: bool=False):
        """
        Display the message to the proper output
        :param message: the message to display
        :param use_logging: whether to display the message to logging.info or print
        """
        if use_logging:
            logging.info(message)
        else:
            print(message)

    @staticmethod
    def _format_output(name: str, runs: int, iterations: int, time: float, unit: str, args: list=(), kwargs: dict=(),
                       message: str="") -> str:
        """
        Build up a string message based on the input parameters
        :param name: the name of the function, part of the string being timed, or label of the call
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
            name_part = "{:42.42}".format("{}({})".format(name, arguments[:25]))
        else:
            name_part = "{:15.15}".format(name)

        if message:
            message = "| {}".format(message)

        return "{:.5} {:2} - {} [runs={:3}, iterations={:3}] {:<20.20}".format(BaseTimer._convert_time(time, unit),
                                                                               unit, name_part, runs, iterations,
                                                                               message)

    @staticmethod
    def _replace_callable_args(args: tuple, kwargs: dict) -> Tuple[list, dict]:
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


class StaticTimer(BaseTimer):
    elapsed_time = None

    @staticmethod
    def decorate(runs=1, iterations_per_run=1, average_runs=True, output_unit=BaseTimer.MS, use_logging=False,
                 call_callable_args=False, log_arguments=False) -> callable:
        """
        A decorate that will time a function and then immediately output the timing results either to logging.info
        or print
        :param runs: the number of runs to measure the time for
        :param iterations_per_run: how many iterations to do in each of those runs
        :param average_runs: whether to average the runs together or list them individually
        :param output_unit: the time scale to output the values in
        :param use_logging: whether to use logging.info instead of print
        :param call_callable_args: whether to call any arguments and pass those values instead
        :param log_arguments: whether to keep track of the arguments and display them in the output
        :return: a function wrapper
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> any:
                run_totals = []
                value = None
                new_args, new_kwargs = args, kwargs
                arguments = []

                # COLLECT
                for _ in range(runs):
                    # call any callable args and replace them with the result of the call
                    if call_callable_args:
                        new_args, new_kwargs = StaticTimer._replace_callable_args(args, kwargs)

                    if log_arguments:
                        arguments.append((new_args, new_kwargs))

                    st = StaticTimer._time()
                    for _ in range(iterations_per_run):
                        value = func(*new_args, **new_kwargs)

                    run_totals.append(StaticTimer._time() - st)

                # DISPLAY
                if average_runs:
                    average = sum(run_totals) / len(run_totals)

                    if log_arguments:
                        string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                            output_unit, args=arguments[0][0], kwargs=arguments[0][1])
                    else:
                        string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                            output_unit)

                    StaticTimer._display_message(string, use_logging=use_logging)
                else:
                    for i in range(len(run_totals)):
                        if log_arguments:
                            string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                output_unit, message="Run {}".format(i+1),
                                                                args=arguments[i][0], kwargs=arguments[i][1])
                        else:
                            string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                output_unit, message="Run {}".format(i+1))

                        StaticTimer._display_message(string, use_logging=use_logging)

                return value
            return inner_wrapper
        return wrapper

    @staticmethod
    def time_it(block: Union[str, callable], *args, **kwargs):
        if isinstance(block, str):
            pass
        else:
            pass

    @staticmethod
    def elapsed():
        if StaticTimer.elapsed_time is None:
            StaticTimer.elapsed_time = StaticTimer._time()
        else:
            dif = StaticTimer._time() - StaticTimer.elapsed_time

            StaticTimer.elapsed_time = StaticTimer._time()


class Timer(BaseTimer):
    def __init__(self):
        pass
