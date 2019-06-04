# PyTimer - A Python packaged for measuring the execution time of code
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

from typing import List, Tuple, Dict

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from scipy.optimize import curve_fit
import numpy as np


class BestFitBase:
    """
    An abstract class to be used as a template for best fit curves. The process is to first calculate the curve using
    calculated points and then check how accurate the curve is.
    """
    @staticmethod
    def _flatten_args_separate_points(points: List[Tuple[Tuple[List[int], Dict[str, int]], float]]
                                      ) -> Tuple[List[List[int]], List[float]]:
        """
        Take a list of points and separate them two lists, one containing a list of all the args and kwargs flattened,
        the other containing the measured times corresponding to that list of arguments. Flattening the kwargs requires
        dict.values() to be stable.
        """
        flattened_args = []
        matching_points = []
        for all_args, y in points:  # flatten args and kwargs into a single list. Requires dicts to be stable
            matching_points.append(y)

            args = [arg for arg in all_args[0]]
            args.extend(all_args[1].values())  # relies on keys(), and values() being stable
            flattened_args.append(args)

        return flattened_args, matching_points

    @staticmethod
    def calculate_curve(points: List[Tuple[Tuple[List[int], Dict[str, int]], float]]) -> dict:
        """
        Take a list of tuples, each containing the arguments and the time value, and determines the parameters for this
        type of curve. All arguments must be integers.
        :param points: each entry is ((tuple of positional arguments, dict of keyword arguments), measured time)
        :return: a dict of the parameters of the curve
        """
        pass

    @staticmethod
    def calculate_point(arguments: Tuple[List[int], Dict[str, int]], parameters: dict) -> float:
        """
        Take a tuple of arguments and calculate what the time should be for those arguments with the given parameters
        :param arguments: positional and keyword arguments. All values must be ints.
        :param parameters: the parameters of the calculated curve
        :return: the time value for the given arguments and parameters
        """
        pass

    @staticmethod
    def poll(points: List[Tuple[Tuple[List[int], Dict[str, int]], float]]) -> bool:
        """
        Determine if this best fit method will work with the given data
        """
        return True


class BestFitExponential(BestFitBase):
    @staticmethod
    def calculate_curve(points):
        """
        Use scipy.optimize.curve_fit with a*e^(b*x) to find a and b for this exponential curve
        """
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)
        values = curve_fit(lambda x, a, b: a*np.exp(b*x), [val[0] for val in flattened_args], matching_points,
                           p0=(0.000001, 0.000001))  # set default params low as measured times can be very short

        return {"a": values[0][0], "b": values[0][1]}

    @staticmethod
    def calculate_point(arguments, parameters):
        x = arguments[0][0] if arguments[0] else list(arguments[1].values())[0]  # get arg or kwarg
        return parameters["a"] * np.exp(parameters["b"]*x)

    @staticmethod
    def poll(points):
        """
        There can only be one argument for a exponential curve, this guarantees that is the case
        """
        for args, _ in points:
            if len(args[0]) + len(args[1]) != 1:
                return False

        return True


class BestFitLinear(BestFitBase):
    @staticmethod
    def calculate_curve(points):
        """
        Use sklearn.linear_model.LinearRegression to determine the variable coefficients and y-intercept
        """
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)

        model = LinearRegression()
        model.fit(flattened_args, matching_points)

        params = {"b": model.intercept_}
        i = 0
        for _ in range(len(points[0][0][0])):
            params["x{}".format(i)] = model.coef_[i]
            i += 1

        for key in points[0][0][1]:
            params[key] = model.coef_[i]
            i += 1

        return params

    @staticmethod
    def calculate_point(arguments, parameters):
        """

        """
        value = parameters["b"]

        for i in range(len(arguments[0])):
            value += arguments[0][i] * parameters["x{}".format(i)]

        for key in arguments[1]:
            value += arguments[1][key] * parameters[key]

        return value


class BestFitLogarithmic(BestFitBase):
    @staticmethod
    def calculate_curve(points):
        """
        Use scipy.optimize.curve_fit with a + b*log(x) to find a and b for this logarithmic curve
        """
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)
        values = curve_fit(lambda x, a, b: a + b*np.log(x), [val[0] for val in flattened_args], matching_points)

        return {"a": values[0][0], "b": values[0][1]}

    @staticmethod
    def calculate_point(arguments, parameters):
        x = arguments[0][0] if arguments[0] else list(arguments[1].values())[0]  # get arg or kwarg
        return parameters["a"] + parameters["b"]*np.log(x)

    @staticmethod
    def poll(points):
        """
        There can only be one argument for a logarithmic curve, this guarantees that is the case
        """
        for args, _ in points:
            if len(args[0]) + len(args[1]) != 1:
                return False

        return True


class BestFitPolynomial(BestFitBase):
    @staticmethod
    def calculate_curve(points):
        """
        Use sklearn.linear_model.LinearRegression to determine the variable coefficients and y-intercept
        """
        flattened_args, matching_points = BestFitBase._flatten_args_separate_points(points)

        poly_model = PolynomialFeatures(degree=2)
        values = poly_model.fit_transform(flattened_args)

        values_model = LinearRegression()
        values_model.fit(values, matching_points)

        params = {"b": values_model.intercept_}
        for i in range(len(values_model.coef_)):
            params["x^{}".format(i)] = values_model.coef_[i]

        return params

    @staticmethod
    def calculate_point(arguments, parameters):
        """

        """
        flattened_args = arguments[0][:]
        flattened_args.extend(arguments[1].values())

        poly_model = PolynomialFeatures(degree=2)
        adjusted = poly_model.fit_transform([flattened_args])[0]

        value = parameters["b"]
        for i in range(len(adjusted)):
            value += parameters["x^{}".format(i)] * adjusted[i]

        return value
