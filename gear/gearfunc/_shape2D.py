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

from math import cos, sin, atan, pi, tan, sqrt, acos
from numpy import array, dot, linspace, transpose, vstack, ndarray
from numpy.linalg import solve
import copy


# dg...groundcircle
# dw...pitch circle
# df...? fußkreis
# c... ? clearence
class gearrack():

    def __init__(self, m=5, z=21, shift=0., alpha=15 * pi / 180, clearence=0.12, beta=0.):
        self.clearence = clearence
        self.alpha = alpha
        self.beta = beta
        self.z = z
        self.m = m
        self.shift = shift
        self.c = self.clearence * m
        self.m_t = self.m / cos(self.beta)
        self.alpha_t = atan(tan(self.alpha) / cos(self.beta))

    def points(self):
        x1 = - self.m - self.c + self.shift * self.m
        x2 = self.m + self.shift * self.m
        y1 = self.m_t * pi / 4 - (self.m + self.c) * tan(self.alpha_t)
        y2 = self.m_t * pi / 4 + (self.m) * tan(self.alpha_t)
        p1 = [x2, -y2]
        p2 = [x1, -y1]
        p3 = [x1, y1]
        p4 = [x2, y2]
        z = vstack([p1, p2, p3, p4])
        teeth = [z]
        trans = translation([0., self.m_t * pi])
        for i in range(self.z):
            z = trans(z)
            teeth.append(z)
        teeth = vstack(teeth)[1:]
        reflect = reflection(0)
        teeth = vstack([teeth[::-1], reflect(teeth)])
        trans = translation([0., self.m_t * pi / 2.])
        teeth = trans(teeth)
        return(teeth)

    def gearfunc(self, x):
        trans = translation([0., -x])
        return(trans)


