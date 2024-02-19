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


def calculate_normal_vectors(points):
    # Calculate the tangent vectors for each point
    tangents = np.diff(points, axis=0)
    # Normalize the tangent vectors to get the direction vectors
    directions = tangents / np.linalg.norm(tangents, axis=1)[:, np.newaxis]
    # Calculate the normal vectors by rotating the direction vectors 90 degrees
    normals = np.zeros_like(points)

    normals[1:-1] = np.cross(directions[:-1], directions[1:])  # Cross product for inner points
    normals[0] = np.cross(directions[0], directions[0] - directions[1])  # Special case for first point
    normals[-1] = np.cross(directions[-1], directions[-1] - directions[-2])  # Special case for last point
    return normals


def create_offset(points, thickness):
    # Calculate the normal vectors for each point
    normals = calculate_normal_vectors(points)
    # Normalize the normal vectors
    unit_normals = normals / np.linalg.norm(normals, axis=1)[:, np.newaxis]
    # Scale the normal vectors by the thickness
    offset_vectors = unit_normals * thickness
    # Add the offset vectors to the original points to create the offset
    offset_points = points + offset_vectors
    return offset_points


def createHex(rot_angle, lift, size, rho, type='flat'):
    def a(val2):
        return np.arctan2(rho, val2)

    if type.lower() == 'flat':
        height = np.sqrt(3) * size
        thetas = np.array([a(0.5 * size), a(1.0 * size), a(1.5 * size),
                           a(1.0 * size), a(0.5 * size), a(0 * size), a(0.5 * size)], dtype='float32')
        rhos = np.array([rho, rho, rho, rho, rho, rho, rho], dtype='float32')
        zs = np.array([0, 0, 0.5 * height, height, height, 0.5 * height, 0], dtype='float32')
        hex = pol2cart(thetas, rhos, zs + lift)
    elif type.lower() == 'pointy':
        height = 2 * size
        thetas = np.array(([a(0.5 * size), a(1.0 * size), a(1.0 * size),
                            a(0.5 * size), a(0.0 * size), a(0.0 * size), a(0.5 * size)]), dtype='float32')
        rhos = np.array([rho, rho, rho, rho, rho, rho, rho], dtype='float32')
        zs = np.array([0, 0.25 * height, 0.75 * height, height, 0.75 * height, 0.25 * height, 0], dtype='float32')
        hex = pol2cart(thetas, rhos, zs + lift)

    else:
        print(f'\tshapeGenerator::createHex > only \'flat\' or \'pointy\' are allowed. You are entered {type}')
        raise f'\tshapeGenerator::createHex > only \'flat\' or \'pointy\' are allowed. You are entered {type}'
    if rot_angle > 0:
        hex = rotate(hex, rot_angle)
    return hex


def generateBasicLine(RAD=10, layer_count=2, size=None, hex_count=None, hex_type='pointy'):
    # flat:    1 ---- 2        | pointy:         1
    #        /          \     h|                /   \
    #       /       size \    e|               6     2
    #       6      ._____3    i|               |     |
    #       \            /    g|               5     3
    #        \          /     h|                \   /
    #          5 ---- 4       t|                  4

    if not bool((size is None) + (hex_count is None)):
        print('\tshapeGenerator:generateBasicLine > one of \'size\' or \'hex_count\' sould be given')
        raise '\tshapeGenerator:generateBasicLine > one of \'size\' or \'hex_count\' sould be given'

    if hex_type.lower() == 'flat':
        if size is None:
            size = (2 * np.pi * RAD) / (2 * hex_count)
        else:
            hex_count = (2 * np.pi * RAD) / (2 * size)
        # size = 2
        height = np.sqrt(3) * size
        print(f'size = {size}\nhex_count = {hex_count}\nheight = {height}')
        hex = list()
        for layer in range(layer_count):
            iter_bounce = False
            for i in range(int(2 * hex_count)):
                hex.append(np.array(
                    createHex(rot_angle=(i * np.arctan2(size, RAD)),
                              lift=(layer * height + int(iter_bounce) * 0.5 * height),
                              size=size, rho=RAD, type=hex_type), dtype='float32'))
                iter_bounce = not iter_bounce

    elif hex_type.lower() == 'pointy':
        if size is None:
            size = (2 * np.pi * RAD) / (1 * hex_count)
        else:
            hex_count = (2 * np.pi * RAD) / size
        height = 2 * size
        print(f'size = {size}\nhex_count = {hex_count}\nheight = {height}')
        hex = list()
        for layer in range(layer_count):
            iter_bounce = False
            for i in range(int(2 * hex_count)):
                hex.append(np.array(
                    createHex(rot_angle=(i * np.arctan2(0.5 * size, RAD)),
                              lift=(layer * 1.5 * height + int(iter_bounce) * 0.75 * height),
                              size=size, rho=RAD, type=hex_type), dtype='float32'))
                iter_bounce = not iter_bounce
    else:
        print(f'\tshapeGenerator::generateBasicLine > only \'flat\' or \'pointy\' are allowed. You are entered {type}')
        raise f'\tshapeGenerator::generateBasicLine > only \'flat\' or \'pointy\' are allowed. You are entered {type}'

    return hex


def generateSplineShape(RAD=10):
    line = np.array(pol2cart([0, 0, 0, 0], [RAD, RAD, RAD, RAD], [0, 2, 5, 10]), dtype='float32').T
    thickness = 1
    arr = list()
    arr.append(line)
    arr.append(create_offset(line, thickness))

    return arr
