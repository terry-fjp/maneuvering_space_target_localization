import numpy as np
from numerics import acceleration,gravity_jacobian
SIGMA_ANGLE=100e-6/np.sqrt(2)

def basis(u):
 ref=np.zeros_like(u); ref[:,2]=1; mask=np.abs(u[:,2])>.9; ref[mask]=[0,1,0]
 a=np.cross(u,ref);a/=np.linalg.norm(a,axis=1)[:,None]
 return np.stack((a,np.cross(u,a)),axis=1)

def rk4(x,dt,a=None):
 if a is None:a=np.zeros_like(x[:,:3])
 def rhs(y):return np.concatenate((y[:,3:],acceleration(y[:,:3])+a),axis=1)
 k1=rhs(x);k2=rhs(x+dt*k1/2);k3=rhs(x+dt*k2/2);k4=rhs(x+dt*k3)
 return x+dt*(k1+2*k2+2*k3+k4)/6

class Filter:
 def __init__(self,x,p,dim=9):
  self.x=np.zeros((len(x),dim));self.x[:,:6]=x
  self.p=np.zeros((len(x),dim,dim));self.p[:,:6,:6]=p
  if dim==9:self.p[:,6:,6:]=np.eye(3)*1e-4
  self.dim=dim
 def predict(self,dt,active=None):
  n=len(self.x);d=self.dim
  a=self.x[:,6:] if d==9 else None
  old=self.x[:,:3].copy();self.x[:,:6]=rk4(self.x[:,:6],dt,a)
  # Second-order variational map; exact kinematic white-jerk covariance.
  F=np.zeros((n,d,d));F[:,:3,3:6]=np.eye(3);F[:,3:6,:3]=gravity_jacobian(old)
  if d==9:F[:,3:6,6:]=np.eye(3)
  phi=np.eye(d)+F*dt+(F@F)*(dt*dt/2)
  self.p=phi@self.p@phi.transpose(0,2,1)
  if d==9:
   q=np.where(active,3e-4,1e-7) if active is not None else np.full(n,3e-4)
   small=np.array([[dt**5/20,dt**4/8,dt**3/6],[dt**4/8,dt**3/3,dt**2/2],[dt**3/6,dt**2/2,dt]])
   self.p+=q[:,None,None]*np.kron(small,np.eye(3))
  else:
   self.p+=1e-6*np.kron(np.array([[dt**3/3,dt**2/2],[dt**2/2,dt]]),np.eye(3))

 def reset(self,mask):
  self.p[mask,3:6,3:6]+=25*np.eye(3)
