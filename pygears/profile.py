import numpy as np
from .involute_tooth import InvoluteTooth, InvoluteRack
from .bevel_tooth import BevelTooth
from .cycloid_tooth import CycloidTooth
from ._functions import rotation, rotation3D


class _GearProfile(object):
    rot3D = False
    def profile(self, num=10):
        tooth = self.points(num=num)
        tooth = [list(point) for wire in tooth for point in wire]
        if self.rot3D:
            rot = rotation3D( np.pi * 2 / self.z)
        else:
            rot = rotation(- np.pi * 2 / self.z)
        profile = tooth
        for i in range(self.z - 1):
            tooth = rot(tooth).tolist()
            profile = profile + tooth
        profile.append(profile[0])
        return np.array(profile)

class InvoluteProfile(InvoluteTooth, _GearProfile):
    pass

class CycloidProfile(CycloidTooth, _GearProfile):
    pass

class BevelProfile(BevelTooth, _GearProfile):
    rot3D = True

class InvoluteRackProfile(InvoluteRack):
    def profile(self):
        return self.points()




