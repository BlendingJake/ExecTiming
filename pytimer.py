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
from os.path import sep as os_file_sep


class PyTimer(object):
    """
    PyTimer is a class for easily timing execution of sections of codes. PyTimer supports splitting
    to allow different segments of code to be timed separately.
    """
    seconds = 's'
    milliseconds = "ms"
    microseconds = "us"
    nanoseconds = "ns"

    rounding = 4
    _last_time = 0  # used for static elapsed method to know what time was on last call

    # static methods
    @staticmethod
    def _time():  # allow internal timer to be changed easily
        """
        Get the current time, currently perf_counter() because of its accuracy and that fact it returns values in 
        fractional seconds
        :return: a relative time, only good for telling elapsed times, in seconds
        """
        return perf_counter()

    @staticmethod
    def _convert_time(t: float, units="") -> [float, str]:
        """
        Internal method. Will determine the units if they are not specified and the value is within a certain range,
        or will convert to whatever units are specified.
        :param t: the time in seconds
        :param units: the units to convert to, automatically determined if none are specified
        :return: a list of [converted time, units], units are returned in case they weren't specified.
        """
        if (units == "" and t < 0.00000001) or units == PyTimer.nanoseconds:
            return [t * 1000000000, PyTimer.nanoseconds]
        elif (units == "" and t < 0.00001) or units == PyTimer.microseconds:
            return [t * 1000000, PyTimer.microseconds]
        elif (units == "" and t < 0.01) or units == PyTimer.milliseconds:
            return [t * 1000, PyTimer.milliseconds]
        else:
            return [t, PyTimer.seconds]

    @staticmethod
    def elapsed(message="", **kwargs):
        """
        Allows the elapsed time to be easily checked using repeated calls to this. There must be an initial call
        that gets the start time.
        :param message: a message to be displayed along with the elapsed time
        :param kwargs: the elapsed time in seconds can be returned instead of displayed using display=False
        :return: 
        """
        if PyTimer._last_time == 0:
            PyTimer._last_time = PyTimer._time()
        else:
            dif = PyTimer._time() - PyTimer._last_time

            if 'display' not in kwargs or ('display' in kwargs and kwargs['display']):
                converted = PyTimer._convert_time(dif)
                print(("{}: ".format(message) if message else "") + "{} {}".format(round(converted[0], 5),
                                                                                   converted[1]))
                PyTimer._last_time = PyTimer._time()  # update last
            else:
                PyTimer._last_time = PyTimer._time()  # update last
                return dif

    @staticmethod
    def time_block(block, *args, **kwargs):
        """
        A static method that allows timing a function or string of code without creating a PyTimer object
        :param block: either a callable, or a string
        :param args: any positional arguments to be passed into block if it is a function
        :param kwargs: any keyword arguments to be passed into block if it is a function, or reps/iterations. Where
        reps and iterations have their standard definitions.
        :return: The amount time it takes to call/evaluate block iterations times, averaged over reps runs. If block
        is neither a callable or a string, then None is returned
        """
        reps = 1
        if 'reps' in kwargs and isinstance(kwargs['reps'], int) and kwargs['reps'] > 0:
            reps = kwargs['reps']
            del kwargs['reps']

        iterations = 10
        if 'iterations' in kwargs and isinstance(kwargs['iterations'], int) and kwargs['iterations'] > 0:
            iterations = kwargs['iterations']
            del kwargs['iterations']

        running_total = 0
        is_function = callable(block)  # check if function or string outside of loop to help get a more accurate time

        # if block is neither a string or a callable
        if not is_function and not isinstance(block, str):
            return None

        for rep in range(reps):
            start_time = PyTimer._time()
            for iteration in range(iterations):
                if is_function:
                    block(*args, **kwargs)
                else:
                    eval(block)
            running_total += PyTimer._time() - start_time

        average = running_total / reps
        return average

    def __init__(self, *args, **kwargs):
        """
        Create timer object, start() is called automatically unless args[0] is False
        :param args: args[0] should be a bool that tells whether or not to automatically
        :param kwargs: in (round, run, collect, display, units), where round is the number of decimal places to round
        to, run is whether or not to start the timer as soon as it is created, collect tells whether or not to collect
        output statements so they can later be written to a file, display tells whether or not to display output, 
        and finally, units tells what units to use when displaying times
        """

        self._elapsed_times = [[]]
        self._logged_messages = [[]]
        self._split_messages = []
        self._collected_output = []

        self._start_time = 0
        self._running_time = 0
        self._decorator_reps = 1
        self._decorator_iterations = 10
        self._units = ""

        self._paused = False
        self._started = False
        self._run = True
        self._collect_output = False
        self. _display = True

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
                strings.append(self._format_split(i, False))

            return "".join(strings)
        else:
            return ""

    def _confirm_started(self):
        """
        Called by most methods to start out with, confirm that timer has been started. Can lead to issues, because
        timer might not be started until log() is called, meaning that the elapsed time is 0
        """
        if not self._started and self._run:
            self.start()

    def _format_time(self, t: float) -> str:
        """
        Format time into strings with correct units
        :param t: the time in seconds to be formatted
        :return: the string of a time converted to the correct units and then the abbreviation for those units
        """
        if self._run:
            converted = PyTimer._convert_time(t, self._units)
            return str(round(converted[0], self.rounding)) + " {}".format(converted[1])

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
                str_list.append("\t-- Empty Split --\n")
            if newline:
                str_list.append("\n")

            return "".join(str_list)

    def _parse_kwargs_reps_iter(self, kwargs: dict, rep_default: int, iter_default: int):
        """
        Checks kwargs for reps and iterations and makes sure they are the correct type and >= 1, if either aren't then
        their default value is returned
        :param kwargs: dictionary of values
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
            del kwargs['reps']

        iterations = iter_default
        if 'iterations' in kwargs:
            if isinstance(kwargs['iterations'], int) and kwargs['iterations'] >= 1:
                iterations = kwargs['iterations']
            elif isinstance(kwargs['iterations'], int) and kwargs['iterations'] <= 0:
                self._write("Iterations cannot be less than 1\n")
            else:
                self._write("Iterations must be an integer value\n")
            del kwargs['iterations']

        return reps, iterations

    def _valid_split(self, i: int) -> bool:
        """
        Determines if the split index is valid
        :param i: split index to check 
        :return: true or false depending on whether or not the split is valid
        """
        if self._run:
            return len(self._split_messages) > 0 and 0 <= i < len(self._split_messages) and \
                       self._split_messages[i] != ""

    def _write(self, *args):  # write to console if _display, add to collected outputs if _collect_output
        """
        Write to either the console if _display, add output to collected outputs if _collect_output, write newline
        if now parameters are provided
        :param args: string to be written, only 0 or 1 is accepted
        """
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
        if self._run and not self._paused:
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
        elif self._paused:
            self._write("Timer is currently paused\n")

    def averages(self) -> list:
        """
        Returns list of averages for every split
        :return: list of averages, if position i is invalid, then list[i] is None
        """
        if self._run and not self._paused:
            return [self.average(i) for i in range(len(self._elapsed_times))]
        elif self._paused:
            self._write("Timer is currently paused\n")
            return []
        else:
            return []

    def decorator(self, func: callable) -> callable:
        """
        Returns a decorator so that functions can be timed with having to use evaluate, but functions can't take any
        parameters
        :param func: takes a function as a parameter
        :return: a wrapper function for use as a decorator
        """
        self._confirm_started()

        def wrapper(*args, **kwargs):
            """
            wrapper returned when using as decorator
            :param args: (optional) values to be passed into function that is being called
            """
            if self._run and not self._paused:  # if the timer is not running, then just call the function
                arguments = [str(i) for i in args]
                for i in kwargs.keys():
                    arguments.append("{}={}".format(i, kwargs[i]))

                val = None
                for i in range(self._decorator_iterations):
                    for j in range(self._decorator_reps):
                        val = func(*args, **kwargs)
                    self.log()
                self.split("{}({}) - Decorator ({} reps)".format(func.__name__, ", ".join(arguments),
                                                                 self._decorator_reps))

                return val  # make sure value gets returned
            elif self._paused:
                self._write("Timer is currently paused\n")
            else:
                return func(*args, **kwargs)
        return wrapper

    def deviation(self, i: int):
        """
        Calculates standard deviation for split i
        :param i: split index
        :return: None if split i is empty, False if invalid index, otherwise returns standard deviation of split i
        """
        if self._run and not self._paused:
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
        elif self._paused:
            self._write("Timer is currently paused\n")

    def deviations(self) -> list:
        """
        Calculates standard deviations for every split
        :return: list of standard deviations for all splits. If split i is empty, than list[i] is None
        """
        if self._run and not self._paused:
            return [self.deviation(i) for i in range(len(self._elapsed_times))]
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_average(self, i: int):
        """
        Display average for split i if valid index and split is not empty, otherwise displays appropriate message
        :param i: split index
        """
        if self._run and not self._paused:
            num = self.average(i)
            if num is not None and not isinstance(num, bool):
                self._write(("Split " + str(i) if not self._valid_split(i) else self._split_messages[i]) +
                            ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " + self._format_time(num) +
                            "\n")
            elif num is None:
                self._write(self._format_split(i, False))
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_averages(self):
        """
        Display averages for all splits unless split i is empty, in which case it is skipped
        """
        if self._run and not self._paused:
            av = self.averages()
            for i in range(len(av)):
                if av[i] is not None:
                    self._write(("Split " + str(i) if not self._valid_split(i) else self._split_messages[i]) +
                                ":\n\tAverage (" + str(len(self._elapsed_times[i])) + " runs): " +
                                self._format_time(av[i]))

            if len(av) > 0 and av[0] is not None:  # add final newline
                self._write()
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_deviation(self, i: int):
        """
        Display standard deviation for split i if valid index and split is not empty, otherwise displays appropriate
        message
        :param i: split index
        """
        if self._run and not self._paused:
            dev = self.deviation(i)
            if dev is not None and not isinstance(dev, bool):
                self._write(("Split " + str(i) if not self._valid_split(i) else self._split_messages[i]) +
                            ":\n\tStandard Deviation: " + self._format_time(dev) + "\n")
            elif dev is None:
                self._write(self._format_split(i, False))
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_deviations(self):
        """
        Display standard deviation for all splits unless split is empty, in which case that split is skipped
        """
        if self._run and not self._paused:
            devs = self.deviations()
            for i in range(len(devs)):
                if devs[i] is not None:
                    self._write(("Split " + str(i) if not self._valid_split(i) else self._split_messages[i]) +
                                ":\n\tStandard Deviation: " + self._format_time(devs[i]))

            if len(devs) > 0 and devs[0] is not None:  # add newline
                self._write()
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_overall_time(self):
        """
        Display time since last start() or reset(). This time includes that time taken to execute PyTimer method calls
        """
        if self._run and not self._paused:
            self._confirm_started()
            self._write("Overall Time: {}\n".format(self._format_time(self._time() - self._start_time)))
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_split(self, i: int):
        """
        Display all values in split i if valid index and split is not empty, otherwise displays appropriate message
        :param i: split index
        """
        if self._run and not self._paused:
            self._confirm_started()
            if 0 <= i < len(self._elapsed_times) and len(self._elapsed_times[i]) > 0:
                self._write(self._format_split(i, False))
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))
        elif self._paused:
            self._write("Timer is currently paused\n")

    def display_splits(self):
        """
        Display all values for all splits unless split is empty, in which case the split is skipped
        """
        if self._run and not self._paused:
            self._confirm_started()
            for i in range(len(self._elapsed_times)):
                if len(self._elapsed_times[i]) > 0:  # make sure split is not empty
                    self.display_split(i)
        elif self._paused:
            self._write("Timer is currently paused\n")

    def time_it(self, block, *args, **kwargs):
        """
        Evaluates a string of code or a function and times how long it takes for each iteration. If block is a function,
        then parameters can be passed to it like so: evaluate(bar, "something", 12, iterations=100) ->
        bar("something", 12). No error checking is done, meaning any error that is raised within block will crash
        the entire program.
        :param block: either function or string of code
        :param args: any arguments that needs to be passed into block if block is a function
        :param kwargs: can be in (reps, iterations, message) which have their usual definition, or they can be any
        argument that should be passed into block if block is a function
        """
        if self._run and not self._paused:
            self._confirm_started()
            self.pause()

            reps, iterations = self._parse_kwargs_reps_iter(kwargs, 10, 10)
            split_message = kwargs['message'] if 'message' in kwargs else ""

            if callable(block):
                if not split_message:  # if no message was passed in
                    arguments = [str(i) for i in args]
                    for i in kwargs.keys():
                        arguments.append("{}={}".format(i, kwargs[i]))

                    split_message = "{}({}) - Evaluate Function ({} reps)".format(block.__name__, ", ".join(arguments),
                                                                                  reps)

                self.resume()
                for i in range(iterations):
                    for j in range(reps):
                        block(*args, **kwargs)
                    self.log()
                self.split(message=split_message)
            elif isinstance(block, str):
                if not split_message:  # if not message was passed in
                    if len(block) > 50:  # shorten string if really long
                        split_message = "'{}'... - Evaluate String ({} reps)".format(block[0:50], reps)
                    else:
                        split_message = "'{}' - Evaluate String ({} reps)".format(block, reps)

                self.resume()
                for i in range(iterations):
                    for j in range(reps):
                        exec(block)
                    self.log()
                self.split(message=split_message)
            else:
                self.resume()
                self._write("Block is not callable or a string\n")
        elif self._paused:
            self._write("Timer is currently paused\n")

    def log(self, message=""):
        """
        Log elapsed time, log will have no affect if timer is paused
        :param message: optional: store message with the log
        """
        if self._run and not self._paused:
            self._confirm_started()
            if not self._paused:
                self._elapsed_times[len(self._elapsed_times) - 1].append(self._time() - self._running_time)
                self._logged_messages[len(self._logged_messages) - 1].append(str(message))
                self._running_time = self._time()
            else:
                self._write("Timer is currently paused: log had no affect\n")
        elif self._paused:
            self._write("Timer is currently paused\n")

    def overall_time(self) -> float:
        """
        :return: Elapsed time since start() in seconds, includes time to execute PyTimer method calls
        """
        if self._run and not self._paused:
            self._confirm_started()
            return self._time() - self._start_time
        elif self._paused:
            self._write("Timer is currently paused\n")
            return 0

    def pause(self):
        """
        Pause the timer, meaning no actions can be performed, allows portions of code to be skipped
        """
        if self._run:
            if not self._paused:
                self._confirm_started()
                self._paused = True
            else:
                self._write("Timer is already paused\n")

    def reset(self):
        """
        Clear the timer back to its defaults
        """
        if self._run:
            self._elapsed_times = [[]]
            self._logged_messages = [[]]
            self._split_messages = []

        self._paused = False
        self.start()

    def resume(self):
        """
        Resume the timer from being paused, updates the internal clock to the current time
        """
        if self._run:
            self._confirm_started()

            if self._paused:
                self._paused = False
                self._running_time = self._time()
            else:
                self._write("Timer is not currently paused\n")

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
        if self._run and not self._paused:
            self._confirm_started()
            self._split_messages.append(message)
            self._elapsed_times.append([])
            self._logged_messages.append([])
            self._running_time = self._time()
        elif self._paused:
            self._write("Timer is currently paused\n")

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
        if self._run and not self._paused:
            self._confirm_started()
            if 0 <= i <= len(self._elapsed_times[i]):
                return self._elapsed_times[i]
            else:
                self._write("Invalid split index, must be in [0-{}]\n".format(len(self._elapsed_times) - 1))
                return None
        elif self._paused:
            self._write("Timer is currently paused\n")

    def write_output(self, folder_path: str, basename: str, file_per_run=False):
        """
        Write all collected output to a file, assuming that _collect_output was set in constructor. File is either
        written to folder_path + basename if file_per_run is false or folder_path + basename + date_time where
        date_time is formatted "-day-month-year-hours-minutes-seconds". All files are written to .txt format
        :param folder_path: Path of folder to write to
        :param basename: Name of file
        :param file_per_run: Create a new file with every run
        """
        if not self._collect_output and self._run and not self._paused:
            self._write("Timer was not set to save output, to do so: PyTimer(save_output=True)\n")

        if self._collect_output and self._run and not self._paused:
            if file_per_run:  # determine file path, if file_per_run, then use date and time on top of basename
                time_name = datetime.today().strftime("-%d-%m-%Y-%H-%M-%S")
                fp = folder_path + os_file_sep + basename + time_name + ".txt"
            else:
                fp = folder_path + os_file_sep + basename + ".txt"

            try:
                file = open(fp, 'w')
                file.write(datetime.today().strftime("Saved on %B %d, %Y at %I:%M:%S %p\n\n"))

                for line in self._collected_output:
                    file.write(line)
                file.close()

                if self._display:
                    self._write("File written to '{}'\n".format(fp))
            except PermissionError:
                self._write("Could not write to file path '{}'\n".format(fp))
        elif self._paused:
            self._write("Timer is currently paused\n")
