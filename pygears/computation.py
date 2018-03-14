import numpy as np
from scipy import optimize as opt

def computeShiftedGears(m, alpha, t1, t2, x1, x2):
    """Summary
    
    Args:
        m (float): common module of both gears [length]
        alpha (float): pressure-angle [rad]
        t1 (int): number of teeth of gear1
        t2 (int): number of teeth of gear2
        x1 (float): relative profile-shift of gear1
        x2 (float): relative profile-shift of gear2
    
    Returns:
        (float, float): distance between gears [length], pressure angle of the assembly [rad]
    """
    inv = lambda x: np.tan(x) - x
    inv_alpha_w = inv(alpha) + 2 * np.tan(alpha) * (x1 + x2) / (t1 + t2)
    root_inv = lambda x: inv(x) - inv_alpha_w
    alpha_w = opt.fsolve(root_inv, 0.)
    dist = m * (t1+ t2) / 2 * np.cos(alpha) / np.cos(alpha_w)
    return dist, alpha_w