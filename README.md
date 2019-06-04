# PyTimer
> An advanced timer for Python that makes it easy to determine execution times.

Python has a built-in package named `timeit` which provides a way to
"Measure execution time of small code snippets." It can be great for quick
tests, but lacks more expansive features like curve fitting, statistical information,
and the ability to use in existing projects. PyTimer seeks to change that by
including most of the features of `timeit` and adding many more like decorators,
argument calling and replacement, best-fit-curve determination, and in-project use.

## Features
 * `StaticTimer` which provides the ability to time functions via a decorator,
 strings, or just seeing the amount of time elapsed between a call to `.start_elapsed()` and `elapsed()`
 * `Timer` which gives a way to log measured times and then display statistical data,
 perform curve-fitting for functions with parameters as the independent variables and
 the measured time as the dependent variable, and all the features the StaticTimer has.
 * All output can be re-directed by changing `output_stream`, which can be any
 file-like object or anything with a `.write()` method.
 * A wrapper for `logging.info` and `logging.debug` is included to redirect
 output to those sources
 * Measured times can be displayed in seconds `s`, milliseconds `ms`,
 microseconds `us`, or nanoseconds `ns`.
 * The same block can be executed multiple times to get a more accurate reading.
 This is done by setting `iterations_per_run`. After that many iterations, the
 elapsed time is measured.
 * Multiple runs can be carried out and averaged to remove outlying results.


### Static decorate:
```
from pytimer.timer import StaticTimer
from random import randint

@StaticTimer.decorate(runs=5, average_runs=False, call_callable_args=True, log_arguments=True)
def factorial(n):
    if n == 1:
        return 1
    else:
        return n * factorial.__wrapped__(n-1)

factorial(lambda: randint(3, 40))

#    0.01663 ms - factorial(33) ... [runs=  1, iterations=  1] | Run 1
#    0.00544 ms - factorial(19) ... [runs=  1, iterations=  1] | Run 2
#    0.00736 ms - factorial(28) ... [runs=  1, iterations=  1] | Run 3
#    0.00448 ms - factorial(17) ... [runs=  1, iterations=  1] | Run 4
#    0.01087 ms - factorial(38) ... [runs=  1, iterations=  1] | Run 5
```

 * Functions, even recursive ones, can be wrapped so that any time they are called they get timed
 * You can replace arguments with functions which can be automatically called and the argument replaced
 to allow testing like shown above, `call_callable_args=True`
 * Arguments show up in the output to provide more information, `log_arguments=True`

### Static time_it:
```
from pytimer.timer import StaticTimer

StaticTimer.time_it("pow(2, 64)", runs=5, iterations_per_run=10000)
# 102.40978 ms - pow(2, 64) ... [runs=  5, iterations=10000]

StaticTimer.time_it("2**64", runs=5, iterations_per_run=10000)
#  77.39217 ms - 2**64    ...   [runs=  5, iterations=10000]
```

 * Strings can be timed
 * Multiple runs can be measured then averaged together to get a more accurate result
 * Any needed `globals` or `locals` can be specified by passing `globals=` and `locals=`

 `time_it` can be used to re-write the decorator above example like so:
 ```
 StaticTimer.time_it(factorial, lambda: randint(3, 40), call_callable_args=True, average_runs=False, runs=5, log_arguments=True)
 ```

### Transformers, statistics, and best fit:
```
from pytimer.pytimer import Timer

timer = Timer()

@timer.decorate(runs=5, log_arguments=True, call_callable_args=True)
def bubble_sort(array):
    # print(len(array))

    while True:
        switched = False
        for i in range(0, len(array)-1):
            if array[i] > array[i+1]:
                array[i], array[i+1] = array[i+1], array[i]
                switched = True

        if not switched:
            break

    return array

bubble_sort(lambda: [randint(0, 1000) for _ in range(randint(100, 5000))])

timer.output(split_index="bubble_sort", transformers={0: len})
# bubble_sort:
#     1360.32880 ms - bubble_sort(3004) ... [runs=  1, iterations=  1]
#      726.70468 ms - bubble_sort(2201) ... [runs=  1, iterations=  1]
#     3313.44760 ms - bubble_sort(4692) ... [runs=  1, iterations=  1]
#      562.01346 ms - bubble_sort(1947) ... [runs=  1, iterations=  1]
#      200.57170 ms - bubble_sort(1169) ... [runs=  1, iterations=  1]

timer.statistics()
# bubble_sort:
#     Runs                5
#     Total Time          6163.06623 ms
#     Average             1232.61325 ms
#     Standard Deviation  1106.06873 ms
#     Variance            1223.38803 ms

timer.best_fit_curve(transformers={0: len})
# ('Polynomial', {'b': -0.013786, 'x^0': 0.0, 'x^1': 0.0000066066, 'x^2': 0.000000149})
```

 * `Timer` stores the output until requested
 * Function parameters can be transformed in the output. In the above example,
 `transformers={0: len}` indicates that the positional argument at index `0` should have its
 value in the output replaced by the result of calling the function with that parameter.
 The output otherwise would have been something like `bubble_sort([1, 2, 3, 4, 5, ...])`
 * Basic statistics can be displayed
 * A best-fit-curve can be determined. To use this, all logged function parameters
 must be integers. In this case, one was an a list, so it was transformed so that the
 analysis was done on the length of the list, instead of the list itself.
 * The resulting best fit curve is, if `n=len(list)`, `y = b + x^0*n^0 + x^1*n^1 + x^2*n^2`, where
 `x^2*n^2` is the coefficient `x^2` multiplied by n-squared. We can extrapolate
 using this curve to determine what the execution time of a list of list of
 length `n=10000`, which would be `-0.013786 + 0.0000066066*10000 + 0.000000149*10000^2`.
 That is `15.028 s` or `15028 ms`

## TODO
 - [ ] Make scipy, numpy, and scikit-learn optional, just prohibit `best_fit_curve` if they aren't there
 - [ ] Add graphing feature with matplotlib, Linear will only be graphed if there is a single argument
 - [ ] Add the ability to sort runs so they are display in some sort of order. Maybe allow sorting
 by time or by an argument
