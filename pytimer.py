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

from time import perf_counter
from datetime import datetime


class PyTimer(object):
    """
    PyTimer is a class for easily timing execution of sections of codes. PyTimer supports splitting
    to allow different segments of code to be timed separately.
    """
    seconds = 's'
    milliseconds = "ms"
    microseconds = "(mu)s"
    nanoseconds = "ns"

    _elapsed_times = [[]]
    _logged_messages = [[]]
    _split_messages = []
    _collected_output = []

    _start_time = 0
    _running_time = 0
    _decorator_reps = 1
    _decorator_iterations = 10
    _units = ""
    rounding = 4

    _paused = False
    _started = False
    _run = True
    _collect_output = False
    _display = True

    def __init__(self, *args, **kwargs):
        """
        Create timer object, start() is called automatically unless args[0] is False
        :param args: args[0] should be a bool that tells whether or not to automatically
        :param kwargs: in (round, run, collect, display, units)
        """
        # automatically start unless set not to
        if len(args) == 0 or (len(args) >= 1 and isinstance(args[0], bool) and args[0]):
            self.start()

        if "round" in kwargs:
            if isinstance(kwargs['round'], int) and kwargs['round'] > 0:
                self.rounding = kwargs['round']
            else:
                self._write("Round must be an integer value greater than 0")

        if 'run' in kwargs:
            if isinstance(kwargs['run'], bool):
                self._run = kwargs['run']
            else:
                self._write("Run must be a boolean value")

        if 'collect' in kwargs:
            if isinstance(kwargs['collect'], bool):
                self._collect_output = kwargs['collect']
            else:
                self._write("Collect must be a boolean value")

        if 'display' in kwargs:
            if isinstance(kwargs['display'], bool):
                self._display = kwargs['display']
            else:
                self._write("Display must be a boolean value")

        if 'units' in kwargs:
            if kwargs['units'] in (PyTimer.seconds, PyTimer.milliseconds, PyTimer.nanoseconds, PyTimer.microseconds):
                self._units = kwargs['units']
            else:
                self._write("Units must be in PyTimer.(seconds, milliseconds, nanoseconds, microseconds)")

    def __str__(self):
        """
        Returns string of all values in all splits, if split is empty, than message is displayed
        :return: string of all values in all splits
        """
        if self._run:
            # pretty print table
            strings = []
            for i in range(len(self._elapsed_times)):  # for every split
                strings.append(self._format_split(i, True))

            if len(self._elapsed_times) > 0:
                strings.append("\n")

            return "".join(strings)
        else:
            return ""

    def _confirm_started(self):
        """
        Called by most methods to start out with, confirm that timer has been started. Can lead to errors, because
        timer might not be started until log() is called, meaning that the elapsed time is 0
        """
        if not self._started and self._run:
            self.start()

    def _format_time(self, t: float) -> str:
        if self._run:
            if (self._units == "" and t < 0.00000001) or self._units == PyTimer.nanoseconds:
                return str(round(t * 1000000000, self.rounding)) + " {}".format(PyTimer.nanoseconds)
            elif (self._units == "" and t < 0.00001) or self._units == PyTimer.microseconds:
                return str(round(t * 1000000, self.rounding)) + " {}".format(PyTimer.microseconds)
            elif (self._units == "" and t < 0.01) or self._units == PyTimer.milliseconds:
                return str(round(t * 1000, self.rounding)) + " {}".format(PyTimer.milliseconds)
            else:
                return str(round(t, self.rounding)) + " {}".format(PyTimer.seconds)

    def _format_split(self, i: int, newline: bool) -> str:
        """
        Return string with all values in split. If the split is empty, than split is just listed as empty. Will throw
        IndexError if i is invalid, so checks should be done outside of here
        :param i: index of split
        :param newline: add newline at end
        :return: string with all values from split, or message if split is empty
        """
        if self._run:
            str_list = ["Split " + str(i) + ":" if i >= len(self._split_messages) or self._split_messages[i] == ""
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

    def _parse_kwargs_reps_iter(self, kwargs: dict, rep_default: int, iter_default: int):
        """
        Checks kwargs for reps and iterations and makes sure they are the correct type and >= 1, if either aren't then
        their default value is returned
        :param kwargs: dictionary
        :param rep_default: the value to use for reps if not found in kwargs
        :param iter_default: the value to use for iterations if not found in kwargs
        :return: reps and iterations are either their default values, or the values found in kwargs
        """
        reps = rep_default
        if 'reps' in kwargs:
            if isinstance(kwargs['reps'], int) and kwargs['reps'] >= 1:
                reps = kwargs['reps']
            elif isinstance(kwargs['reps'], int) and kwargs['reps'] <= 0:
                self._write("Reps cannot be less than 1\n")
            else:
                self._write("Reps must be an integer value\n")

        iterations = iter_default
        if 'iterations' in kwargs:
            if isinstance(kwargs['iterations'], int) and kwargs['iterations'] >= 1:
                iterations = kwargs['iterations']
            elif isinstance(kwargs['iterations'], int) and kwargs['iterations'] <= 0:
                self._write("Iterations cannot be less than 1\n")
            else:
                self._write("Iterations must be an integer value\n")

        return reps, iterations

    @classmethod
    def _time(cls):  # allow internal timer to be changed easily
        return perf_counter()

    def _valid_split(self, i: int) -> bool:
        if self._run:
            return len(self._split_messages) > 0 and 0 <= i < len(self._split_messages) and \
                       self._split_messages[i] != ""

    def _write(self, *args):  # write to console if _display, add to collected outputs if _collect_output
        if self._display and len(args) == 1 and self._run:
            print(args[0])
        elif self._display and len(args) == 0 and self._run:
            print()

        if self._run and self._collect_output:  # save output
            if len(args) > 0:
                self._collected_output.append(args[0])
            self._collected_output.append("\n")

    def average(self, i: int):
        """
        Calculates average for split i
        :param i: Index of split to determine average for
        :return: None if empty split, False if invalid index, otherwise average for split
        """
        if self._run:
            self._confirm_started()

            if 0 <= i < len(self._elapsed_times) and len(self._elapsed_times[i]) > 0:
                count = 0
                for j in range(len(self._elapsed_times[i])):
                    count += self._elapsed_times[i][j]
                return count / len(self._elapsed_times[i])
            elif 0 <= i < len(self._elapsed_times):  # empty split
                return None
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))
                return False

    def averages(self) -> list:
        """
        Returns list of averages for every split
        :return: list of averages, if position i is invalid, then list[i] is None
        """
        if self._run:
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
            if self._run:
                val = None
                for i in range(self._decorator_iterations):
                    for j in range(self._decorator_reps):
                        val = function(*args)
                    self.log()
                self.split("Function -> " + function.__name__)

                return val  # make sure value gets returned
            else:
                return function(*args)
        return wrapper

    def deviation(self, i: int):
        """
        Calculates standard deviation for split i
        :param i: split index
        :return: None if split i is empty, False if invalid index, otherwise returns standard deviation of split i
        """
        if self._run:
            av = self.average(i)
            if av is not None and not isinstance(av, bool):
                total = 0
                for val in self._elapsed_times[i]:
                    total += (val - av) ** 2  # Sum from 1->N: (val - av)^2
                return ((1 / len(self._elapsed_times[i])) * total) ** 0.5  # sqrt((1/N) * total)
            elif av is None:
                return None
            else:
                return False

    def deviations(self) -> list:
        """
        Calculates standard deviations for every split
        :return: list of standard deviations for all splits. If split i is empty, than list[i] is None
        """
        if self._run:
            return [self.deviation(i) for i in range(len(self._elapsed_times))]

    def display_average(self, i: int):
        """
        Display average for split i if valid index and split is not empty, otherwise displays appropriate message
        :param i: split index
        """
        if self._run:
            num = self.average(i)
            if num is not None and not isinstance(num, bool):
                self._write(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                            ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " + self._format_time(num) +
                            "\n")
            elif num is None:
                self._write(self._format_split(i, True))
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))

    def display_averages(self):
        """
        Display averages for all splits unless split i is empty, in which case it is skipped
        """
        if self._run:
            av = self.averages()
            for i in range(len(av)):
                if av[i] is not None:
                    self._write(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                                ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " +
                                self._format_time(av[i]))

            if len(av) > 0 and av[0] is not None:  # add final newline
                self._write()

    def display_deviation(self, i: int):
        """
        Display standard deviation for split i if valid index and split is not empty, otherwise displays appropriate
        message
        :param i: split index
        """
        if self._run:
            dev = self.deviation(i)
            if dev is not None and not isinstance(dev, bool):
                self._write(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                            ":\n\tStandard Deviation: " + self._format_time(dev) + "\n")
            elif dev is None:
                self._write(self._format_split(i, True))
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))

    def display_deviations(self):
        """
        Display standard deviation for all splits unless split is empty, in which case that split is skipped
        """
        if self._run:
            devs = self.deviations()
            for i in range(len(devs)):
                if devs[i] is not None:
                    self._write(("Split " + str(i + 1) if not self._valid_split(i) else self._split_messages[i]) +
                                ":\n\tStandard Deviation: " + self._format_time(devs[i]))

            if len(devs) > 0 and devs[0] is not None:  # add newline
                self._write()

    def display_split(self, i: int):
        """
        Display all values in split i if valid index and split is not empty, otherwise displays appropriate message
        :param i: split index
        """
        if self._run:
            self._confirm_started()
            if 0 <= i < len(self._elapsed_times) and len(self._elapsed_times[i]) > 0:
                self._write(self._format_split(i, False))
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))

    def display_splits(self):
        """
        Display all values for all splits unless split is empty, in which case the split is skipped
        """
        if self._run:
            self._confirm_started()
            for i in range(len(self._elapsed_times)):
                if len(self._elapsed_times[i]) > 0:  # make sure split is not empty
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
        if self._run:
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
        Log elapsed time, log will have no affect if timer is paused
        :param message: optional: store message with the log
        """
        if self._run:
            self._confirm_started()
            if not self._paused:
                self._elapsed_times[len(self._elapsed_times) - 1].append(self._time() - self._running_time)
                self._logged_messages[len(self._logged_messages) - 1].append(str(message))
                self._running_time = self._time()
            else:
                self._write("Timer is currently paused: log had no affect\n")

    def overall_time(self) -> float:
        """
        :return: Elapsed time since start()
        """
        if self._run:
            self._confirm_started()
            return self._time() - self._start_time

    def pause(self):
        if self._run:
            self._confirm_started()
            self._paused = True

    def reset(self):
        if self._run:
            self._elapsed_times = [[]]
            self._logged_messages = [[]]
            self._split_messages = []

        self._paused = False
        self.start()

    def resume(self):
        if self._run:
            self._confirm_started()
            self._paused = False
            self._running_time = self._time()

    def setup_decorator(self, **kwargs):
        """
        Allow decorator to run function for multiple reps and iterations
        :param kwargs: in (reps, iterations)
        """
        if self._run:
            reps, iterations = self._parse_kwargs_reps_iter(kwargs, 1, 10)

            self._decorator_iterations = iterations
            self._decorator_reps = reps

    def split(self, message=""):
        if self._run:
            self._confirm_started()
            self._split_messages.append(message)
            self._elapsed_times.append([])
            self._logged_messages.append([])
            self._running_time = self._time()

    def start(self):
        if self._run:
            self._start_time = self._time()
            self._running_time = self._time()
            self._started = True

    def times(self, i: int):
        """
        Return list of elapsed times for split i
        :param i: index of split
        :return: returns list of elapsed times for split i if valid index, otherwise returns None
        """
        if self._run:
            self._confirm_started()
            if 0 <= i <= len(self._elapsed_times[i]):
                return self._elapsed_times[i]
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))
                return None

    def write_output(self, fp: str):
        if not self._collect_output and self._run:
            self._write("Timer was not set to save output, to do so: PyTimer(save_output=True)\n")

        if self._run:
            try:
                file = open(fp, 'w')

                file.write(datetime.today().strftime("Saved on %B %d, %Y at %I:%M:%S %p\n\n"))

                for line in self._collected_output:
                    file.write(line)
                file.close()

                if self._display:
                    self._write("Saved file successfully\n")
            except PermissionError:
                self._write("Could not write to file path '{}'\n".format(fp))
