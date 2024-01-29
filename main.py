import numpy as np
from utils.drawLine import drawLine
from utils.shapeGenerator import generateBasicLine

if __name__ == '__main__':
    arr = generateBasicLine(RAD=10, layer_count=1, size=2, hex_type='flat')
    #print(arr.T)
    drawLine(arr)