class gearwheel():

    def __init__(self, m=5, z=15, alpha=20 * pi / 180., clearence=0.12, shift=0.5, beta=0., undercut=False, backslash=0.01):
        self.alpha = alpha
        self.beta = beta
        self.m_n = m
        self.z = z
        self.undercut = undercut
        self.shift = shift
        self.clearence = clearence
        self.backslash = backslash
        self.alpha_t = atan(tan(self.alpha) / cos(self.beta))
        self.m = self.m_n / cos(self.beta)
        self.c = self.clearence * self.m_n
        self.midpoint = [0., 0.]
        self.d = self.z * self.m
        self.dw = self.m * self.z
        self.da = self.dw + 2. * self.m_n + 2. * self.shift * self.m_n
        self.df = self.dw - 2. * self.m_n - \
            2 * self.c + 2. * self.shift * self.m_n
        self.dg = self.d * cos(self.alpha_t)
        self.phipart = 2 * pi / self.z

        self.undercut_end = sqrt(-self.df ** 2 + self.da ** 2) / self.da
        self.undercut_rot = (-self.df / self.dw * tan(atan((2 * ((self.m * pi) / 4. -
                            (self.c + self.m_n) * tan(self.alpha_t))) / self.df)))

        self.involute_end = sqrt(self.da ** 2 - self.dg ** 2) / self.dg
        self.involute_rot1 = sqrt(-self.dg ** 2 + (self.dw) ** 2) / self.dg - atan(
            sqrt(-self.dg ** 2 + (self.dw) ** 2) / self.dg)
        self.involute_rot2 = self.m / \
            (self.d) * (pi / 2 + 2 * self.shift * tan(self.alpha_t))
        self.involute_rot = self.involute_rot1 + self.involute_rot2
        self.involute_start = 0.
        if self.dg <= self.df:
            self.involute_start = sqrt(self.df ** 2 - self.dg ** 2) / self.dg

    def undercut_points(self, num=10):
        pts = linspace(0, self.undercut_end, num=num)
        fx = self.undercut_function_x()
        x = array(map(fx, pts))
        fy = self.undercut_function_y()
        y = array(map(fy, pts))
        xy = transpose([x, y])
        rotate = rotation(
            self.undercut_rot + self.phipart / 2 - self.backslash / 4)
        xy = rotate(xy)
        return(array(xy))

    def involute_points(self, num=10):
        pts = linspace(self.involute_start, self.involute_end, num=num)
        fx = self.involute_function_x()
        x = array(map(fx, pts))
        fy = self.involute_function_y()
        y = array(map(fy, pts))
        rot = rotation(self.involute_rot - self.backslash / 4)
        xy = rot(transpose(array([x, y])))
        return(xy)

    def points(self, num=10):
        l1 = self.undercut_points(num=num)
        l2 = self.involute_points(num=num)
        s = trimfunc(l1, l2[::-1])
        if self.undercut:
            if isinstance(s, ndarray):
                u1, e1 = s
            else:
                u1, e1 = nearestpts(l2, l1)
        else:
            u1 = False
            if self.dg > self.df:
                u1 = vstack(
                    [[l2[0] * self.df / (norm(l2[0], [0, 0]) * 2)], [l2[0]]])
                e1 = l2
            else:
                e1 = l2

        reflect = reflection(0)
        e2 = reflect(e1)[::-1]
        rot = rotation(-self.phipart)
        if isinstance(u1, bool):
            u2 = False
            one_tooth = [e1, [e1[-1], e2[0]], e2]
        else:
            u2 = reflect(u1)[::-1]
            one_tooth = [u1, e1, [e1[-1], e2[0]], e2, u2]
        all_teeth = copy.copy(one_tooth)
        last_tooth = copy.copy(one_tooth)
        for i in range(self.z - 1):
            rot = rotation(-self.phipart * (i + 1))
            temp_tooth = map(rot, one_tooth)
            join_seg = [array([last_tooth[-1][-1], temp_tooth[0][0]])]
            all_teeth += join_seg
            all_teeth += temp_tooth
            last_tooth = copy.copy(temp_tooth)
        all_teeth += [[all_teeth[0][0], all_teeth[-1][-1]]]
        return(all_teeth)


    def gearfunc(self, x):
        rot = rotation(2 * x / self.dw, self.midpoint)
        return(rot)

    def undercut_function_x(self):
        def func(psi):
            return(
               cos(psi - (self.df * tan(psi)) / self.dw) * sqrt(self.df ** 2 / 4 +
                                                                (self.df ** 2 * tan(psi) ** 2) / 4.))
        return(func)


    def undercut_function_y(self):
        def func(psi):
            return(
                sin(psi - (self.df * tan(psi)) / self.dw) * sqrt(self.df ** 2 / 4 +
                                                                (self.df ** 2 * tan(psi) ** 2) / 4.))
        return(func)

    def involute_function_x(self):
        def func(phi):
            return(array(self.dg / 2 * cos(phi) + phi * self.dg / 2 * sin(phi)))
        return(func)

    def involute_function_y(self):
        def func(phi):
            return(self.dg / 2 * sin(phi) - phi * self.dg / 2 * cos(phi))
        return(func)

    def _update(self):
        self.__init__(m = self.m_n, z = self.z,
                alpha = self.alpha, clearence = self.clearence, shift = self.shift,
                beta = self.beta, undercut = self.undercut, backslash = self.backslash)


