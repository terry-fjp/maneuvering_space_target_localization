"""Original vector schematics: two-panel observation scene and three-stage method.
Schematic curves/ellipses explain principles; the range inset uses archived target states.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/msc-matplotlib')
from pathlib import Path
import csv
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch,FancyBboxPatch,Rectangle,Polygon,Ellipse,Circle
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'analysis/thrust_review_v12'))
from engine import rk4
H=Path(__file__).resolve().parents[2]/'analysis/thrust_review_v12';P=H.parents[1]/'output/latex/remotesensing_submission_en';O=P/'figures'

# Explicit sans-serif family sequence preserves Latin/CJK glyph fallback.
mpl.rcParams.update({'font.family':['DejaVu Sans'],'font.sans-serif':['DejaVu Sans'],'font.size':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
C='#146b87';G='#4a8468';R='#b75d55';Y='#c28a3b';N='#647582'
def save(f,n):
 f.savefig(O/f'{n}.pdf',dpi=300,bbox_inches='tight',pad_inches=.07)
 f.savefig(O/f'{n}.svg',dpi=300,bbox_inches='tight',pad_inches=.07)
 f.savefig(O/f'{n}.png',dpi=300,bbox_inches='tight',pad_inches=.07)
 plt.close(f)
def frame(a,title):
 a.set(xlim=(0,1),ylim=(0,1));a.axis('off');a.text(0,1.025,title,transform=a.transAxes,fontsize=11,weight='bold',va='bottom')
def box(a,x,y,w,h,t,color='#edf3f6',fs=9):
 a.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.008,rounding_size=.015',fc=color,ec='#b6c5cd',lw=.8));a.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=fs,linespacing=1.5)
def arrow(a,p,q,col=N,rad=0,style='-|>',lw=1.3,ls='-'):
 a.add_patch(FancyArrowPatch(p,q,arrowstyle=style,color=col,lw=lw,mutation_scale=11,connectionstyle=f'arc3,rad={rad}',linestyle=ls))
def sat(a,x,y,s=.07,col=Y):
 a.add_patch(Rectangle((x-s*.3,y-s*.34),s*.6,s*.68,fc=col,ec='#4e6270',lw=.7))
 for d in [-1,1]:
  xx=x+s*.38 if d>0 else x-s*1.1
  a.add_patch(Rectangle((xx,y-s*.27),s*.72,s*.54,fc='#477b9a',ec='#244e6a',lw=.7))
  for frac in [.25,.5,.75]:a.plot([xx+frac*s*.72]*2,[y-s*.27,y+s*.27],color='#a6c9d8',lw=.5)
 a.add_patch(Circle((x,y+s*.39),s*.13,fc='#e8edef',ec=N,lw=.6))
def ranges(ax):
 rows=list(csv.DictReader((H/'data/targets.csv').open()))
 for km,col in zip([500,1000,1500,2000],['#82aabc',C,G,Y]):
  rr=[r for r in rows if int(r['range_bin_km'])==km];x=np.array([[float(r[f'x{j}']) for j in range(6)] for r in rr]);o=np.array([[float(r[f'o{j}']) for j in range(6)] for r in rr]);v=[]
  for t in range(701):v.append(np.linalg.norm(x[:,:3]-o[:,:3],axis=1)/1000);x=rk4(x,1);o=rk4(o,1)
  v=np.array(v);ax.fill_between(range(701),v.min(1),v.max(1),color=col,alpha=.1);ax.plot(np.median(v,axis=1),color=col,lw=1.1,label=f'{km}')
 ax.set(xlabel='Time (s)',ylabel='Slant range (km)',xticks=[0,350,700],yticks=[500,1000,1500,2000]);ax.tick_params(labelsize=7);ax.set_title('Range coverage: 64 targets',fontsize=9,pad=20);ax.legend(ncol=4,loc='lower center',bbox_to_anchor=(.5,1),frameon=False,fontsize=6.8,handlelength=1.1,columnspacing=.5);ax.grid(alpha=.16)
def scene():
 fig=plt.figure(figsize=(11,7.5));a=fig.add_axes([.04,.53,.92,.42]);frame(a,'a  One observer, separate maneuvering-target encounters')
 # One observer, separate encounter targets and two complementary sensor paths.
 sat(a,.12,.56,.105,C);a.text(.12,.37,'Observer\n800 km / 60°',ha='center',va='top',fontsize=9)
 targets=[(.49,.82,500),(.57,.59,1000),(.52,.30,1500),(.35,.12,2000)]
 for j,(x,y,km) in enumerate(targets):
  arrow(a,(.18,.56),(x-.065,y),C,lw=1,ls='--');arrow(a,(x-.066,y-.025),(.18,.535),Y,lw=.9)
  sat(a,x,y,.047,Y);a.text(x,y-.075,f'{km} km',ha='center',va='top',fontsize=8.5)
  a.plot([x-.07,x,x+.085],[y-.08,y,y+.06],color='#9caeb7',lw=1,ls=':')
  arrow(a,(x+.01,y+.01),(x+.055,y+.09),R,lw=1.5)
  a.plot([x,x+.05,x+.10],[y,y+.08,y+.09],color=R,lw=1.1)
 a.text(.29,.95,'Eight acceleration levels; 60 s thrust',color=R,fontsize=8.8)
 a.text(.02,.04,'Optical angles',color=C,fontsize=8.5);a.plot([.02,.105],[.12,.12],color=C,ls='--');a.text(.15,.04,'Laser range',color=Y,fontsize=8.5);a.plot([.15,.235],[.12,.12],color=Y)
 inset=fig.add_axes([.71,.64,.245,.24]);ranges(inset)
 a.text(.82,.07,'4 range strata × 16 targets\nPaired rates: 5 / 10 / 15 / 20 Hz',ha='center',va='center',fontsize=8.5)
 # Principle panel: geometry constrains uncertainty; measurement action follows tracking precision.
 b=fig.add_axes([.04,.055,.92,.40]);frame(b,'b  Complementary angular and range information')
 for x,txt,fc in [(.01,'Optical tracking\nLine-of-sight direction','#edf3f6'),(.265,'Accumulate evidence\nDetect model mismatch','#faeee9'),(.52,'Add range data\nUpdate position/velocity','#fbf2e2'),(.775,'Restore accuracy\nForecast range needs','#edf3e9')]:box(b,x,.76,.21,.18,txt,fc,9)
 for x in [.22,.475,.73]:arrow(b,(x,.85),(x+.043,.85))
 b.text(.04,.63,'Measurement geometry (schematic)',fontsize=9)
 b.add_patch(Polygon([[.05,.27],[.40,.62],[.46,.50]],fc='#edf3f6',ec='none'))
 b.plot([.06,.44],[.28,.57],color=C,ls='--',lw=1)
 b.add_patch(Ellipse((.29,.44),.31,.09,angle=39,fc='#dce9ef',ec=C,ls='--',lw=1.2))
 b.add_patch(Ellipse((.32,.46),.085,.075,angle=39,fc='#d8e8db',ec=G,lw=1.5))
 b.scatter(.32,.46,marker='*',s=65,color=R);b.text(.14,.17,'Angles constrain transverse error\nRange constrains radial error',ha='center',fontsize=8.5)
 arrow(b,(.42,.62),(.34,.49),Y);b.text(.39,.66,'Range data',ha='center',fontsize=8.5,color=Y)
 curve=fig.add_axes([.57,.12,.36,.17]);tt=np.linspace(0,1,150);passive=.1+.66*np.clip(tt-.2,0,None);fusion=np.where(tt<.42,.1+.66*np.clip(tt-.2,0,None),.09+.155*np.exp(-(tt-.42)*13))
 curve.plot(tt,passive,color=C,ls='--',lw=1.2,label='Angles only');curve.plot(tt,fusion,color=G,lw=1.5,label='Angles + range');curve.axhline(.21,color=Y,ls=':',lw=1);curve.axvline(.2,color=R,ls=':',lw=.8);curve.axvline(.42,color=Y,ls=':',lw=.8)
 curve.set(xticks=[.2,.42,.87],xticklabels=['Thrust','Range added','Recovery'],yticks=[],ylabel='Position error');curve.legend(loc='upper left',fontsize=7.5,frameon=False);curve.text(.62,.225,'Task limit',fontsize=7.5,color=Y);curve.set_ylim(0,.68)
 b.text(.74,.025,'Accuracy and consistency feedback → range requests',ha='center',fontsize=8.5,color=G)
 save(fig,'scenario')
def method():
 fig=plt.figure(figsize=(11,8.0));a=fig.add_axes([.05,.775,.9,.17]);frame(a,'a  Detection, estimation, and ranging in one tracking loop')
 a.texts[0].set_position((0,1.28))
 stages=[(.01,'I  Maneuver detection','Optical innovations\n2 / 8 / 16 s windows + suppression','#edf3f6'),(.355,'II  State estimation','Alert → process-noise adaptation\nRetain prior; joint measurement update','#fbf2e2'),(.70,'III  Ranging control','Optical forecast + range-age guard\nThree task tiers; on-demand ranging','#edf3e9')]
 for x,title,body,col in stages:box(a,x,.20,.28,.70,body,col,9);a.text(x+.14,.98,title,ha='center',fontsize=10,color=C if x<.1 else Y if x<.5 else G)
 arrow(a,(.29,.54),(.35,.54));arrow(a,(.635,.54),(.695,.54));a.plot([.84,.84,.15,.15],[.18,.02,.02,.18],color=N,lw=1);arrow(a,(.15,.04),(.15,.18));a.text(.50,.025,'Continuous tracking feedback',ha='center',va='bottom',fontsize=8.5)
 b=fig.add_axes([.055,.405,.415,.27]);frame(b,'b  Directional evidence accumulation')
 tt=np.linspace(.02,.97,220);raw=.58+.042*np.sin(tt*150)+.16*np.clip((tt-.45)/.23,0,1);b.plot(tt,raw,color=C,lw=1.05);b.plot([.44,.44],[.40,.91],color=R,ls=':',lw=.9);b.text(.43,.93,'Sustained maneuver-induced residual',ha='center',fontsize=8.8,color=R)
 for y,x,name,col in [(.32,.86,'2 s: capture abrupt changes',C),(.20,.60,'8 s: confirm persistent changes',G),(.08,.08,'16 s: accumulate weak deviations',Y)]:b.add_patch(Rectangle((x,y),.97-x,.055,fc=col,alpha=.65));b.text(.025,y+.074,name,fontsize=8.3)
 c=fig.add_axes([.55,.405,.405,.27]);frame(c,'c  Joint update retaining the prior')
 c.add_patch(Ellipse((.47,.71),.76,.17,angle=15,fc='#dce9ef',ec=C,ls='--'));c.add_patch(Ellipse((.6,.74),.22,.12,angle=15,fc='#e2ecd9',ec=G));c.scatter(.60,.74,color=R,marker='*',s=55)
 c.text(.08,.94,'Combine existing information and new data',fontsize=8.8);c.text(.5,.49,'Retain state priors and cross-covariances',ha='center',fontsize=8.8,color=Y)
 for x,tx in [(.02,'Position r'),(.37,'Velocity v'),(.72,'Accel. a')]:box(c,x,.24,.24,.15,tx,fs=8.8)
 arrow(c,(.37,.315),(.27,.315));arrow(c,(.72,.315),(.62,.315));c.text(.5,.09,'Alert raises process noise for 60 s\nMeasurements update position, velocity, acceleration',ha='center',fontsize=8.5)
 d=fig.add_axes([.055,.065,.415,.245]);frame(d,'d  Guarded covariance prediction')
 xx=np.linspace(.04,.96,100);current=.17+.42*np.exp(-((xx-.40)/.16)**2);forecast=.24+.48*np.exp(-((xx-.36)/.20)**2)
 d.plot(xx,current,color=C,lw=1.3);d.plot(xx,forecast,color=Y,lw=1.3);d.plot([.03,.97],[.48,.48],color=R,ls='--',lw=.8)
 d.text(.78,.54,'Control threshold',fontsize=8,color=R,ha='center');d.text(.68,.84,'Forecast + range-age guard',color=Y,fontsize=8.8);d.text(.59,.31,'Covariance forecast',color=C,fontsize=8.8)
 arrow(d,(.28,.63),(.20,.52),Y);d.text(.13,.84,'Request range',color=Y,fontsize=8.5);d.text(.53,.035,'A longer range gap increases the guard',ha='center',fontsize=8.4)
 e=fig.add_axes([.55,.065,.405,.245]);frame(e,'e  Ranging requests across the stages')
 for x,w,col,tx in [(.13,.25,'#edf3f6','Evidence'),(.38,.30,'#fbf2e2','Correction'),(.68,.29,'#edf3e9','Tracking')]:e.add_patch(Rectangle((x,.13),w,.71,fc=col,ec='none'));e.text(x+w/2,.91,tx,ha='center',fontsize=8.5)
 e.plot([.13,.38,.38,.70,.70,.97],[.39,.39,.67,.67,.39,.39],color=C,lw=1.7);e.text(.015,.68,'On',fontsize=8.5);e.text(.015,.38,'Off',fontsize=8.5)
 for x in [.83,.94]:e.plot([x,x],[.39,.48],color=Y,lw=2)
 e.axvline(.38,ymin=.1,ymax=.87,color=R,ls=':',lw=1);e.text(.38,.035,'Accepted alert',ha='center',fontsize=8,color=R);e.text(.83,.19,'Predictive requests',ha='center',fontsize=8.5,color=Y)
 save(fig,'workflow')
if __name__=='__main__':scene();method();print('MSC-GP method schematic complete')
