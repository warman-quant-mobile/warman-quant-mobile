"""Additional exploratory indicators. Signals at completed close; fill next bar.
Research-only. No broker integration. Daily Turtle uses daily bars, never 20 hours.
"""
import math,statistics
def ema(values,n):
 out=[];v=None;k=2/(n+1)
 for x in values:
  v=x if v is None else k*x+(1-k)*v;out.append(v)
 return out
def rsi(values,n):
 if len(values)<n+1:return None
 changes=[values[i]-values[i-1] for i in range(len(values)-n,len(values))]
 gain=sum(max(x,0) for x in changes)/n;loss=sum(max(-x,0) for x in changes)/n
 return 100 if loss==0 else 100-100/(1+gain/loss)
def sma(values,n):
 return statistics.mean(values[-n:]) if len(values)>=n else None
def macd(values):
 if len(values)<35:return None
 a=ema(values,12);b=ema(values,26);hist=[x-y for x,y in zip(a,b)]
 sig=ema(hist,9)
 return hist[-1]-sig[-1],hist[-2]-sig[-2]
def stochastic(a,n=14,smooth=3):
 if len(a)<n+smooth:return None
 ks=[]
 for j in range(len(a)-smooth+1,len(a)+1):
  part=a[j-n:j];hi=max(x[2] for x in part);lo=min(x[3] for x in part)
  ks.append(50 if hi==lo else 100*(a[j-1][4]-lo)/(hi-lo))
 return statistics.mean(ks)
def atr(a,n=20):
 if len(a)<n+1:return None
 vals=[]
 for i in range(len(a)-n,len(a)):
  prev=a[i-1][4];vals.append(max(a[i][2]-a[i][3],abs(a[i][2]-prev),abs(a[i][3]-prev)))
 return statistics.mean(vals)
def decide(a,i,name):
 p=a[:i+1];cl=[x[4] for x in p];price=cl[-1]
 if name.startswith('rsi'):
  n=int(name[3]);v=rsi(cl,n);trend=sma(cl,200)
  if v is None or trend is None:return 0
  if price>trend and v<5:return 1
  if price<trend and v>95:return -1
  return 0
 if name.startswith('turtle'):
  n=int(name.split('_')[1])
  if i<n:return 0
  prior=a[i-n:i]
  return 1 if price>max(x[2] for x in prior) else -1 if price<min(x[3] for x in prior) else 0
 if name=='macd':
  m=macd(cl)
  return 1 if m and m[0]>0>=m[1] else -1 if m and m[0]<0<=m[1] else 0
 if name.startswith('stoch'):
  n=int(name.split('_')[1]);v=stochastic(p,n)
  if v is None:return 0
  return 1 if v<20 else -1 if v>80 else 0
 if name=='rsi2_macd':
  v=rsi(cl,2);m=macd(cl);trend=sma(cl,200)
  if v is None or m is None or trend is None:return 0
  return 1 if price>trend and v<15 and m[0]>m[1] else -1 if price<trend and v>85 and m[0]<m[1] else 0
 if name=='donchian_macd':
  if i<20:return 0
  m=macd(cl);prior=a[i-20:i]
  if not m:return 0
  return 1 if price>max(x[2] for x in prior) and m[0]>0 else -1 if price<min(x[3] for x in prior) and m[0]<0 else 0
 return 0
HOURLY=('rsi2','rsi3','rsi4','macd','stoch_5','stoch_14','rsi2_macd','donchian_macd')
DAILY=('turtle_20','turtle_55')
def simulate(a,name,cost=.002):
 """Independent candidate trades; ATR-based stop, Turtle trailing-channel exit."""
 trades=[];i=201 if name.startswith('rsi') else 55 if name.startswith('turtle') else 36
 while i<len(a)-2:
  side=decide(a,i,name)
  if not side:i+=1;continue
  entry=a[i+1][1];unit=atr(a[:i+1],20)
  if not unit or entry<=0:i+=1;continue
  stop=entry-side*2*unit
  if stop<=0:i+=1;continue
  turtle=name.startswith('turtle');maxhold=100 if turtle else 12
  end=min(i+maxhold,len(a)-1);price=a[end][4];exit_i=end
  for j in range(i+1,end+1):
   _,o,h,l,c=a[j]
   if (l<=stop if side==1 else h>=stop):
    price=min(o,stop) if side==1 else max(o,stop);exit_i=j;break
   if turtle and j>=11:
    prev=a[j-10:j];channel=min(x[3] for x in prev) if side==1 else max(x[2] for x in prev)
    if (c<channel if side==1 else c>channel):
     price=c;exit_i=j;break
   if not turtle and (h>=entry+side*4*unit if side==1 else l<=entry+side*4*unit):
    price=entry+side*4*unit;exit_i=j;break
  net=side*(price-entry)/entry-cost
  trades.append((a[i+1][0],a[exit_i][0],(side*(price-entry)-entry*cost)/(2*unit),net))
  i=exit_i+1
 return trades
