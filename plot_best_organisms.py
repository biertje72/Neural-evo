import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy

def running_mean(x, N):
    cumsum = numpy.cumsum(numpy.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

dir_path = "./organisms10x32x4"
paths = sorted(Path(dir_path).iterdir(), key=os.path.getmtime)
#fitnesses = [float(str(path).split("fit",1)[1][:4]) for path in paths]
splits1 = [str(path).split("fit",1)[1] for path in paths]
fitnesses = [float(split1.split("_",1)[0]) for split1 in splits1]
fitnesses2 = running_mean(fitnesses, 15)
#plt.plot(fitnesses)
#plt.ylabel('some numbers')
plt.plot(fitnesses2)
plt.ylabel('running mean')
plt.show()
