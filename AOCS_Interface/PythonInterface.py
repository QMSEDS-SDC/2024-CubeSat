import ctypes
import pandas as pd

# File Path To .so File (Not sure what final path is gonna be but just enter cpplib.so path) 
# (Also make sure to only use forward slashes for the path otherwise it doesn't work)
library = ctypes.CDLL("placeholder.so")

# Assigns C++ Function To Python Function
mainpy = library.main

# Specifies Argument DataType
mainpy.argtypes = [ctypes.c_double]

# Read CSV
df = pd.read_csv('your_file.csv')

# Retrieve Value (Note: Edit This To Get Correct Value From CSV)
value = df.iloc[1, 2]  

# Run FUnction
mainpy(value)
