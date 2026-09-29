"""Asymmetric research hypotheses: uncapped exits, no orders or live sizing."""
import statistics
from indicators import atr,sma
NAMES=('compression_expansion','failed_breakout','trend_pullback')
def signal(a,i,name):
 if i<205:return 0
 p=a[i-20:i];c=a[i][4];hi=max(x[2] for x in p);lo=min(x[3] for x in p)
 if name=='compression_expansion':
  recent=[x[2]-x[3] for x in a[i-5:i]]
  old=[x[2]-x[3] for x in a[i-25:i-5]]
  if statistics.mean(recent)>=.65*statistics.mean(old):return 0
  return 1 if c>hi else -1 if c<lo else 0
 if name=='failed_breakout':
  bar=a[i];return -1 if bar[2]>hi and c<hi else 1 if bar[3]<lo and c>lo else 0
 if name=='trend_pullback':
  avg=sma([x[4] for x in a[:i+1]],200)
  return 1 if c>avg and a[i-1][4]<a[i-2][4] and c>a[i-1][2] else -1 if c<avg and a[i-1][4]>a[i-2][4] and c<a[i-1][3] else 0
 return 0
def simulate(a,name,cost=.002,slip=0):
 trades=[];i=205
 while i<len(a)-2:
  side=signal(a,i,name)
  if not side:i+=1;continue
  vol=atr(a[:i+1],20)
  if not vol or vol<=0:i+=1;continue
  raw=a[i+1][1];entry=raw+side*raw*slip
  stop=entry-side*2*vol
  if stop<=0:i+=1;continue
  highwater=entry;lowwater=entry;end=min(i+60,len(a)-1)
  exitprice=a[end][4];exit_i=end
  for j in range(i+1,end+1):
   _,o,h,l,c=a[j]
   if (l<=stop if side==1 else h>=stop):
    exitprice=min(o,stop) if side==1 else max(o,stop);exit_i=j;break
   highwater=max(highwater,h);lowwater=min(lowwater,l)
   # Trail only from NEXT bar, so current high cannot raise stop before current low.
   if j<end:stop=max(stop,highwater-3*vol) if side==1 else min(stop,lowwater+3*vol)
  exitprice-=side*exitprice*slip
  r=(side*(exitprice-entry)-entry*cost)/(2*vol)
  trades.append((a[i+1][0],a[exit_i][0],r,side*(exitprice-entry)/entry-cost))
  i=exit_i+1
 return trades
