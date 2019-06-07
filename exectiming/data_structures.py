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
Provide a series of classes the collect run and split data for Timer() and provide some statistic calculating
functionality
"""

from .best_fit_curves import BestFitExponential, BestFitLinear, BestFitLogarithmic, BestFitPolynomial, \
    MISSING_CURVE_FITTING
from math import sqrt
from typing import Set, Dict, Union, Tuple, List


class Run:
    def __init__(self, label: str, time: float, runs: int, iterations_per_run: int, args: tuple=(), kwargs: dict=()):
        self.label: str = label
        self.time: float = time
        self.runs = runs
        self.iterations_per_run = iterations_per_run
        self.args: tuple = args
        self.kwargs: dict = kwargs if kwargs else {}


class Split:
    best_fit_curves = {"Exponential": BestFitExponential, "Linear": BestFitLinear, "Logarithmic": BestFitLogarithmic,
                       "Polynomial": BestFitPolynomial}

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

    def determine_best_fit(self, curve_type: str=any, exclude_args: Set[int]=(), exclude_kwargs: set=(),
                           transformers: Dict[Union[int, str], callable]=()) -> Union[None, Tuple[str, dict]]:
        """
        Determine the best fit curve for the runs contained in this split.
        :return: A tuple of a string name for the best fit curve and a dict of the parameters for that curve
        """
        if MISSING_CURVE_FITTING:
            raise RuntimeWarning("scikit-learn, scipy, and numpy are needed for curve fitting and could not be found")

        points = []
        for run in self.runs:
            if not run.args and not run.kwargs:
                raise RuntimeWarning("Arguments must have been logged to determine a best fit curve")

            # TRANSFORM ARGUMENTS
            new_args, new_kwargs = run.args[:], dict(run.kwargs)
            if transformers:
                for i in range(len(new_args)):
                    if i in transformers:
                        new_args[i] = transformers[i](new_args[i])

                for key in new_kwargs:
                    if key in transformers:
                        new_kwargs[key] = transformers[key](new_kwargs[key])

            # EXCLUDE ARGUMENTS
            collapsed = dict((i, new_args[i]) for i in range(len(new_args)) if i not in exclude_args)

            for key in new_kwargs:
                if key not in exclude_kwargs:
                    collapsed[key] = new_kwargs[key]

            points.append((collapsed, run.time))

        if curve_type is any:
            best: Tuple[float, str, dict] = None  # tuple of distance, name, and parameters
            for bfc_name, bfc in self.best_fit_curves.items():
                if not bfc.poll(points):
                    continue

                params = bfc.calculate_curve(points)

                # DISTANCE
                distance = 0
                for point in points:
                    distance += abs(point[1] - bfc.calculate_point(point[0], params))

                if best is None or distance < best[0]:
                    best = (distance, bfc_name, params)

            if best is None:
                return None
            else:
                return best[1], best[2]
        else:
            if curve_type in self.best_fit_curves:
                if self.best_fit_curves[curve_type].poll(points):
                    return curve_type, self.best_fit_curves[curve_type].calculate_curve(points)
                else:
                    raise RuntimeWarning(
                        "{}'s poll method returned that is couldn't run. There might be too many arguments.".format(
                            curve_type
                        ))
            else:
                raise RuntimeWarning("{} is an invalid curve type. Must be in [{}]".format(
                    curve_type, ", ".join(self.best_fit_curves.keys())
                ))

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
