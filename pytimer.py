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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Original Author = Jacob Morris

from time import time


class PyTimer(object):
    """
    PyTimer is a class for easily timing execution of sections of codes. PyTimer supports splitting
    to allow different segments of code to be timed separately.
    """

    _elapsed_times = [[]]
    _logged_messages = [[]]
    _split_messages = []

    _start_time = 0
    _running_time = 0
    _decorator_reps = 1
    _decorator_iterations = 10
    _paused = False
    _started = False

    def __init__(self, rounder=4):
        self.rounding = rounder

    def __str__(self):
        # pretty print table
        strings = []
        for i in range(len(self._elapsed_times)):  # for every split
            if len(self._elapsed_times[i]) > 0:
                strings.append(self._format_split(i, True))

        return "".join(strings)

    def _confirm_started(self):
        """
        Called by most methods to start out with, confirm that timer has been started
        """
        if not self._started:
            self._start()

    def _format_time(self, t: float) -> str:
        if t < 0.001:
            return str(round(t * 1000, self.rounding)) + " ms"
        else:
            return str(round(t, self.rounding)) + " s"

    def _format_split(self, i: int, newline: bool) -> str:
        str_list = ["Split " + str(i + 1) + ":" if i >= len(self._split_messages) or self._split_messages[i] == ""
                    else self._split_messages[i] + ":", "\n"]

        for j in range(len(self._elapsed_times[i])):  # for every log in split
            str_list.append("\t")
            str_list.append(self._format_time(self._elapsed_times[i][j]) + (": {}".
                                                                            format(self._logged_messages[i][j])
                                                                            if self._logged_messages[i][j] != ""
                                                                            else ""))
            str_list.append("\n")

        if len(self._elapsed_times[i]) == 0:  # empty split
            str_list.append("\t-- Empty Split --")
        if newline:
            str_list.append("\n")

        return "".join(str_list)

    def _start(self):
        self._start_time = time()
        self._running_time = time()
        self._started = True

    def _valid_split(self, i: int) -> bool:
        return len(self._split_messages) > 0 and 0 <= i < len(self._split_messages) and self._split_messages[i] != ""

    def average(self, i: int):
        """
        Calculates average for i'th split
        :param i: Index of split to determine average for
        :return: None if invalid or empty split, otherwise average for split
        """
        self._confirm_started()

        if 0 <= i < len(self._elapsed_times) and len(self._elapsed_times[i]) > 0:
            count = 0
            for j in range(len(self._elapsed_times[i])):
                count += self._elapsed_times[i][j]
            return count / len(self._elapsed_times[i])
        elif 0 <= i < len(self._elapsed_times):  # empty split
            return None
        else:
            raise IndexError("Invalid split index, must be in [0-{}]".format(len(self._elapsed_times) - 1))

    def averages(self) -> list:
        """
        Returns averages for every split. If split i has no values, then list[i] is None
        :return: list of averages, if position i is invalid, then list[i] is None
        """
        return [self.average(i) for i in range(len(self._elapsed_times))]

    def decorator(self, function: callable) -> callable:
        """
        Returns a decorator so that functions can be timed with having to use evaluate, but functions can't take any
        parameters
        :param function: takes a function as a parameter
        :return: a wrapper function for use as a decorator
        """
        self._confirm_started()

        def wrapper(*args):
            """
            wrapper returned when using as decorator
            :param args: (optional) values to be passed into function that is being called
            """
            for i in range(self._decorator_iterations):
                for j in range(self._decorator_reps):
                    function(*args)
                self.log()
            self.split("Function -> " + function.__name__)
        return wrapper

    def deviation(self, i: int):
        """
        Calculates standard deviation for split i
        :param i: split position
        :return: None if i is invalid or empty split, otherwise returns standard deviation of split i
        """
        av = self.average(i)
        if av is not None:
            total = 0
            for val in self._elapsed_times[i]:
                total += (val - av) ** 2  # Sum from 1->N: (val - av)^2
            return ((1 / len(self._elapsed_times[i])) * total) ** 0.5  # sqrt((1/N) * total)
        else:
            return None

    def deviations(self) -> list:
        """
        Calculates standard deviations for every split. If split is invalid or empty, then value is None for that split
        :return: list of standard deviations for all splits
        """
        return [self.deviation(i) for i in range(len(self._elapsed_times))]

    def display_average(self, i: int):
        """
        Display average for split i in a formatted view if i is a valid, non-empty split
        :param i: split position
        """
        num = self.average(i)
        if num is not None:
            print(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                  ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " + self._format_time(num) + "\n")
        else:
            print(self._format_split(i, True))

    def display_averages(self):
        """
        Display averages for all splits in a formatted view
        """
        av = self.averages()
        for i in range(len(av)):
            if av[i] is not None:
                print(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                      ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " + self._format_time(av[i]))

        if len(av) > 0:  # add final newline
            print()

    def display_deviation(self, i: int):
        """
        Display standard deviation for split i in a formatted view if i is a valid, non-empty split
        :param i: split position
        """
        dev = self.deviation(i)
        if dev is not None:
            print(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                  ":\n\tStandard Deviation: " + self._format_time(dev) + "\n")
        else:
            print(self._format_split(i, True))

    def display_deviations(self):
        """
        Display standard deviation for all splits in a formatted view
        """
        devs = self.deviations()
        for i in range(len(devs)):
            if devs[i] is not None:
                print(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                      ":\n\tStandard Deviation: " + self._format_time(devs[i]))

        if len(devs) > 0:  # add newline
            print()

    def display_split(self, i: int):
        """
        Display all values in split if i is valid position for split
        :param i: position of split
        """
        self._confirm_started()
        if 0 <= i < len(self._elapsed_times):
            print(self._format_split(i, False))
        else:
            raise IndexError("Invalid split index, must be in [0-{}]".format(len(self._elapsed_times) - 1))

    def display_splits(self):
        """
        Display all values for all splits
        """
        self._confirm_started()
        for i in range(len(self._elapsed_times)):
            self.display_split(i)

    def evaluate(self, block, *args, **kwargs):
        """
        Evaluates a string of code or a function and times how long it takes for each iteration. If block is a function,
        then parameters can be passed to it like so: evaluate(bar, "something", 12, iterations=100) ->
        bar("something", 12). No error checking is done, meaning any error that is raised within block will crash
        the entire program.
        :param block: either function or string of code
        :param args: any arguments that needs to be passed into block if block is a function
        :param kwargs: can be any in (reps, iterations, message) which have their usual definition
        """
        self._confirm_started()
        self.pause()

        reps, iterations = self._parse_kwargs_reps_iter(kwargs, 10, 10)

        # build string with function and needed variables
        string = ""
        split_message = kwargs['message'] if 'message' in kwargs else ""

        if callable(block):
            if not split_message:  # if no message was passed in
                split_message = "Function -> {}".format(block.__name__)

            string_builder = ["block("]
            for i in range(len(args)):
                string_builder.append("args[")
                string_builder.append(str(i))
                string_builder.append("]")

                if i != len(args) - 1:
                    string_builder.append(", ")
            string_builder.append(")")
            string = "".join(string_builder)
        elif isinstance(block, str):
            if not split_message:  # if not message was passed in
                if len(block) > 50:  # shorten string if really long
                    split_message = "String Block -> '{}'...".format(block[0:50])
                else:
                    split_message = "String Block -> '{}'".format(block)

            string = block

        if string != "":
            self.resume()

            for i in range(iterations):
                for j in range(reps):
                    exec(string)
                self.log()
            self.split(message=split_message)

    def log(self, message=""):
        """
        Log elapsed time. Will raise RuntimeWarning if timer is currently paused
        :param message: optional: store message with the log
        """
        self._confirm_started()
        if not self._paused:
            self._elapsed_times[len(self._elapsed_times) - 1].append(time() - self._running_time)
            self._logged_messages[len(self._logged_messages) - 1].append(str(message))
            self._running_time = time()
        else:
            raise RuntimeWarning("Timer is currently paused: log had no affect")

    def overall_time(self) -> float:
        """
        :return: Elapsed time since _start()
        """
        self._confirm_started()
        return time() - self._start_time

    @classmethod
    def _parse_kwargs_reps_iter(cls, kwargs: dict, rep_default: int, iter_default: int):
        """
        Checks kwargs for reps and iterations and makes sure they are the correct type and >= 1, if either aren't then
        their default value is returned
        :param kwargs: dictionary
        :param rep_default: the value to use for reps if not found in kwargs
        :param iter_default: the value to use for iterations if not found in kwargs
        :return: reps and iterations either as their default values or the value found in kwargs
        """
        if 'reps' in kwargs:
            if isinstance(kwargs['reps'], int) and kwargs['reps'] >= 1:
                reps = kwargs['reps']
            elif isinstance(kwargs['reps'], int) and kwargs['reps'] <= 0:
                raise ValueError("Reps cannot be less than 1")
            else:
                raise TypeError("Reps must be an integer value")
        else:
            reps = rep_default

        if 'iterations' in kwargs:
            if isinstance(kwargs['iterations'], int) and kwargs['iterations'] >= 1:
                iterations = kwargs['iterations']
            elif isinstance(kwargs['iterations'], int) and kwargs['iterations'] <= 0:
                raise ValueError("Iterations cannot be less than 1")
            else:
                raise TypeError("Iterations must be an integer value")
        else:
            iterations = iter_default

        return reps, iterations

    def pause(self):
        self._confirm_started()
        self._paused = True

    def reset(self):
        self._elapsed_times = [[]]
        self._logged_messages = [[]]
        self._split_messages = []

        self._paused = False
        self._start()

    def resume(self):
        self._confirm_started()
        self._paused = False
        self._running_time = time()

    def setup_decorator(self, **kwargs):
        """
        Allow decorator to run function for multiple reps and iterations
        :param kwargs: in (reps, iterations)
        """
        reps, iterations = self._parse_kwargs_reps_iter(kwargs, 1, 10)

        self._decorator_iterations = iterations
        self._decorator_reps = reps

    def split(self, message=""):
        self._confirm_started()
        self._split_messages.append(message)
        self._elapsed_times.append([])
        self._logged_messages.append([])
        self._running_time = time()

    def times(self, i: int):
        self._confirm_started()
        if 0 <= i <= len(self._elapsed_times[i]):
            return self._elapsed_times[i]
        else:
            return None
