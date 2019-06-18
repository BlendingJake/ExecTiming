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

"""
Provides a series of classes built on BestFitBase that all implement .calculate_curve(), .calculate_point(), and
poll(). These methods are used to determine the parameters for the given curve type, then determine the distance or
accuracy of the curve type.
"""

from typing import List, Tuple, Dict, Union

try:
    from sklearn.linear_model import LinearRegression
    from scipy.optimize import curve_fit
    import numpy as np

    np.seterr(divide="ignore")
    MISSING_CURVE_FITTING = False
except ImportError:
    MISSING_CURVE_FITTING = True


class BestFitBase:
    """
    An abstract class to be used as a template for best fit curves. The process is to first calculate the curve using
    calculated points and then check how accurate the curve is.
    """
    @staticmethod
    def _flatten_args_separate_points(points: List[Tuple[Dict[Union[str, int], int], float]]
                                      ) -> Tuple[List[List[int]], List[float]]:
        """
        Take a list of points and separate them two lists, one containing a list of all the args and kwargs values,
        the other containing the measured times corresponding to that list of arguments. Flattening the kwargs requires
        dict.values() to be stable.
        """
        flattened_args = []
        matching_points = []
        for all_args, y in points:  # flatten args and kwargs into a single list. Requires dicts to be stable
            matching_points.append(y)
            flattened_args.append(list(all_args.values()))

        return flattened_args, matching_points

    @staticmethod
    def calculate_curve(points: List[Tuple[Dict[Union[str, int], int], float]]) -> dict:
        """
        Take a list of tuples, each containing the arguments and the time value, and determines the parameters for this
        type of curve. All arguments must be integers.
        :param points: each entry is ((tuple of positional arguments, dict of keyword arguments), measured time)
        :return: a dict of the parameters of the curve
        """
        pass

    @staticmethod
    def calculate_point(arguments: Dict[Union[str, int], int], parameters: dict) -> float:
        """
        Take a tuple of arguments and calculate what the time should be for those arguments with the given parameters
        :param arguments: positional and keyword arguments. All values must be ints.
        :param parameters: the parameters of the calculated curve
        :return: the time value for the given arguments and parameters
        """
        pass

    @staticmethod
    def equation(parameters: dict, rounding: int=8) -> str:
        """
        Create a string representation of the parameters
        :param parameters: the parameters describing the curve
        :param rounding: the number of digits to round to
        :return: a string representation
        """
        return ""

    @staticmethod
    def poll(points: List[Tuple[Dict[Union[str, int], int], float]]) -> bool:
        """
        Return True if this best-fit-curve type can operate on these data points. Otherwise, return False
        """
        return not MISSING_CURVE_FITTING

    @staticmethod
    def _poll_single_arg(points):
        """
        There can only be one argument for a exponential curve, this guarantees that is the case
        """
        if MISSING_CURVE_FITTING:
            return False

        for args, _ in points:
            if len(args) != 1:
                return False

        return True


class BestFitExponential(BestFitBase):
    """
    Uses scipy.optimize.curve_fit to find `a` and `b` such that `a + b*e^x` best fits the data given. Can only handle a
    single independent variable. Generated parameters are `a` and `b`
    """
    @staticmethod
    def calculate_curve(points):
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)
        # set default params low as measured times can be very short
        values = curve_fit(lambda x, a, b: a + b*np.exp(x), [val[0] for val in flattened_args],
                           matching_points, p0=(0.0000001, 0.0000001))

        return {"a": values[0][0], "b": values[0][1]}

    @staticmethod
    def calculate_point(arguments, parameters):
        x = next(iter(arguments.values()))
        return parameters["a"] + parameters["b"]*np.exp(x)

    @staticmethod
    def equation(parameters, rounding=8):
        return "y = {} + {}e^x".format(round(parameters["a"], rounding), round(parameters["b"], rounding))

    @staticmethod
    def poll(points):
        return BestFitBase._poll_single_arg(points)


class BestFitLinear(BestFitBase):
    """
    Uses sklearn.linear_model.LinearRegression to determine coefficients for each of the independent variables and
    the y-intercept. Generate parameters are the y-intercept, `b`, and coefficients where the key is
    `x_index/key`. The index or key is the index of a positional argument or the name of a keyword argument.
    """
    @staticmethod
    def calculate_curve(points):
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)

        model = LinearRegression()
        model.fit(flattened_args, matching_points)

        params = {"b": model.intercept_}
        i = 0
        for key in points[0][0]:  # for all the keys, assuming stable iteration
            params["x_{}".format(key)] = model.coef_[i]
            i += 1

        return params

    @staticmethod
    def calculate_point(arguments, parameters):
        value = parameters["b"]

        for key in arguments:
            value += arguments[key] * parameters["x_{}".format(key)]

        return value

    @staticmethod
    def equation(parameters, rounding=8):
        return "y = {} + {}".format(
            round(parameters["b"], rounding),
            " + ".join("{}{}".format(round(value, rounding), key) for key, value in parameters.items() if key != "b")
        )


class BestFitLogarithmic(BestFitBase):
    """
    Use scipy.optimize.curve_fit to find `a` and `b` such that `a + b*log(x)` is best fitted to the data. Can only
    handle a single independent variable. Generated parameters are `a` and `b`
    """
    @staticmethod
    def calculate_curve(points):
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)
        values = curve_fit(lambda x, a, b: a + b*np.log(x), [val[0] for val in flattened_args], matching_points)

        return {"a": values[0][0], "b": values[0][1]}

    @staticmethod
    def calculate_point(arguments, parameters):
        x = next(iter(arguments.values()))
        return parameters["a"] + parameters["b"]*np.log(x)

    @staticmethod
    def equation(parameters, rounding=8):
        return "y = {} + {}*log(x)".format(round(parameters["a"], rounding), round(parameters["b"], rounding))

    @staticmethod
    def poll(points):
        return BestFitBase._poll_single_arg(points)


class BestFitPolynomial(BestFitBase):
    """
    Uses scipy.optimize.curve_fit to find the values `a`, `b`, and, `c` such that `ax^2 + bx + c` is best fit to the
    data.
    """
    @staticmethod
    def calculate_curve(points):
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)

        values = curve_fit(lambda x, a, b, c: a*np.power(x, 2) + b*x + c, [val[0] for val in flattened_args],
                           matching_points, p0=(0.000001, 0.000001, 0.000001))

        return {"a": values[0][0], "b": values[0][1], "c": values[0][2]}

    @staticmethod
    def calculate_point(arguments, parameters):
        x = next(iter(arguments.values()))

        return parameters["a"] * x**2 + parameters["b"]*x + parameters["c"]

    @staticmethod
    def equation(parameters, rounding=8):
        return "y = {}x^2 + {}x + {}".format(
            round(parameters["a"], rounding),
            round(parameters["b"], rounding),
            round(parameters["c"], rounding)
        )

    @staticmethod
    def poll(points):
        return BestFitBase._poll_single_arg(points)