class cycloidegear():
    def __init__(self, d1 = 10, d2 = 10, z = 14, m = 5, clearence = 0.12, backslash = 0.00):
        self.m = m
        self.z = z
        self.clearence = clearence
        self.backslash = backslash
        self.d1 = d1 * self.m
        self.d2 = d2 * self.m
        self.c = self.clearence * self.m
        self.phi = self.m * pi
        self.d = self.z * self.m
        self.da = self.d + 2*self.m
        self.di = self.d - 2*self.m - self.c
        self.phipart = 2 * pi / self.z


    def epicycloide_x(self):
        def func(t):
            return(((self.d2 + self.d) * cos(t))/2. - (self.d2 * cos((1 + self.d / self.d2) * t))/2.)
        return(func)

    def epicycloide_y(self):
        def func(t):
            return(((self.d2 + self.d) * sin(t))/2. - (self.d2 * sin((1 + self.d / self.d2) * t))/2.)
        return(func)

    def hypocycloide_x(self):
        def func(t):
            return((self.d - self.d1)*cos(t)/2 + self.d1/2 * cos((self.d / self.d1 - 1) * t))
        return(func)

    def hypocycloide_y(self):
        def func(t):
            return((self.d - self.d1)*sin(t)/2 - self.d1/2 *sin((self.d/self.d1 - 1)*t))
        return(func)

    def inner_end(self):
        return(
            -((self.d1*acos((2*self.d1**2 - self.di**2 -
                2*self.d1*self.d + self.d**2)/(2.*self.d1*
                (self.d1 - self.d))))/self.d)
            )

    def outer_end(self):
        return(
            (self.d2*acos((2*self.d2**2 - self.da**2 +
                2*self.d2*self.d + self.d**2)/
                (2.*self.d2*(self.d2 + self.d))))/self.d
            )

    def points(self, num = 10):

        inner_x = self.hypocycloide_x()
        inner_y = self.hypocycloide_y()
        outer_x = self.epicycloide_x()
        outer_y = self.epicycloide_y()
        t_inner_end = self.inner_end()
        t_outer_end = self.outer_end()
        t_vals_outer = linspace(0, t_outer_end, num)
        t_vals_inner = linspace(t_inner_end,0,num)
        pts_outer_x = map(outer_x, t_vals_outer)
        pts_outer_y = map(outer_y, t_vals_outer)
        pts_inner_x = map(inner_x, t_vals_inner)
        pts_inner_y = map(inner_y, t_vals_inner)
        pts_outer = transpose([pts_outer_x, pts_outer_y])
        pts_inner = transpose([pts_inner_x, pts_inner_y])
        pts1 = vstack([pts_inner[:-2],pts_outer])
        rot =rotation(self.phipart/4 - self.backslash)
        pts1 = rot(pts1)
        ref = reflection(0.)
        pts2 = ref(pts1)[::-1]
        one_tooth = [pts1,array([pts1[-1],pts2[0]]), pts2]
        all_teeth = copy.copy(one_tooth)
        last_tooth = copy.copy(one_tooth)
        for i in range(self.z - 1):
            rot = rotation(-self.phipart * (i + 1))
            temp_tooth = map(rot, one_tooth)
            join_seg = [array([last_tooth[-1][-1], temp_tooth[0][0]])]
            all_teeth += join_seg
            all_teeth += temp_tooth
            last_tooth = copy.copy(temp_tooth)
        all_teeth += [array([all_teeth[0][0], all_teeth[-1][-1]])]
        return(all_teeth)

    def _update(self):
        self.__init__(m = self.m, z = self.z, d1 = self.d1, d2 = self.d2,
                      clearence = self.clearence, backslash = self.backslash)


class bevelgear(object):
    def __init__(self, alpha = 70 * pi / 180, gamma = pi / 4 , z = 21, backslash = 0.01, module = 0.25):
        self.alpha = alpha
        self.gamma = gamma
        self.z = z
        self.backslash = backslash
        self.module = module

        self.involute_end = acos(
            0.7071067811865475 * sqrt((42. + 16.*cos(2.*self.alpha) +
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
            atan(1/tan(self.gamma)*1/cos(self.alpha))
        self.involute_start_radius = self.getradius(self.involute_start)
        self.r_f = sin(self.gamma - sin(gamma) * 2 / self.z)
        self.z_f = cos(self.gamma - sin(gamma) * 2 / self.z)
        self.add_foot = True

        if self.involute_start_radius < self.r_f:
            self.add_foot = False
            self.involute_start = -acos(
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
                [pts1[-2], pts1[-1]],
                [pts1[-1],pt3]]))
            return(array([pts,[pts[-1],pts1[0]], pts1,[pts1[-1],pt3]]))
        else:
            return(array([pts,[pts[-1],pts1[0]], pts1,[pts1[-1],pt3]]))

    def _update(self):
        self.__init__(z = self.z,
                alpha = self.alpha,  gamma = self.gamma, backslash = self.backslash, module = self.module)






if __name__ == "__main__":
    a = cycloidegear(d1=4, d2=4, z=30)
    from openglider.graphics import Graphics2D, Line
    Graphics2D(map(Line, a.points(10)))
