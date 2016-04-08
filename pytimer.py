#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

#Original Author = Jacob Morris

import timeit


class PyTimer:

    def __init__(self, rounder=4):
        self.elapsed_times = [[]]
        self.logged_times = [[]]
        self.logged_messages = [[]]
        self.split_messages = []

        self.start_time = 0
        self.stop_time = 0
        self.elapsed_counter = 0
        self.rounding = rounder

        self.__split_pos = 0

    def __str__(self):
        if self.stop_time == 0:
            return "Not Stopped, Current Running Time: " + str(round(timeit.default_timer() -
                                                                     self.start_time, self.rounding)) + " s"
        else:
            return "Total Time Recorded: " + str(round(self.stop_time - self.start_time, self.rounding)) + " s"

    # average all elapsed times together
    def average(self):
        total = 0
        count = 0

        for i in self.elapsed_times:
            for i2 in i:
                total += i2
                count += 1

        if count != 0:
            return round(total / count, self.rounding)
        else:
            return 0

    # return averages for each split
    def averages(self):
        averages = []

        for i in self.elapsed_times:
            total = 0
            count = 0

            for i2 in i:
                total += i2
                count += 1

            if count != 0:
                averages.append(round(total / count, self.rounding))
            else:
                averages.append(0)

        return averages

    def display(self):
        print(self.format())

    def display_last(self):
        print(self.format_last())

    def display_point(self, pos, split=0):
        print(self.format_point(pos, split))

    def display_split(self, split):
        print(self.format_split(split))

    def format(self):
        out = "Point, Time Since Start, Time Elapsed Between Points\n"

        for i in range(len(self.logged_times)):
            for i2 in range(len(self.logged_times[i])):
                out += self.logged_messages[i][i2] + ": "
                out += str(self.logged_times[i][i2]) + " s, "
                out += str(self.elapsed_times[i][i2]) + " s\n"

            # check for split
            if i < len(self.split_messages) > 0:
                out += "--Split: " + self.split_messages[i] + "--\n"

        return out

    def format_last(self):
        data = self.get_last()
        out = "Point, Time Since Start, Time Elapsed Between Points\n"

        out += data["message"] + ": "
        out += str(data["time"]) + " s, "
        out += str(data["elapsed"]) + " s\n"

        return out

    def format_point(self, pos, split=0):
        data = self.get_point(pos, split)
        out = "Point, Time Since Start, Time Elapsed Between Points\n"

        out += data["message"] + ": "
        out += str(data["time"]) + " s, "
        out += str(data["elapsed"]) + " s\n"

        return out

    def format_split(self, split):
        data = self.get_split(split)
        out = "Point, Time Since Start, Time Elapsed Between Points\n"

        for i in data:
            out += i["message"] + ": "
            out += str(i["time"]) + " s, "
            out += str(i["elapsed"]) + " s\n"

        return out

    def get_last(self):
        return self.get_point(len(self.logged_times[self.__split_pos - 1]) - 1, self.__split_pos - 1)

    # get point data at location [split][pos]
    def get_point(self, pos, split=0):
        if 0 <= split < len(self.logged_times):
            if 0 <= pos < len(self.logged_times[split]):
                return {"elapsed": self.elapsed_times[split][pos], "message": self.logged_messages[split][pos],
                        "time": self.logged_times[split][pos]}
            else:
                raise IndexError("Position value is invalid")
        else:
            raise IndexError("Split value is invalid")

    # get all points in split
    def get_split(self, split):
        if 0 <= split < len(self.logged_times):
            back = []

            for i in range(len(self.logged_times[split])):
                back.append({"elapsed": self.elapsed_times[split][i], "message": self.logged_messages[split][i],
                        "time": self.logged_times[split][i]})

            return back
        else:
            raise IndexError("Split value is invalid")

    def log(self, message=""):
        if self.start_time == 0:
            raise RuntimeError("Timer never started")

        if message == "":
            message += "Point " + str(self.number_points() + 1)

        time = round(timeit.default_timer() - self.start_time, self.rounding)

        self.logged_times[self.__split_pos].append(time)
        self.elapsed_times[self.__split_pos].append(round(time - self.elapsed_counter, self.rounding))
        self.logged_messages[self.__split_pos].append(str(message))

        self.elapsed_counter = time

    def number_points(self):
        count = 0

        for i in self.logged_times:
            count += len(i)

        return count

    def reset(self):
        self.__init__()

    def split(self, message=""):
        if self.start_time == 0:
            raise RuntimeError("Timer never started")

        self.elapsed_counter = 0
        self.split_messages.append(message)
        self.start_time = timeit.default_timer()

        self.logged_messages.append([])
        self.logged_times.append([])
        self.elapsed_times.append([])
        self.__split_pos += 1

    def start(self):
        self.start_time = timeit.default_timer()

    def stop(self):
        if self.start_time == 0:
            raise RuntimeError("Timer never started")

        self.log("Stop")
        self.stop_time = timeit.default_timer()

    # return total time from start to last logged point
    def total(self):
        if len(self.logged_times) >= 1:
            last_split = self.logged_times[len(self.logged_times) - 1]
            return last_split[len(last_split) - 1]
        else:
            return 0
