# PyTimer
An advanced timer for Python that makes it easy to determine execution times. 
Notable features include: easy splitting, calculation of averages and standard deviation, displaying formatted views of collected data, and evaluation of functions and code in strings.

Quick Start:
    
    from pytimer import PyTimer
    timer = PyTimer()
    for run in range(100):
   
        temp = ""
        
        for i in range(1000):
        
            temp += str(i)
            
        timer.log()
        
    timer.display_average(0)
