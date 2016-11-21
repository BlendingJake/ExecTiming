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
    _paused = False

    def __init__(self, rounder=4):
        self.rounding = rounder

    def __str__(self):
        # pretty print table
        strings = []
        for i in range(len(self._elapsed_times)):  # for every split
            if len(self._elapsed_times[i]) > 0:
                strings.append(self._format_split(i))

        return "".join(strings)

    def _format_time(self, t):
        if t < 0.001:
            return str(round(t * 1000, self.rounding)) + " ms"
        else:
            return str(round(t, self.rounding)) + " s"

    def _format_split(self, i):
        string = []
        string.append("Split " + str(i + 1) + ":" if i >= len(self._split_messages) or self._split_messages[i] == ""
                      else self._split_messages[i] + ":")

        string.append("\n")
        for j in range(len(self._elapsed_times[i])):  # for every log in split
            string.append("\t")
            string.append(self._format_time(self._elapsed_times[i][j]) + (": {}".
                                                                          format(self._logged_messages[i][j])
                                                                          if self._logged_messages[i][j] != ""
                                                                          else ""))
            string.append("\n")
        string.append("\n")

        return "".join(string)

    def average(self, i):
        """
        Calculates average for i'th split
        :param i: Index of split to determine average for
        :return: None if invalid or empty split, otherwise average for split
        """
        if 0 <= i < len(self._elapsed_times) and len(self._elapsed_times[i]) > 0:
            count = 0
            for j in range(len(self._elapsed_times[i])):
                count += self._elapsed_times[i][j]
            return count / len(self._elapsed_times[i])
        else:
            return None

    def averages(self):
        """
        Returns averages for every split. If split i has no values, then list[i] is None
        :return: list of averages, if position i is invalid, then list[i] is None
        """
        return [self.average(i) for i in range(len(self._elapsed_times))]

    def deviation(self, i):
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

    def deviations(self):
        """
        Calculates standard deviations for every split. If split is invalid or empty, then value is None for that split
        :return: list of standard deviations for all splits
        """
        return [self.deviation(i) for i in range(len(self._elapsed_times))]

    def display_average(self, i):
        """
        Display average for split i in a formatted view if i is a valid, non-empty split
        :param i: split position
        """
        num = self.average(i)
        if num is not None:
            print(("Split " + str(i + 1) if self._split_messages[i] == "" else self._split_messages[i]) +
                  ":\n\tAverage: " + self._format_time(num))

    def display_averages(self):
        """
        Display averages for all splits in a formatted view
        """
        av = self.averages()
        for i in range(len(av)):
            if av[i] is not None:
                print(("Split " + str(i + 1) if self._split_messages[i] == "" else self._split_messages[i]) +
                      ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " + self._format_time(av[i]))

    def display_deviation(self, i):
        """
        Display standard deviation for split i in a formatted view if i is a valid, non-empty split
        :param i: split position
        """
        dev = self.deviation(i)
        if dev is not None:
            print(("Split " + str(i + 1) if self._split_messages[i] == "" else self._split_messages[i]) +
                  ":\n\tStandard Deviation: " + self._format_time(dev))

    def display_deviations(self):
        """
        Display standard deviation for all splits in a formatted view
        """
        devs = self.deviations()
        for i in range(len(devs)):
            if devs[i] is not None:
                print(("Split " + str(i + 1) if self._split_messages[i] == "" else self._split_messages[i]) +
                      ":\n\tStandard Deviation: " + self._format_time(devs[i]))

    def display_split(self, i):
        """
        Display all values in split if i is valid position for split
        :param i: position of split
        """
        if 0 <= i <= len(self._elapsed_times) and len(self._elapsed_times[i]) > 0:
            print(self._format_split(i))

    def evaluate(self, block, iterations, *args):
        """
        Evaluates a string of code or a function and times how long it takes for each iteration. If block is a function,
        then parameters can be passed to it like so: evaluate(bar, 100, 12, "something") -> bar(12, "something"). No
        error checking is done, meaning any error that is raised within block will crash the entire program.
        :param block: either function or string of code
        :param iterations: number of times to run block
        :param args: any arguments that needs to be passed into block if block is a function
        """
        self.pause()

        # build string with function and needed variables
        string = ""

        if callable(block):
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
            string = block

        if string != "":
            self.resume()

            for i in range(iterations):
                exec(string)
                self.log()

    def log(self, message=""):
        """
        Log elapsed time. Will raise RuntimeWarning if timer is currently paused
        :param message: optional: store message with the log
        """
        if not self._paused:
            self._elapsed_times[len(self._elapsed_times) - 1].append(time() - self._running_time)
            self._logged_messages[len(self._logged_messages) - 1].append(str(message))
            self._running_time = time()
        else:
            raise RuntimeWarning("Timer Is Currently Paused: Log Had No Effect")

    def overall_time(self):
        """
        :return: Elapsed time since start()
        """
        return time() - self._start_time

    def pause(self):
        self._paused = True

    def reset(self):
        self._elapsed_times = [[]]
        self._logged_messages = [[]]
        self._split_messages = []

        self._start_time = time()
        self._running_time = time()
        self._paused = False

    def resume(self):
        self._paused = False
        self._running_time = time()

    def start(self):
        self._start_time = time()
        self._running_time = time()

    def split(self, message=""):
        self._split_messages.append(message)
        self._elapsed_times.append([])
        self._logged_messages.append([])
        self._running_time = time()
