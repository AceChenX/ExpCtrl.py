# ALP4lib: A Python module to control Vialux DMDs
# https://github.com/wavefrontshaping/ALP4lib
# by Sébastien M. Popoff
import numpy as np
import ALP4
import time
from configparser import ConfigParser
config = ConfigParser()
config.read('config.ini')

# Load the Vialux .dll
DMD = ALP4(version = conf['dmd']['alp4ver'], libDir = conf['dmd']['alp4dir'])
# Initialize the device
DMD.Initialize()
# Binary amplitude image (0 or 1)
bitDepth = 1
imgBlack = np.zeros([DMD.nSizeY,DMD.nSizeX])
imgWhite = np.ones([DMD.nSizeY,DMD.nSizeX])*(2**8-1)
#imgSeq  = np.concatenate([imgBlack.ravel(),imgWhite.ravel()])

# Generate testing patterns
imgNum = 10
imgTime = 100000 # microsec
imgNew = np.zeros([DMD.nSizeY,DMD.nSizeX])
imgSeq = np.array([])
for i in range(imgNum):
    for x in range(DMD.nSizeX):
        for y in range(DMD.nSizeY):
            if ((x-i*100)**2 + (y-DMD.nSizeY//2)**2) < 2500:
                imgNew[y,x] = (2**8-1)
            else:
                imgNew[y,x] = 0

    imgSeq = np.concatenate([imgSeq, imgNew.ravel()])

# Allocate the onboard memory for the image sequence
DMD.SeqAlloc(nbImg = imgNum, bitDepth = bitDepth)
# Send the image sequence as a 1D list/array/numpy array
DMD.SeqPut(imgData = imgSeq)
# Set image rate
DMD.SetTiming(illuminationTime = imgTime)
# Show sequence is ready
print('Ready')
# Use ALP external trigger mode
DMD.Halt()
DMD.ProjControl(controlType=ALP_PROJ_MODE, value=ALP_MASTER)
DMD.ProjControl(controlType=ALP_PROJ_STEP, value=ALP_EDGE_RISING)
# Run the sequence
DMD.Run()
# Timeout
time.sleep(30)
# Stop the sequence display
DMD.Halt()
# Free the sequence from the onboard memory
DMD.FreeSeq()
# De-allocate the device
DMD.Free()
