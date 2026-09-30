import numpy as np
from scipy.linalg import expm
from scipy.special import logsumexp
from scipy.stats import chi2
RISK_CHI2=float(chi2.ppf(.999,3))
def confidence_bounds(p):
 """Bounding-sphere radii of 99.9% marginal Gaussian 3D error ellipsoids.
 Valid under the local unbiased Gaussian covariance model, not a hard guarantee.
 """
 return np.sqrt(RISK_CHI2*np.maximum(0,np.stack((np.linalg.eigvalsh(p[:,:3,:3])[:,-1],np.linalg.eigvalsh(p[:,3:6,3:6])[:,-1]),axis=1)))
from engine import Filter, rk4, basis, gravity_jacobian, SIGMA_ANGLE

def observations(truth, observer, rng):
 d=truth[:,:3]-observer[:,:3];rho=np.linalg.norm(d,axis=1);u=d/rho[:,None]
 e=rng.normal(size=(len(d),3));bu=basis(u)
 um=u+np.einsum('nij,ni->nj',bu,e[:,:2]*SIGMA_ANGLE);um/=np.linalg.norm(um,axis=1)[:,None]
 return um,rho+50*e[:,2]

def cartesian(um,rho,observer):
 outer=um[:,:,None]*um[:,None,:]
 R=2500*outer+(rho*SIGMA_ANGLE)[:,None,None]**2*(np.eye(3)-outer)
 return observer[:,:3]+rho[:,None]*um,R

class Tracker(Filter):
 def __init__(self,x,p,dim=9,q=1e-7):
  super().__init__(x,p,dim);self.q=q;self.loglike=np.zeros(len(x))
 def predict(self,dt,active=None):
  super().predict(dt,active)
  if self.dim==9 and active is None:
   small=np.array([[dt**5/20,dt**4/8,dt**3/6],[dt**4/8,dt**3/3,dt**2/2],[dt**3/6,dt**2/2,dt]])
   self.p+=(self.q-3e-4)*np.kron(small,np.eye(3))
 def linear_update(self,y,h,R,ids):
  if not len(ids):return
  p=self.p[ids];hp=h@p;S=hp@h.transpose(0,2,1)+R
  gain=np.linalg.solve(S,hp).transpose(0,2,1)
  self.loglike[ids]=-.5*(np.einsum('ni,ni->n',y,np.linalg.solve(S,y[:,:,None])[:,:,0])+np.linalg.slogdet(S)[1]+h.shape[1]*np.log(2*np.pi))
  self.x[ids]+=np.einsum('nij,nj->ni',gain,y)
  A=np.eye(self.dim)-gain@h;new=A@p@A.transpose(0,2,1)+gain@R@gain.transpose(0,2,1)
  self.p[ids]=(new+new.transpose(0,2,1))/2
 def observe(self,um,rho,o,use_range,recondition=None):
  ids=np.flatnonzero(~use_range)
  if len(ids):
   delta=self.x[ids,:3]-o[ids,:3];rr=np.linalg.norm(delta,axis=1);pred=delta/rr[:,None];b=basis(um[ids]);y=np.einsum('nij,nj->ni',b,um[ids]-pred)
   h=np.zeros((len(ids),2,self.dim));h[:,:,:3]=(b-np.einsum('nij,nj->ni',b,pred)[:,:,None]*pred[:,None,:])/rr[:,None,None]
   self.linear_update(y,h,np.broadcast_to(np.eye(2)*SIGMA_ANGLE**2,(len(ids),2,2)),ids)
  z,R=cartesian(um,rho,o);reset=np.zeros(len(um),bool) if recondition is None else (recondition&use_range)
  ids=np.flatnonzero(reset)
  if len(ids):
   self.x[ids,:3]=z[ids];self.p[ids,:3,:]=0;self.p[ids,:,:3]=0;self.p[ids,:3,:3]=R[ids]
   self.p[ids,3:6,3:6]+=25*np.eye(3)
   if self.dim==9:self.p[ids,6:,6:]+=.01*np.eye(3)
  ids=np.flatnonzero(use_range&~reset)
  if len(ids):
   h=np.zeros((len(ids),3,self.dim));h[:,:,:3]=np.eye(3);self.linear_update(z[ids]-self.x[ids,:3],h,R[ids],ids)
  return z,R
 def bounds(self,horizon=0,q=1e-7):
  ar=np.zeros((3,self.dim));ar[:,:3]=np.eye(3);ar[:,3:6]=horizon*np.eye(3)
  av=np.zeros((3,self.dim));av[:,3:6]=np.eye(3)
  if self.dim==9:ar[:,6:]=.5*horizon*horizon*np.eye(3);av[:,6:]=horizon*np.eye(3)
  pr=ar@self.p@ar.T;pv=av@self.p@av.T
  if self.dim==9:pr+=np.asarray(q)[...,None,None]*horizon**5/20*np.eye(3);pv+=np.asarray(q)[...,None,None]*horizon**3/3*np.eye(3)
  return np.sqrt(RISK_CHI2*np.maximum(0,np.stack((np.linalg.eigvalsh(pr)[:,-1],np.linalg.eigvalsh(pv)[:,-1]),axis=1)))

class IMM:
 """Standard two-mode interacting EKF; maneuver-tracking family of Goff et al.
 Full moment mixing and likelihood updates; not a reproduction of their settings.
 """
 def __init__(self,x,p):
  self.filters=[Tracker(x.copy(),p.copy(),9,q=q) for q in [1e-7,3e-4]];self.w=np.tile([.9,.1],(len(x),1));self.x=self.filters[0].x.copy();self.p=self.filters[0].p.copy()
 def predict(self,dt,active=None):
  if not hasattr(self,'transition') or self.transition[0]!=dt:self.transition=(dt,expm(np.array([[-.005,.005],[.05,-.05]])*dt))
  trans=self.transition[1];pred=self.w@trans;mix=self.w[:,:,None]*trans[None,:,:]/pred[:,None,:]
  states=np.stack([f.x for f in self.filters],axis=1);covs=np.stack([f.p for f in self.filters],axis=1)
  for j,f in enumerate(self.filters):
   x=np.einsum('ni,nij->nj',mix[:,:,j],states);delta=states-x[:,None,:];p=np.einsum('ni,nijk->njk',mix[:,:,j],covs+delta[:,:,:,None]*delta[:,:,None,:]);f.x=x;f.p=p;f.predict(dt)
  self.w=pred
 def observe(self,um,rho,o,use_range,recondition=None):
  for f in self.filters:f.observe(um,rho,o,use_range)
  logw=np.log(np.maximum(self.w,1e-300))+np.stack([f.loglike for f in self.filters],axis=1);self.w=np.exp(logw-logsumexp(logw,axis=1)[:,None]);states=np.stack([f.x for f in self.filters],axis=1);self.x=np.einsum('ni,nij->nj',self.w,states);delta=states-self.x[:,None,:];covs=np.stack([f.p for f in self.filters],axis=1);self.p=np.einsum('ni,nijk->njk',self.w,covs+delta[:,:,:,None]*delta[:,:,None,:])
