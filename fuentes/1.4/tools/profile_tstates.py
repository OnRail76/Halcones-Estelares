#!/usr/bin/env python3
import sys, argparse, bisect,collections
from pathlib import Path
p=Path(sys.argv[1]).resolve();sys.path.insert(0,str(p/'tests'))
from mini_z80 import VM,SYM
from boot_v15 import boot_to_game
labels=sorted((v,k) for k,v in SYM.items() if k not in ('entry',))
addrs=[a for a,_ in labels]
stats=collections.Counter();hist=collections.Counter()

def tstate(v):
 op=v.m[v.pc]; f=v.f; z=bool(f&64);c=bool(f&1)
 if op in (0x00,0x76,0xf3,0xfb,0xeb,0x0f,0x07):return 4
 if op==0xc9:return 10
 if op in (0xc5,0xd5,0xe5,0xf5):return 11
 if op in (0xc1,0xd1,0xe1,0xf1):return 10
 if op&0xcf==1:return 10
 if op&0xcf in (3,11):return 6
 if op&0xcf==9:return 11
 if op in (0x3a,0x32):return 13
 if op in (0x2a,0x22):return 16
 if op in (0x0a,0x1a,0x02,0x12):return 7
 if op&0xc7==6:return 10 if (op>>3)&7==6 else 7
 if op&0xc7 in (4,5):return 11 if (op>>3)&7==6 else 4
 if 0x40<=op<=0x7f:return 7 if ((op>>3)&7==6 or op&7==6) else 4
 if 0x80<=op<=0xbf:return 7 if op&7==6 else 4
 if op in (0xc6,0xd6,0xe6,0xee,0xf6,0xfe):return 7
 if op in (0xc3,):return 10
 if op&0xc7==0xc2:return 10
 if op==0xcd:return 17
 if op&0xc7==0xc4:
  cc=(op>>3)&7;cond=([not z,z,not c,c,False,False,False,False][cc]);return 17 if cond else 10
 if op&0xc7==0xc0:
  cc=(op>>3)&7;cond=([not z,z,not c,c,False,False,False,False][cc]);return 11 if cond else 5
 if op==0x10:return 8 if v.r[0]==1 else 13
 if op in (0x18,0x20,0x28,0x30,0x38):
  if op==0x18:return 12
  cc={0x20:not z,0x28:z,0x30:not c,0x38:c}[op];return 12 if cc else 7
 if op==0xd3:return 11
 if op==0xed:
  x=v.m[v.pc+1]
  if x==0x78:return 12
  if x in (0x47,):return 9
  if x in (0x5e,):return 8
  if x in (0x4d,):return 14
  if x==0xa0:return 16
  if x in (0x4b,0x5b,0x6b,0x7b):return 20
  if x in (0xb0,0xb8):return max(16,21*v.r16(0)-5)
 if op==0xcb:
  x=v.m[v.pc+1];return 12 if x&7==6 else 8
 if op in (0xdd,0xfd):
  x=v.m[v.pc+1]
  if x==0x21:return 14
  if x==0x23:return 10
  if x==0x19:return 15
  if x==0xe1:return 14
  if x==0xe5:return 15
  if x==0x36:return 19
  if x in (0x34,0x35):return 23
  if x in range(0x70,0x78) or (0x46<=x<=0x7e and x&7==6):return 19
 raise RuntimeError(f'unknown 0x{op:02x} at 0x{v.pc:04x}')

v=VM();total=[0]
ori=v.step
def wrapped():
 pc=v.pc
 cost=tstate(v)
 key=labels[bisect.bisect_right(addrs,pc)-1][1] if bisect.bisect_right(addrs,pc) else 'unknown'
 stats[key]+=cost;hist[key]+=1;total[0]+=cost
 return ori()
v.step=wrapped
# don't count boot
boot_to_game(v)
frame_cycles=[]
for f in range(180):
 v.keys={'SPACE'} if f%4==1 else set()
 before=total[0]
 v.step();v.run_to(lambda q:q.pc==SYM['main_loop'],steps=500_000)
 cost=total[0]-before
 frame_cycles.append(cost)
 if f%15==0: print(f'{f:03} {cost:,} T-states (no ULA contention, no ISR) {v.steps} instructions cumulative')
print('T-state min/max/mean:',min(frame_cycles),max(frame_cycles),round(sum(frame_cycles)/len(frame_cycles)))
print('25Hz update budget 139776; over-budget frame count:',sum(c>139776 for c in frame_cycles))
print('top ops cost:')
for k,n in stats.most_common(26):print(f'{k:28} {n:>12,d} {hist[k]:>12,d}')
