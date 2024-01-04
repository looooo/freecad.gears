import unittest

from freecad import app
from freecad import part
from freecad.gears.basegear import helical_extrusion



class GearTests(unittest.TestCase):
    def test_helical_extrusion(self):
        """check if helical extrusion is working correctly"""
        n = app.Vector(0, 0, 1)
        m = app.Vector(0, 0, 0)
        r = 10
        h = 10
        degree = 3.1415926535 / 4

        a = part.Circle(m, n, r)
        face = part.Face(part.Wire(a.toShape()))
        s = helical_extrusion(face, h, 1)
        
        # face 0 is the cylinder
        # face 1 is pointing in positive z direction
        # face 2 is pointing in negative z direction
        self.asserTrue((s.Faces[1].normalAt(0,0) - n).Length < 10e-15)
        self.asserTrue((s.Faces[2].normalAt(0,0) + n).Length < 10e-15)
        self.asserTrue(s.Faces[1].valueAt(0,0)[2] - h < 10e-15)
        self.asserTrue(s.Faces[2].valueAt(0,0)[2] - 0. < 10e-15)