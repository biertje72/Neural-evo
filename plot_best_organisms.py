import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy

plt.rcParams["figure.figsize"] = (15,3)

def running_mean(x, N):
    cumsum = numpy.cumsum(numpy.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

dir_path = "./organisms10x64x4"
paths = sorted(Path(dir_path).iterdir(), key=os.path.getmtime)
#fitnesses = [float(str(path).split("fit",1)[1][:4]) for path in paths]
splits1 = [str(path).split("fit",1)[1] for path in paths]
fitnesses = [float(split1.split("_",1)[0]) for split1 in splits1]
plt.plot(fitnesses, 'r+')
plt.ylabel('fitnesses')

filtered_fitnss = running_mean(fitnesses, 50)
#plt.ylabel('some numbers')
plt.plot(filtered_fitnss)
plt.ylabel('running mean')
plt.grid(True)
plt.show()
