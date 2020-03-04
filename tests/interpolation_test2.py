import numpy as np
from scipy.interpolate import RectBivariateSpline
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import time

print("RectBivariateSpline")
start_time = time.time()
# Regularly-spaced, coarse grid - real DEM
# #------- test: Generate interpolation --------
# x = np.arange(1716948)
# y = np.arange(1716948)
# Z = np.zeros(1716948)

dx, dy = 0.4, 0.4
xmax, ymax = 2, 4
x = np.arange(-xmax, xmax, dx)
y = np.arange(-ymax, ymax, dy)
X, Y = np.meshgrid(x, y)
# X: increments to right(col)
# Y: increments to down(row)
Z = np.exp(-(2*X)**2 - (Y/2)**2)
print(Z.shape)

interp_spline = RectBivariateSpline(y, x, Z)    # row, col, value

# Regularly-spaced, fine grid - virtual DEM
dx2, dy2 = 0.16, 0.16
x2 = np.arange(-xmax, xmax, dx2)
y2 = np.arange(-ymax, ymax, dy2)
X2, Y2 = np.meshgrid(x2,y2)
Z2 = interp_spline(y2, x2)
print(Z2.shape)
print("--- %s seconds ---" % (time.time() - start_time))

fig, ax = plt.subplots(nrows=1, ncols=2, subplot_kw={'projection': '3d'})
ax[0].plot_wireframe(X, Y, Z, color='k')

ax[1].plot_wireframe(X2, Y2, Z2, color='k')
for axes in ax:
    axes.set_zlim(-0.2,1)
    axes.set_axis_off()

fig.tight_layout()
plt.show()