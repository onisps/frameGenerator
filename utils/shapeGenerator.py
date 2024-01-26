import numpy as np


def cart2pol(x, y, z):
    theta = np.arctan2(y, x)
    rho = np.sqrt(x ** 2 + y ** 2)
    return theta, rho, z


def pol2cart(theta, rho, z):
    x = rho * np.cos(theta)
    y = rho * np.sin(theta)
    return x, y, z


# flat - width = 2*size, height = sqrt*size

def rotate(arr, theta, rot_axis='z'):
    s = np.sin(theta)
    c = np.cos(theta)
    if rot_axis.lower() == 'x':
        mat = np.array(([1, 0, 0],
                        [0, c, -s],
                        [0, c, s]))
    elif rot_axis.lower() == 'y':
        mat = np.array(([c, 0, s],
                        [0, 1, 0],
                        [-s, 0, c]))
    elif rot_axis.lower() == 'z':
        mat = np.array(([c, -s, 0],
                        [s, c, 0],
                        [0, 0, 1]))
    else:
        print(f'\tshapeGenerator::rotate > only \'x\' or \'y\' or \'z\' are allowed. You are entered {type}')
        raise f'\tshapeGenerator::rotate > only \'x\' or \'y\' or \'z\' are allowed. You are entered {type}'
    return np.dot(mat, arr)


def createHex(rot_angle, lift, size, rho, type='flat'):
    def a(val2):
        return np.arctan2(rho, val2)

    if type.lower() == 'flat':
        height = np.sqrt(3) * size
        thetas = np.array([a(0.5 * size), a(1.5 * size), a(2 * size),
                           a(1.5 * size), a(0.5 * size), a(0 * size), a(0.5*size)], dtype='float32')
        rhos = np.array([rho, rho, rho, rho, rho, rho, rho], dtype='float32')
        zs = np.array([0, 0, 0.5 * height, height, height, 0.5 * height, 0], dtype='float32')
        hex = pol2cart(thetas, rhos, zs + lift)
    elif type.lower() == 'pointy':
        height = 2 * size
        thetas = np.array([a(0, 0.5 * size), a(0, 1.5 * size), a(0.5 * height, 2 * size),
                           a(height, 1.5 * size), a(0.5 * size), a(0.5 * height, 0)], dtype='float32')
        rhos = np.array([rho, rho, rho, rho, rho, rho], dtype='float32')
        zs = np.array([0, 0, 0.5 * height, height, height, 0.5 * height], dtype='float32')
        hex = pol2cart(thetas, rhos, zs)

    else:
        print(f'\tshapeGenerator::createHex > only \'flat\' or \'pointy\' are allowed. You are entered {type}')
        raise f'\tshapeGenerator::createHex > only \'flat\' or \'pointy\' are allowed. You are entered {type}'
    if rot_angle > 0:
        hex = rotate(hex, rot_angle)
    return hex


def generateBasicLine(RAD=10, layer_count=2, size=None, hex_count=None):

    if not bool((size == None) + (hex_count == None)):
        print('\tshapeGenerator:generateBasicLine > one of \'size\' or \'hex_count\' sould be given')
        raise '\tshapeGenerator:generateBasicLine > one of \'size\' or \'hex_count\' sould be given'

    hex_count = 21 #(2*np.pi*rho)/size

    height = np.sqrt(3) * size
    hex = list()
    for layer in range(layer_count):
        iter_bounce = False
        for i in range(int(hex_count)):
            hex.append(np.array(
                createHex(i * np.arctan2(1.5 * size, RAD), layer * height + int(iter_bounce) * size, size, RAD),
                dtype='float32'))
            iter_bounce = not iter_bounce

    return hex
