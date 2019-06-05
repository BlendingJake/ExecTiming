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

import logging


class LoggingInfoWrapper:
    """
    Provides a basic wrapper around logging.info to allow it to act like a file-like object to be used
    as an output stream in some of the functions below.
    """
    @staticmethod
    def write(message: str):
        """
        Write a message to logging.info. If the message ends with a newline, remove it, as logging.info adds that itself
        :param message: the string message to log
        """
        if message[-1] == "\n":
            logging.info(message[:-1])
        else:
            logging.info(message)


class LoggingDebugWrapper:
    """
    Provides a basic wrapper around logging.debug to allow it to act like a file-like object to be used
    as an output stream in some of the functions below.
    """
    @staticmethod
    def write(message: str):
        """
        Write a message to logging.info. If the message ends with a newline, remove it, as logging.info adds that itself
        :param message: the string message to log
        """
        if message[-1] == "\n":
            logging.debug(message[:-1])
        else:
            logging.debug(message)
