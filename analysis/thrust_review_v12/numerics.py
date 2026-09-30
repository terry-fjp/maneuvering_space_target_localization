import numpy as np
MU=3.986004418e14
RE=6378137.0
J2=1.08262668e-3
def acceleration(r):
    r2 = np.sum(r * r, axis=-1, keepdims=True)
    z2 = r[..., 2:3] ** 2 / r2
    correction = np.concatenate((5 * z2 - 1, 5 * z2 - 1, 5 * z2 - 3), -1)
    return -MU * r / r2**1.5 + 1.5 * J2 * MU * RE**2 * r * correction / r2**2.5



def gravity_jacobian(r):
 r=np.asarray(r);z=r[...,None,:].astype(complex)+1e-12j*np.eye(3)
 return np.swapaxes(acceleration(z).imag/1e-12,-1,-2)
