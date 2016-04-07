import timeit


class PyTimer:

    def __init__(self, round=4):
        self.elapsed_counter = 0
        self.elapsed_times = []
        self.logged_times = []
        self.logged_messages = []
        self.start_time = 0
        self.rounding = round

    def __str__(self):
        out = "Point, Time Since Start, Time Elapsed Between Points\n"

        for i in range(len(self.logged_times)):
            if self.logged_times[i] is not None:
                out += self.logged_messages[i] + ": "
                out += str(self.logged_times[i]) + " s, "
                out += str(self.elapsed_times[i]) + " s\n"
            else:
                out += str("--Split--\n")

        return out

    def start(self):
        self.start_time = timeit.default_timer()

    def stop(self):
        self.log("Stop")

    def log(self, message=""):
        if message == "":
            message += "Point " + str(len(self.logged_times) + 1)

        time = round(timeit.default_timer() - self.start_time, self.rounding)

        self.logged_times.append(time)
        self.elapsed_times.append(round(time - self.elapsed_counter, self.rounding))
        self.logged_messages.append(str(message))

        self.elapsed_counter = time

    def split(self, message=""):
        self.logged_times.append(None)
        self.elapsed_times.append(None)
        self.logged_messages.append(str(message))
        self.elapsed_counter = 0
        self.start_time = timeit.default_timer()

    def average(self):
        running_total, counted = 0, 0

        for i in self.elapsed_times:
            if i is not None:
                running_total += i
                counted += 1

        return round(running_total / counted, self.rounding)

    def averages(self):
        averages = []
        running_total, counted = 0, 0

        for i in self.elapsed_times:
            if i is not None:
                running_total += i
                counted += 1
            else:
                averages.append(round(running_total / counted, self.rounding))
                running_total, counted = 0, 0

        # add last part average
        if counted != 0:
            averages.append(round(running_total / counted, self.rounding))

        return averages

    def total(self):
        total_time = 0

        for i in self.logged_times:
            if i is not None:
                total_time += (i - self.start_time)

        return total_time

    def number_points(self):
        return len(self.logged_times)

    def get_point(self, pos):
        if 0 <= pos < self.number_points():
            return self.logged_times[pos]
        else:
            raise IndexError
