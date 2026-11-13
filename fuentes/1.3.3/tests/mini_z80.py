#!/usr/bin/env python3
"""Partial Z80 interpreter for *headless smoke testing*, not a cycle-accurate emulator.
Only covers instructions emitted by the bundled mini assembler. The actual TAP needs Fuse testing.
"""
from pathlib import Path
import json,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
SYM=json.loads((ROOT/'build/starter.sym.json').read_text())
class VM:
 def __init__(self):
  self.m=bytearray(65536);binary=(ROOT/'build/starter.bin').read_bytes();self.m[32768:32768+len(binary)]=binary
  low=(ROOT/'build/sprites_reloc_v22.bin')
  if low.exists():self.m[0x6000:0x6000+low.stat().st_size]=low.read_bytes()
  low11=(ROOT/'build/v11_bajo.bin')  # V1.1: rutinas frias tras los sprites
  if low11.exists() and low.exists():a=0x6000+low.stat().st_size;self.m[a:a+low11.stat().st_size]=low11.read_bytes()
  extra=(ROOT/'build/moai_bitmap_v19.bin')
  if extra.exists():self.m[0xf401:0xf401+extra.stat().st_size]=extra.read_bytes()
  jupiter=(ROOT/'build/jupiter_bitmap_v20.bin')
  if jupiter.exists():self.m[0xf611:0xf611+jupiter.stat().st_size]=jupiter.read_bytes()
  gameover=(ROOT/'build/gameover_lz.bin')  # V1.2: GAME OVER comprimido LZ
  if gameover.exists():self.m[0xf799:0xf799+gameover.stat().st_size]=gameover.read_bytes()
  self.r=[0]*8 # B,C,D,E,H,L,(HL),A
  self.sp=0xffff;self.pc=32768;self.f=0;self.ix=0;self.iy=0;self.ir=0;self.im=1;self.steps=0;self.keys=set();self.port_writes=0
  # ROM font mock for static analysis and proof of tile drawing, not Sinclair ROM pixels.
  try:font=ImageFont.truetype('DejaVuSansMono.ttf',8)
  except OSError:font=ImageFont.load_default()
  for ch in range(32,128):
   im=Image.new('1',(8,8),0);d=ImageDraw.Draw(im);d.text((1,-1),chr(ch),font=font,fill=1)
   for y in range(8):
    b=0
    for x in range(8):b=(b<<1)|int(im.getpixel((x,y))>0)
    self.m[0x3d00+(ch-32)*8+y]=b
 def rd(self):
  x=self.m[self.pc];self.pc=(self.pc+1)&65535;return x
 def word(self):
  l=self.rd();return l|self.rd()<<8
 def r16(self,rr):
  if rr==3:return self.sp
  i=rr*2;return (self.r[i]<<8)|self.r[i+1]
 def set16(self,rr,v):
  v&=65535
  if rr==3:self.sp=v;return
  i=rr*2;self.r[i]=v>>8;self.r[i+1]=v&255
 def hl(self):return self.r16(2)
 def sethl(self,v):self.set16(2,v)
 def reg(self,n):return self.m[self.hl()] if n==6 else self.r[n]
 def setreg(self,n,v):
  if n==6:self.m[self.hl()]=v&255
  else:self.r[n]=v&255
 def push(self,v):
  self.sp=(self.sp-1)&65535;self.m[self.sp]=(v>>8)&255
  self.sp=(self.sp-1)&65535;self.m[self.sp]=v&255
 def pop(self):
  v=self.m[self.sp]|self.m[(self.sp+1)&65535]<<8;self.sp=(self.sp+2)&65535;return v
 def flags(self,v,carry=0):self.f=(0x40 if (v&255)==0 else 0) | (1 if carry else 0) | (0x80 if v&0x80 else 0)  # V1.2: tambien signo
 def cond(self,idx):
  z=bool(self.f&0x40);c=bool(self.f&1);pv=bool(self.f&4);sg=bool(self.f&0x80)
  return [not z,z,not c,c,not pv,pv,not sg,sg][idx]  # V1.1: PO/PE/P/M reales
 def alu(self,which,v):
  a=self.r[7]
  if which==0:res=a+v;self.flags(res,res>255);self.r[7]=res&255
  elif which==2:res=a-v;self.flags(res,res<0);self.r[7]=res&255
  elif which==4:self.r[7]=a&v;self.flags(self.r[7])
  elif which==5:self.r[7]=a^v;self.flags(self.r[7])
  elif which==6:self.r[7]=a|v;self.flags(self.r[7])
  elif which==7:self.flags(a-v,a<v)
  else:raise RuntimeError('alu mode '+str(which))
 def portread(self):
  b=self.r[0];v=0xff
  if b==0xfb and 'Q' in self.keys:v&=~1
  if b==0xfd and 'A' in self.keys:v&=~1
  if b==0xdf:
   if 'P' in self.keys:v&=~1
   if 'O' in self.keys:v&=~2
  if b==0x7f and 'SPACE' in self.keys:v&=~1
  return v
 def signed(self,v):return v-256 if v&128 else v
 def step(self):
  # V1.1: este interprete no lleva reloj IM2; cada tick de juego recibe aqui
  # las 2 interrupciones que tick_wait espera (25 ticks/s en el Spectrum).
  if self.pc==SYM.get('tick_wait',-1):self.m[SYM['tick_irqs']]=2
  # V1.3: la espera sin efecto ya no es HALT sino un bucle que mira tick_irqs:
  # aqui hace de la interrupcion que llegaria.
  if self.pc==SYM.get('snd_rest_loop',-1):self.m[SYM['tick_irqs']]=(self.m[SYM['tick_irqs']]+1)&255
  at=self.pc;op=self.rd();self.steps+=1
  if op in (0x00,0x76,0xf3,0xfb):return
  if op==0xc9:self.pc=self.pop();return
  if op==0xeb:
   d=self.r16(1);self.set16(1,self.hl());self.sethl(d);return
  if op==0x2f:self.r[7]^=0xff;return  # V1.1: CPL
  if op==0x37:self.f|=1;return  # V1.1: SCF
  if op==0x3f:self.f^=1;return  # V1.1: CCF
  if op==0x1f:  # V1.1: RRA
   a=self.r[7];self.r[7]=(a>>1)|((self.f&1)<<7);self.f=(self.f&0xfe)|(a&1);return
  if op in (0x0f,0x07):
   a=self.r[7];self.r[7]=((a>>1)|(a<<7))&255 if op==0xf else ((a<<1)|(a>>7))&255
   self.f=(self.f&0x40)|(a&1 if op==0xf else a>>7);return
  if op in (0xc5,0xd5,0xe5,0xf5):
   self.push(self.r16((op>>4)&3) if op!=0xf5 else (self.r[7]<<8)|self.f);return
  if op in (0xc1,0xd1,0xe1,0xf1):
   v=self.pop()
   if op==0xf1:self.r[7]=v>>8;self.f=v&255
   else:self.set16((op>>4)&3,v)
   return
  if op&0xcf==0x01:self.set16((op>>4)&3,self.word());return
  if op&0xcf==0x03:self.set16((op>>4)&3,self.r16((op>>4)&3)+1);return
  if op&0xcf==0x0b:self.set16((op>>4)&3,self.r16((op>>4)&3)-1);return
  if op&0xcf==0x09:
   rr=(op>>4)&3;value=self.hl()+self.r16(rr);self.sethl(value);self.f=(self.f&0x40)|(1 if value>65535 else 0);return
  if op in (0x3a,0x32,0x2a,0x22):
   addr=self.word()
   if op==0x3a:self.r[7]=self.m[addr]
   elif op==0x32:self.m[addr]=self.r[7]
   elif op==0x2a:self.sethl(self.m[addr]|(self.m[(addr+1)&65535]<<8))
   else:self.m[addr]=self.r[5];self.m[(addr+1)&65535]=self.r[4]
   return
  if op in (0x0a,0x1a):self.r[7]=self.m[self.r16(0 if op==0x0a else 1)];return
  if op in (0x02,0x12):self.m[self.r16(0 if op==0x02 else 1)]=self.r[7];return
  if op&0xc7==0x06:
   r=(op>>3)&7;self.setreg(r,self.rd());return
  if op&0xc7 in (0x04,0x05):
   r=(op>>3)&7;v=(self.reg(r)+(1 if op&7==4 else -1))&255
   self.setreg(r,v);self.f=(self.f&1)|(0x40 if v==0 else 0);return
  if 0x40<=op<=0x7f:
   if op==0x76:return
   self.setreg((op>>3)&7,self.reg(op&7));return
  if 0x80<=op<=0xbf:self.alu((op>>3)&7,self.reg(op&7));return
  if op in (0xc6,0xd6,0xe6,0xee,0xf6,0xfe):
   self.alu({0xc6:0,0xd6:2,0xe6:4,0xee:5,0xf6:6,0xfe:7}[op],self.rd());return
  if op==0xc3:self.pc=self.word();return
  if op&0xc7==0xc2:
   addr=self.word()
   if self.cond((op>>3)&7):self.pc=addr
   return
  if op==0xcd:
   addr=self.word();self.push(self.pc);self.pc=addr;return
  if op&0xc7==0xc4:
   addr=self.word()
   if self.cond((op>>3)&7):self.push(self.pc);self.pc=addr
   return
  if op&0xc7==0xc0:
   if self.cond((op>>3)&7):self.pc=self.pop()
   return
  if op==0x10:
   j=self.signed(self.rd());self.r[0]=(self.r[0]-1)&255
   if self.r[0]:self.pc=(self.pc+j)&65535
   return
  if op in (0x18,0x20,0x28,0x30,0x38):
   j=self.signed(self.rd());which={0x20:0,0x28:1,0x30:2,0x38:3}.get(op)
   if which is None or self.cond(which):self.pc=(self.pc+j)&65535
   return
  if op==0xd3:self.rd();self.port_writes+=1;return
  if op==0xdb:self.rd();self.r[7]=0xff;return  # V1.1: IN A,(n) - sin Kempston (bus flotante)
  if op==0x08:  # V1.1: EX AF,AF'
   a2=getattr(self,'af2',(0,0));self.af2=(self.r[7],self.f);self.r[7],self.f=a2;return
  if op==0xed:
   x=self.rd()
   if x==0x78:self.r[7]=self.portread();return
   if x==0x47:self.ir=self.r[7];return # LD I,A (real Z80)
   if x in (0x42,0x52):  # V1.1: SBC HL,BC / SBC HL,DE
    v=self.r16(0 if x==0x42 else 1);res=self.hl()-v-(self.f&1);self.set16(2,res&65535)
    self.f=(1 if res<0 else 0)|(0x40 if res&65535==0 else 0)|(0x80 if res&0x8000 else 0)|2;return
   if x==0x5e:self.im=2;return     # IM 2 (real Z80)
   if x==0x4d:self.pc=self.pop();return # RETI (real Z80)
   if x in (0x43,0x53,0x63,0x73):  # V1.2: LD (nn),BC/DE/HL/SP
    addr=self.word();v=self.r16({0x43:0,0x53:1,0x63:2,0x73:3}[x]);self.m[addr]=v&255;self.m[(addr+1)&65535]=v>>8;return
   if x in (0x4b,0x5b,0x6b,0x7b):
    addr=self.word();rr={0x4b:0,0x5b:1,0x6b:2,0x7b:3}[x];self.set16(rr,self.m[addr]|(self.m[(addr+1)&65535]<<8));return
   if x==0xa0:  # LDI; Z80 preserves carry, updates P/V and H/N
    src=self.hl();dst=self.r16(1)
    self.m[dst]=self.m[src]
    self.sethl(src+1);self.set16(1,dst+1)
    bc=(self.r16(0)-1)&65535;self.set16(0,bc)
    self.f=(self.f&0xc1)|(0x04 if bc else 0)
    return
   if x==0xb8:
    n=self.r16(0);src=self.hl();dst=self.r16(1)
    for i in range(n):self.m[(dst-i)&65535]=self.m[(src-i)&65535]
    self.sethl(src-n);self.set16(1,dst-n);self.set16(0,0)
    return
   if x==0xb0:
    n=self.r16(0);src=self.hl();dst=self.r16(1)
    if dst==src+1 and n:val=self.m[src];self.m[dst:dst+n]=bytes([val])*n
    elif src<dst<src+n:  # V1.2: solapado hacia delante, byte a byte como el Z80
     for k in range(n):self.m[(dst+k)&65535]=self.m[(src+k)&65535]
    else:self.m[dst:dst+n]=self.m[src:src+n]
    self.sethl(src+n);self.set16(1,dst+n);self.set16(0,0)
    return
   raise RuntimeError(f'unknown ED {x:02x} at {at:04x}')
  if op==0xcb:
   x=self.rd();r=x&7
   if 0x40<=x<0x80:
    v=self.reg(r);b=(x>>3)&7;self.f=(self.f&1)|(0x40 if (v&(1<<b))==0 else 0);return
   if x>=0x80:  # V1.1: RES / SET b,r
    b=(x>>3)&7;v=self.reg(r);v=(v|(1<<b)) if x>=0xc0 else (v&~(1<<b));self.setreg(r,v&255);return
   raise RuntimeError(f'unknown CB {x:02x} at {at:04x}')
  if op in (0xdd,0xfd):
   x=self.rd();prefix='ix' if op==0xdd else 'iy';idx=getattr(self,prefix)
   if x==0x21:setattr(self,prefix,self.word());return
   if x==0x23:setattr(self,prefix,(idx+1)&65535);return
   if x==0x19:setattr(self,prefix,(idx+self.r16(1))&65535);return
   if x in (0x09,0x29,0x39):  # V1.2: ADD IX,BC/IX/SP
    v={0x09:self.r16(0),0x29:idx,0x39:self.sp}[x];setattr(self,prefix,(idx+v)&65535);return
   if x==0x2b:setattr(self,prefix,(idx-1)&65535);return
   if x==0xe9:self.pc=idx;return
   if x==0x22:a=self.word();self.m[a]=idx&255;self.m[(a+1)&65535]=idx>>8;return
   if x==0x2a:a=self.word();setattr(self,prefix,self.m[a]|self.m[(a+1)&65535]<<8);return
   if x in (0xe1,0xe5):
    if x==0xe1:setattr(self,prefix,self.pop())
    else:self.push(idx)
    return
   off=self.signed(self.rd());addr=(idx+off)&65535
   if x==0x36:self.m[addr]=self.rd();return
   if x==0x34:self.m[addr]=(self.m[addr]+1)&255;return
   if x==0x35:self.m[addr]=(self.m[addr]-1)&255;return
   if 0x46<=x<=0x7e and x&7==6:self.r[(x>>3)&7]=self.m[addr];return
   if 0x70<=x<=0x77:self.m[addr]=self.reg(x&7);return
   if x&0xc7==0x86:self.alu((x>>3)&7,self.m[addr]);return  # V1.1: ADD/SUB/AND/XOR/OR/CP (IX/IY+d)
   raise RuntimeError(f'unknown {prefix} {x:02x} at {at:04x}')
  raise RuntimeError(f'unknown opcode {op:02x} @ {at:04x} after {self.steps} steps')
 def run_to(self,check,steps=1_000_000):
  for _ in range(steps):
   if check(self):return self.steps
   self.step()
  raise TimeoutError(f'at {self.pc:04x} after {self.steps}, waiting for {check}')
 def val(self,label):return self.m[SYM[label]]
 def set(self,label,val):self.m[SYM[label]]=val
 def render(self,out,scale=3):
  palette=[(0,0,0),(0,0,180),(180,0,0),(175,0,175),(0,140,0),(0,150,150),(170,150,0),(180,180,180)]
  bright=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
  im=Image.new('RGB',(256,192));pixels=im.load()
  for y in range(192):
   for x in range(256):
    byte_addr=0x4000+((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+(x>>3)
    bit=(self.m[byte_addr]>>(7-(x&7)))&1
    attr=self.m[0x5800+(y//8)*32+x//8];colors=bright if attr&0x40 else palette
    ink=attr&7;paper=(attr>>3)&7
    pixels[x,y]=colors[ink if bit else paper]
  im.resize((256*scale,192*scale),Image.Resampling.NEAREST).save(out)
if __name__=='__main__':
 v=VM()
 # Emulated keyboard: idle to release, then press only at title wait.
 def boot_keys(m):
  return m.pc==SYM['sp_wait']
 pressed=False
 for i in range(2_000_000):
  if boot_keys(v):pressed=True
  v.keys={'SPACE'} if pressed else set()
  if v.pc==SYM['main_loop']:
   print('game started after',i,'instructions', 'phase',v.val('phase'),'sector',v.val('sector'))
   v.render(ROOT/'build/ACTUAL_Z80_SIMULATED.png')
   break
  v.step()
 else:raise RuntimeError(f'failed boot at pc {v.pc:04x} after 2M steps')
