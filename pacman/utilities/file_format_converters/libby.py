"""Function to convert RA and DEC in SEG format to decimal degrees
   O. Jones 22 Sep 2015
"""
__author__      = "Olivia Jones"

# Set the input and output files
filein = "/Users/ojones/goods_Gal.txt"
fileout = "/Users/ojones/goods_Gal_degree.txt"

# Inport the usefull python modules
from astropy.io import ascii
import numpy as np

# Function to convert RA in HH:MM:SS.SSS into decimal degrees:
def ra_hms_dd(hours, minutes, seconds):
    decimal = hours/15 + minutes/4.0 + seconds/240.0
    return decimal

# Function to convert +DD:MM:SS.SSS into decimal degrees:
def dec_dms_dd(degrees, minutes, seconds):
    if degrees >= 0:
        decimal = degrees + minutes/60.0 + seconds/3600.0
    else:
        decimal = degrees - minutes/60.0 - seconds/3600.0
    return decimal


# Read in the data
data = ascii.read(filein, header_start=None)

h  = data['col1']
m  = data['col2']
s  = data['col3']
dd = data['col4']
dm = data['col5']
ds = data['col6']

#Do the conversion for RA
radegree =[]
for i, hour in enumerate(h):
    radeg = ra_hms_dd(hour, m[i], s[i])
    radeg = np.round(radeg, 5)
    radegree.append(radeg)

# Do the conversion for Dec
decdegree = []
for j, deg in enumerate(dd):
    decdeg = dec_dms_dd(deg, dm[j], ds[j])
    decdeg = np.round(decdeg, 5)
    decdegree.append(decdeg)

# Write the output to a file
ascii.write([radegree, decdegree], fileout, names=['RA (deg)', 'Dec (deg)'],
            delimiter = '\t')
            #, formats = {'radegree': '%10.4f','decdegree': '%10.4f'})
