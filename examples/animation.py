# script for bevel-gear animation

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import numpy as np
import imageio

doc = App.ActiveDocument
g2 = doc.Common
g1 = doc.Common001

timer = QtCore.QTimer()

def make_pics():
    n = 30
    for i in range(n):
        phi = np.pi * 2 / 30 / n
    	g1.Placement.Rotation.Angle += phi * 2
    	g2.Placement.Rotation.Angle -= phi
        Gui.activeDocument().activeView().saveImage('/home/lo/Schreibtisch/animated_gear/gear_{}.png'.format(i) ,300,300,'Current')

def make_animated_gif():


def update(*args):
    print("time")
    delta_phi = 0.005
    g1.Placement.Rotation.Angle += delta_phi * 2
    g2.Placement.Rotation.Angle -= delta_phi

timer.timeout.connect(update)
timer.start()
