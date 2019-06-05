# ExecTiming
> An advanced timer for Python that makes it easy to determine execution times.

Python has a built-in package named `timeit` which provides a way to
"Measure execution time of small code snippets." It can be great for quick
tests, but lacks more expansive features like curve fitting, statistical information,
and the ability to use in existing projects. ExecTiming seeks to change that by
including most of the features of `timeit` and adding many more like decorators,
argument calling and replacement, best-fit-curve determination, and in-project use.

![Imgur Image](https://imgur.com/cJ62w1Z.png)

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

# [Wiki](https://github.com/BlendingJake/ExecTiming/wiki)

## Glossary
 * [`Installation`](#install)
 * [`Decorator`](#decorate)
 * [`Time Strings`](#time_it)
 * [`Statistics & Best Fit Curve`](#statistics_best_fit)
 * [`Plotting`](#plotting)

### <a name="install">Installation</a>
```
pip install exectiming
```
For full functionality:

 * `scipy`
 * `scikit-learn`
 * `numpy`
 * `matplotlib`

However, basic functionality will still exist even if those dependencies aren't found


### <a name="decorate">Static decorate</a>
```python
from exectiming.exectiming import StaticTimer
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

### <a name="time_it">Static time_it</a>
```python
from exectiming.exectiming import StaticTimer

StaticTimer.time_it("pow(2, 64)", runs=5, iterations_per_run=10000)
# 102.40978 ms - pow(2, 64) ... [runs=  5, iterations=10000]

StaticTimer.time_it("2**64", runs=5, iterations_per_run=10000)
#  77.39217 ms - 2**64    ...   [runs=  5, iterations=10000]
```

 * Strings can be timed
 * Multiple runs can be measured then averaged together to get a more accurate result
 * Any needed `globals` or `locals` can be specified by passing `globals=` and `locals=`

 `time_it` can be used to re-write the decorator above example like so:
 ```python
 StaticTimer.time_it(factorial, lambda: randint(3, 40), call_callable_args=True, average_runs=False, runs=5, log_arguments=True)
 ```

### Assume
```python
from exectiming.exectiming import Timer
timer = Timer()
```


### <a name="statistics_best_fit">Transformers, statistics, and best fit</a>
```python
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

### <a name="plotting">Plotting factorial</a>
```python
@timer.decorate(runs=100, iterations_per_run=10, call_callable_args=True, log_arguments=True)
def factorial(n):
    if n == 1:
        return 1
    else:
        return n * factorial.__wrapped__(n-1)

factorial(lambda: randint(1, 100))
timer.plot(plot_curve=True, time_unit=timer.US, equation_rounding=5)
```
![Imgur Image](https://i.imgur.com/c00v9OB.png)

 * `.plot()` provides a quick way to plot the measured times against an argument
 that is the independent variable
 * The best fit curve and equation can be automatically determined and added
 by setting `plot_curve=True`

### Plotting bubble_sort
```python
# using bubble_sort from above, just with runs=10

bubble_sort(lambda: [randint(0, 100) for _ in range(randint(100, 2500))])
curve = timer.best_fit_curve(transformers={0: len})
timer.plot(transformer=len, plot_curve=True, curve=curve, x_label="List Length")
```
![Imgur Image](https://imgur.com/cJ62w1Z.png)

 * The curve can be determined beforehand and then passed into `plot()`
 * `plot()` needs `transformer=len` because the independent and dependent variables
 must be integers, so `len` is used to make it it one

### Plotting binary_search
```python
@timer.decorate(runs=100, iterations_per_run=5, log_arguments=True, call_callable_args=True)
def binary_search(sorted_array, element):
    # print(len(sorted_array))

    lower, upper = 0, len(sorted_array)
    middle = upper // 2

    while middle >= lower and middle != upper:
        if element == sorted_array[middle]:
            return middle
        elif element > sorted_array[middle]:
            lower = middle + 1  # lower must be beyond middle because the middle wasn't right
        else:
            upper = middle - 1  # upper must be lower than the middle because the middle wasn't right

        middle = (upper + lower) // 2

    return None  # couldn't find it

binary_search(lambda: [i for i in range(randint(0, 10000))], lambda: randint(0, 10000))
timer.plot(plot_curve=True, curve=timer.best_fit_curve(exclude_args={1}, transformers={0: len}), key=0,
           transformer=len, time_unit=timer.US, x_label="List Length", equation_rounding=4,
           title="Binary Search - Random Size, Random Element")
```
![Imgur Image](https://imgur.com/a9kNtL9.png)

 * `binary_search()` takes two arguments, so `best_fit_curve` is set to ignore
 the second one, at index 1, and to transform the argument at index 0 using `len`
 * Once the curve is determined, the split must be plotted. Again, there are
 two arguments, so `key=0` says to use the first as the independent variable and
 `transformer=len` will transform the list into an integer
 * Additionally, the title and x-axis labels are specified and rounding set lower

## TODO
 - [x] Make scipy, numpy, and scikit-learn optional, just prohibit `best_fit_curve` if they aren't there
 - [x] Add graphing feature with matplotlib, Linear will only be graphed if there is a single argument
 - [x] Add the ability to sort runs so they are display in some sort of order. Maybe allow sorting
 by time or by an argument
