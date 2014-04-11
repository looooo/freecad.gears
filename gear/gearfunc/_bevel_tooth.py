# -*- coding: utf-8 -*-
#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

from __future__ import division
from __future__ import division
from numpy import cos, sin, tan, arccos, arctan, pi, array, linspace, transpose, vstack, sqrt
from _functions import rotation3D, reflection3D



class bevel_tooth(object):
    def __init__(self, alpha = 70 * pi / 180, gamma = pi / 4 , z = 21, backslash = 0.01, module = 0.25):
        self.alpha = alpha
        self.gamma = gamma
        self.z = z
        self.backslash = backslash
        self.module = module

        self.involute_end = arccos(
            1 / sqrt(2) * sqrt((42. + 16.*cos(2.*self.alpha) +
            6.*cos(4.*self.alpha) + cos(4.*self.alpha - 4.*self.gamma) - 8.*cos(2.*self.alpha - 2.*self.gamma) -
            4.*cos(4.*self.alpha - 2.*self.gamma) + 24.*cos(2.*self.gamma) - 2.*cos(4.*self.gamma) -
            8.*cos(2.*(self.alpha + self.gamma)) + cos(4.*(self.alpha + self.gamma)) -
            4.*cos(4.*self.alpha + 2.*self.gamma) + 24.*cos((4.*sin(self.gamma))/self.z) +
            4.*cos(2.*self.alpha - (4.*sin(self.gamma))/self.z) + 4.*cos(2.*self.alpha -
            4.*self.gamma - (4.*sin(self.gamma))/self.z) - 8.*cos(2.*self.alpha - 2.*self.gamma -
            (4.*sin(self.gamma))/self.z) + 24.*cos(4.*(self.gamma + sin(self.gamma)/self.z)) -
            8.*cos(2.*(self.alpha + self.gamma + (2.*sin(self.gamma))/self.z)) + 4.*cos(2.*self.alpha +
            (4.*sin(self.gamma))/self.z) + 16.*cos(2.*self.gamma + (4.*sin(self.gamma))/self.z) +
            4.*cos(2.*self.alpha + 4.*self.gamma + (4.*sin(self.gamma))/self.z) + 32.*abs(cos(self.gamma +
            (2.*sin(self.gamma))/self.z))*cos(self.alpha)*sqrt(4.*cos(2.*self.alpha) -
            2.*(-2. + cos(2.*self.alpha - 2.*self.gamma) - 2.*cos(2.*self.gamma) + cos(2.*(self.alpha + self.gamma)) +
            4.*cos(2.*self.gamma + (4.*sin(self.gamma))/self.z)))*sin(2.*self.gamma))/(-6. - 2.*cos(2.*self.alpha) +
            cos(2.*self.alpha - 2.*self.gamma) - 2.*cos(2.*self.gamma) + cos(2.*(self.alpha + self.gamma)))**2))

        self.involute_start = -pi/2. + \
            arctan(1/tan(self.gamma)*1/cos(self.alpha))
        self.involute_start_radius = self.getradius(self.involute_start)
        self.r_f = sin(self.gamma - sin(gamma) * 2 / self.z)
        self.z_f = cos(self.gamma - sin(gamma) * 2 / self.z)
        self.add_foot = True

        if self.involute_start_radius < self.r_f:
            self.add_foot = False
            self.involute_start = -arccos(
                sqrt((42 + 16*cos(2*self.alpha) + 6*cos(4*self.alpha) -
                4*cos(4*self.alpha - 2*self.gamma) - 8*cos(2*(self.alpha - self.gamma)) +
                cos(4*(self.alpha - self.gamma)) + 24*cos(2*self.gamma) - 2*cos(4*self.gamma) -
                8*cos(2*(self.alpha + self.gamma)) + cos(4*(self.alpha + self.gamma)) -
                4*cos(2*(2*self.alpha + self.gamma)) + 24*cos((4*sin(self.gamma))/self.z) +
                4*cos(2*self.alpha - (4*sin(self.gamma))/self.z) + 16*cos(2*self.gamma -
                (4*sin(self.gamma))/self.z) + 24*cos(4*self.gamma - (4*sin(self.gamma))/self.z) +
                4*cos(2*self.alpha + 4*self.gamma - (4*sin(self.gamma))/self.z) -
                8*cos(2*(self.alpha + self.gamma - (2*sin(self.gamma))/self.z)) +
                4*cos(2*self.alpha + (4*sin(self.gamma))/self.z) + 4*cos(2*self.alpha -
                4*self.gamma + (4*sin(self.gamma))/self.z) - 8*cos(2*self.alpha - 2*self.gamma +
                (4*sin(self.gamma))/self.z) + 32*sqrt(2)*sqrt(-(cos(self.alpha)**2*
                (-2 - 2*cos(2*self.alpha) + cos(2*(self.alpha - self.gamma)) -
                2*cos(2*self.gamma) + cos(2*(self.alpha + self.gamma)) +
                4*cos(2*self.gamma - (4*sin(self.gamma))/self.z))*cos(self.gamma - (2*sin(self.gamma))/self.z)**2*
                sin(2*self.gamma)**2)))/(-6 - 2*cos(2*self.alpha) + cos(2*(self.alpha - self.gamma)) -
                2*cos(2*self.gamma) + cos(2*(self.alpha + self.gamma)))**2)/sqrt(2))

    def involute_function_x(self):
        def func(s):
            return((
                -(cos(s*1/sin(self.alpha)*1/sin(self.gamma))*sin(self.alpha)*sin(s)) +
                (cos(s)*sin(self.gamma) + cos(self.alpha)*cos(self.gamma)*sin(s))*
                sin(s*1/sin(self.alpha)*1/sin(self.gamma))))
        return(func)

    def involute_function_y(self):
        def func(s):
            return((
                cos(s*1/sin(self.alpha)*1/sin(self.gamma))*(cos(s)*sin(self.gamma) +
                cos(self.alpha)*cos(self.gamma)*sin(s)) + sin(self.alpha)*sin(s)*
                sin(s*1/sin(self.alpha)*1/sin(self.gamma))))
        return(func)

    def involute_function_z(self):
        def func(s):
            return((
                cos(self.gamma)*cos(s) - cos(self.alpha)*sin(self.gamma)*sin(s)))
        return(func)

    def getradius(self, s):
        x = self.involute_function_x()
        y = self.involute_function_y()
        rx = x(s)
        ry = y(s)
        return(sqrt(rx**2 + ry**2))


    def involute_points(self, num=10):
        pts = linspace(self.involute_start, self.involute_end, num=num)
        fx = self.involute_function_x()
        x = array(map(fx, pts))
        fy = self.involute_function_y()
        y = array(map(fy, pts))
        fz = self.involute_function_z()
        z = array(map(fz, pts))
        xyz = transpose(array([x, y,z]))
        if self.add_foot:
            p = xyz[1]
            p1 =map(lambda x: x * (self.r_f / sqrt(p[0]**2 + p[1]**2)), p)
            p1[2] = self.z_f
            xyz=vstack([[p1], xyz])
        xy = [[i[0]/i[2],i[1]/i[2],1.] for i in xyz]
        backslash_rot = rotation3D(self.backslash / 4)
        xy = backslash_rot(xy)
        return(xy)

    def points(self, num=10):
        pts = self.involute_points(num = num)
        rot = rotation3D(-pi/self.z/2)
        pts = rot(pts)
        ref = reflection3D(pi/2)
        pts1 = ref(pts)[::-1]
        rot = rotation3D(2*pi/self.z)
        pt3 = rot(pts[0])
        if self.add_foot:
            return(array([
                [pts[0],pts[1]],
                pts[1:],
                [pts[-1], pts1[0]],
                pts1[:-1],
                [pts1[-2], pts1[-1]]
                ]))
            return(array([pts,[pts[-1],pts1[0]], pts1]))
        else:
            return(array([pts,[pts[-1],pts1[0]], pts1]))

    def _update(self):
        self.__init__(z = self.z,
                alpha = self.alpha,  gamma = self.gamma, backslash = self.backslash, module = self.module)


if __name__ == "__main__":
	from matplotlib import pyplot
	gear = bevel_tooth()
	x = []
	y = []
	for i in gear.points(30):
		for j in i:
			x.append(j[0])
			y.append(j[1])
	pyplot.plot(x,y)
	pyplot.show()
