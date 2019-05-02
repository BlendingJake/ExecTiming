from time import perf_counter
from typing import Union, Tuple
from functools import wraps
import logging


class BaseTimer:
    S, MS, US, NS = "s", "ms", "us", "ns"
    ROUNDING = 5
    _conversion = {S: 1, MS: 10**3, US: 10**6, NS: 10**9}

    @staticmethod
    def _convert_time(time: float, unit: str) -> float:
        return round(time * BaseTimer._conversion[unit], BaseTimer.ROUNDING)

    @staticmethod
    def _current_time():
        return perf_counter()

    @staticmethod
    def _format_output(name: str, runs: int, iterations: int, time: float, unit: str, args: list=(), kwargs: dict=(),
                       message: str="") -> str:
        parts = [name]

        if args or kwargs:
            parts.append("(")
            parts.append(", ".join(str(i) for i in args))

            # add separator
            if args and kwargs:
                parts.append(", ")

            parts.append(", ".join("{}={}".format(key, value) for key, value in kwargs.items()))
            parts.append(")")

        parts.append(" - [runs={}, iterations={}]: ".format(runs, iterations))
        parts.append("{} {}".format(BaseTimer._convert_time(time, unit), unit))

        if message:
            parts.append(" | {}".format(message))

        return "".join(parts)

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
                 call_callable_args=False) -> callable:
        """

        :param runs:
        :param iterations_per_run:
        :param average_runs:
        :param output_unit:
        :param use_logging:
        :param call_callable_args:
        :return:
        """
        def wrapper(func: callable) -> callable:
            @wraps(func)
            def inner_wrapper(*args, **kwargs) -> any:
                run_totals = []
                value = None
                new_args, new_kwargs = args, kwargs
                arguments = []
                for _ in range(runs):
                    # call any callable args and replace them with the result of the call
                    if call_callable_args:
                        new_args, new_kwargs = StaticTimer._replace_callable_args(args, kwargs)
                        arguments.append((new_args, new_kwargs))

                    st = StaticTimer._current_time()
                    for _ in range(iterations_per_run):
                        value = func(*new_args, **new_kwargs)

                    run_totals.append(StaticTimer._current_time() - st)

                if average_runs:
                    average = sum(run_totals) / len(run_totals)

                    if call_callable_args:
                        string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                            output_unit, args=arguments[0][0], kwargs=arguments[0][1])
                    else:
                        string = StaticTimer._format_output(func.__name__, runs, iterations_per_run, average,
                                                            output_unit)

                    if use_logging:
                        logging.info(string)
                    else:
                        print(string)
                else:
                    for i in range(len(run_totals)):
                        if call_callable_args:
                            string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                output_unit, message="Run {}".format(i+1),
                                                                args=arguments[i][0], kwargs=arguments[i][1])
                        else:
                            string = StaticTimer._format_output(func.__name__, 1, iterations_per_run, run_totals[i],
                                                                output_unit, message="Run {}".format(i+1))

                        if use_logging:
                            logging.info(string)
                        else:
                            print(string)

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
            StaticTimer.elapsed_time = StaticTimer._current_time()
        else:
            dif = StaticTimer._current_time() - StaticTimer.elapsed_time

            StaticTimer.elapsed_time = StaticTimer._current_time()


class Timer(BaseTimer):
    def __init__(self):
        pass
