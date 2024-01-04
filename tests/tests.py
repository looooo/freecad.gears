import unittest

from freecad import app
from freecad import part
from freecad.gears.basegear import helical_extrusion



class GearTests(unittest.TestCase):
    def test_helical_extrusion(self):
        """check if helical extrusion is working correctly"""
        normal = app.Vector(0, 0, 1)
        midpoint = app.Vector(0, 0, 0)
        radius = 10
        height = 10
        rotation = 3.1415926535 / 4

        circle = part.Circle(midpoint, normal, radius)
        face = part.Face(part.Wire(circle.toShape()))
        solid = helical_extrusion(face, height, rotation)
        
        # face 0 is the cylinder
        # face 1 is pointing in positive z direction
        # face 2 is pointing in negative z direction
        self.assertAlmostEqual((solid.Faces[1].normalAt(0,0) - normal).Length, 0.)
        self.assertAlmostEqual((solid.Faces[2].normalAt(0,0) + normal).Length, 0.)
        self.assertAlmostEqual(solid.Faces[1].valueAt(0,0)[2], height)
        self.assertAlmostEqual(solid.Faces[2].valueAt(0,0)[2], 0.)

if __name__ == "__main__":
    unittest.main(verbosity=4)