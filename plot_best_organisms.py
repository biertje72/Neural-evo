import os
from pathlib import Path
import matplotlib.pyplot as plt

dir_path = "C:/AzureSandbox/MY_STUFF/NeuralEvolution/organisms"
paths = sorted(Path(dir_path).iterdir(), key=os.path.getmtime)
fitnesses = [int(str(path).split("fit",1)[1][:3]) for path in paths]
    
plt.plot(fitnesses)
plt.ylabel('some numbers')
plt.show()
