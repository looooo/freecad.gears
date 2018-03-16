# script for bevel-gear animation

from PySide import QtGui, QtCore

doc = App.ActiveDocument
g2 = doc.Common
g1 = doc.Common001

timer = QtCore.QTimer()

def update(*args):
    print("time")
    delta_phi = 0.005
    g1.Placement.Rotation.Angle += delta_phi * 2
    g2.Placement.Rotation.Angle -= delta_phi

timer.timeout.connect(update)
timer.start()