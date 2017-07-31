from holder import *


with open('thing.dum', 'r') as file:
    exec("thing = "+file.readline())

