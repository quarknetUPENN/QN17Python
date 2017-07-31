import ast
import numpy as np
import os

os.chdir('data_2017-07-28_1719')

with open('thing.dum', 'r') as file:
    variable = ast.literal_eval(file.readline())
print(variable.keys())
