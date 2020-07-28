""" FIle to add all modules which contains operations """

from . import cleaner, dateoperations, discretize, dropcols, duplicate, extractseries, \
    fill, index, input, join, onehotencoder, utils, remove_nan, rename, replacevalues, scaling, \
    typeconversions, output

ops = [cleaner, dateoperations, discretize, dropcols, duplicate, extractseries,
       fill, index, join, onehotencoder, utils, remove_nan, rename, replacevalues, scaling,
       typeconversions, input, output]
