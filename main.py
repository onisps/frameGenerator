import numpy as np
from utils.drawLine import drawLine
from utils.shapeGenerator import generateBasicLine

if __name__ == '__main__':
    arr = generateBasicLine(10, 2,1)
    #print(arr.T)
    drawLine(arr)