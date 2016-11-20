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


class PyTimer:
    def __init__(self, rounder=4):
        self.elapsed_times = [[]]
        self.logged_messages = [[]]
        self.split_messages = []

        self.start_time = 0
        self.running_time = 0
        self.rounding = rounder
        self.paused = False

    def __str__(self):
        # pretty print table
        string = []  # using list to speed up concatenation
        for i in range(len(self.elapsed_times)):  # for every split
            string.append("Split " + str(i + 1) + ":" if i >= len(self.split_messages) or self.split_messages[i] == ""
                          else self.split_messages[i])
            string.append("\n")
            for j in range(len(self.elapsed_times[i])):  # for every log in split
                string.append("\t")
                string.append(str(self._format_time(self.elapsed_times[i][j])) + (": {}".
                                                                                  format(self.logged_messages[i][j])
                                                                                  if self.logged_messages[i][j] != ""
                                                                                  else ""))
                string.append("\n")
            string.append("\n")

        return "".join(string)

    def _format_time(self, t):
        return round(t, self.rounding)

    def log(self, message=""):
        if not self.paused:
            self.elapsed_times[len(self.elapsed_times) - 1].append(time() - self.running_time)
            self.logged_messages[len(self.logged_messages) - 1].append(str(message))
            self.running_time = time()
        else:
            raise RuntimeWarning("Timer Is Currently Paused: Log Had No Effect")

    def overall_time(self):
        return time() - self.start_time

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.running_time = time()

    def start(self):
        self.start_time = time()
        self.running_time = time()

    def split(self, message=""):
        self.split_messages.append(message)
        self.elapsed_times.append([])
        self.logged_messages.append([])
        self.running_time = time()
