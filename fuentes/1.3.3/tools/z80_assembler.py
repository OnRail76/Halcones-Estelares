#!/usr/bin/env python3
"""Small, deterministic Z80 assembler for the exact documented subset used by GRIT.
Generates flat 0x8000 machine code; no external assembler dependency.
Usage: python3 build_asm.py src/grit.asm build/grit.bin
"""
import ast, re, sys, pathlib, json
R={'b':0,'c':1,'d':2,'e':3,'h':4,'l':5,'(hl)':6,'a':7}
RR={'bc':0,'de':1,'hl':2,'sp':3}
COND={'nz':0,'z':1,'nc':2,'c':3,'po':4,'pe':5,'p':6,'m':7}
class A:
 def __init__(self,source):
  self.lines=source.splitlines();self.labels={};self.data=bytearray();self.pc=0;self.passno=0;self.listing=[]
 def ex(self,x):
  x=x.strip()
  if x.startswith("'") and x.endswith("'") and len(x)==3:return ord(x[1])
  try:
   node=ast.parse(x,mode='eval').body
   def walk(t):
    if isinstance(t,ast.Constant) and isinstance(t.value,int):return t.value
    if isinstance(t,ast.Name):
     if t.id not in self.labels:
      if self.passno==0:return 0
      raise ValueError('unknown '+t.id)
     return self.labels[t.id]
    if isinstance(t,ast.BinOp):
     a,b=walk(t.left),walk(t.right)
     ops={ast.Add:lambda:a+b,ast.Sub:lambda:a-b,ast.Mult:lambda:a*b,ast.FloorDiv:lambda:a//b,ast.BitAnd:lambda:a&b,ast.BitOr:lambda:a|b,ast.BitXor:lambda:a^b,ast.LShift:lambda:a<<b,ast.RShift:lambda:a>>b}
     for typ,fn in ops.items():
      if isinstance(t.op,typ):return fn()
    if isinstance(t,ast.UnaryOp):
     v=walk(t.operand)
     if isinstance(t.op,ast.USub):return -v
     if isinstance(t.op,ast.Invert):return ~v
    raise ValueError('invalid expression '+x)
   return walk(node)
  except (SyntaxError,ValueError,ZeroDivisionError) as e:raise ValueError(f'expression {x!r}: {e}')
 def emit(self,*bs):
  for b in bs:
   if self.passno==1:
    if not 0<=b<=255:raise ValueError(f'byte out of range: {b}')
    self.data.append(b)
   self.pc+=1
 def w(self,v):
  self.emit(v&255,(v>>8)&255)
 def split(self,s):
  vals=[];curr='';quote=None;nest=0
  for c in s:
   if c in ('"',"'"):
    if quote is None:quote=c
    elif quote==c:quote=None
   if c=='(' and not quote:nest+=1
   if c==')' and not quote:nest-=1
   if c==',' and not quote and nest==0:vals.append(curr.strip());curr='';continue
   curr+=c
  if curr.strip():vals.append(curr.strip())
  return vals
 def idx(self,s):
  m=re.fullmatch(r'\((ix|iy)\s*([+-])\s*(\d+)\)',s)
  if not m:return None
  p=0xdd if m[1]=='ix' else 0xfd;d=int(m[3])*(1 if m[2]=='+' else -1)
  if not -128<=d<=127:raise ValueError('bad IX displacement')
  return p,d&255
 def instr(self,s):
  p=s.split(None,1);op=p[0].lower();args=[a.lower() for a in self.split(p[1])] if len(p)>1 else []
  if op=='org':
   address=self.ex(args[0]);
   if self.passno==1 and self.pc and self.pc!=address:raise ValueError('multiple ORG')
   self.pc=address;return
  if op=='equ':raise ValueError('EQU must follow a label')
  if op=='db':
   for x in self.split(p[1]):
    if x.startswith('"') and x.endswith('"'):self.emit(*x[1:-1].encode('ascii'))
    else:self.emit(self.ex(x)&255)
   return
  if op=='dw':
   for x in args:self.w(self.ex(x))
   return
  if op=='ds':
   for _ in range(self.ex(args[0])):self.emit(0)
   return
  simple={'nop':0x00,'halt':0x76,'di':0xf3,'ei':0xfb,'ret':0xc9,'rrca':0x0f,'rlca':0x07,'rra':0x1f,'rla':0x17,'scf':0x37,'ccf':0x3f,'cpl':0x2f,'exx':0xd9}
  if op in simple and not args:self.emit(simple[op]);return
  if op=='reti':self.emit(0xed,0x4d);return
  if op=='im' and args==['2']:self.emit(0xed,0x5e);return
  if op=='ldi':self.emit(0xed,0xa0);return
  if op=='ldir':self.emit(0xed,0xb0);return
  if op=='lddr':self.emit(0xed,0xb8);return
  if op=='neg':self.emit(0xed,0x44);return
  if op=='sbc' and args[0]=='hl' and args[1] in RR:self.emit(0xed,0x42+16*RR[args[1]]);return
  if op=='ex':
   if args==['de','hl']:self.emit(0xeb);return
   if args==["af","af'"]:self.emit(0x08);return
  if op=='push' or op=='pop':
   rr={'bc':0,'de':1,'hl':2,'af':3,'ix':2,'iy':2};prefix={'ix':0xdd,'iy':0xfd}
   if args[0] in prefix:self.emit(prefix[args[0]])
   self.emit((0xc5 if op=='push' else 0xc1)+rr[args[0]]*16);return
  if op=='inc' or op=='dec':
   x=args[0];idx=self.idx(x)
   if idx:self.emit(idx[0],0x34 if op=='inc' else 0x35,idx[1]);return
   if x in R:self.emit((0x04 if op=='inc' else 0x05)+R[x]*8);return
   if x in RR:self.emit((0x03 if op=='inc' else 0x0b)+RR[x]*16);return
   if x in ('ix','iy'):self.emit(0xdd if x=='ix' else 0xfd,0x23 if op=='inc' else 0x2b);return
  if op=='add':
   x,y=args
   if x=='hl' and y in RR:self.emit(0x09+RR[y]*16);return
   if x in ('ix','iy') and y in ('bc','de',x,'sp'):
    self.emit(0xdd if x=='ix' else 0xfd,0x09+{'bc':0,'de':1,x:2,'sp':3}[y]*16);return
   if x=='a':return self.arith('add',y)
  if op in ('sub','and','or','xor','cp'):
   if len(args)==1:return self.arith(op,args[0])
   if op=='sub' and args[0]=='a':return self.arith(op,args[1])
  if op=='ld':
   x,y=args;ix=self.idx(x);iy=self.idx(y)
   if x=='i' and y=='a':self.emit(0xed,0x47);return
   if x in R and y in R:self.emit(0x40+R[x]*8+R[y]);return
   if x in R and iy:self.emit(iy[0],0x46+R[x]*8,iy[1]);return
   if ix and y in R:self.emit(ix[0],0x70+R[y],ix[1]);return
   if ix:self.emit(ix[0],0x36,ix[1],self.ex(y)&255);return
   if x in R:
    if x=='a' and y.startswith('(') and y.endswith(')') and y not in ('(hl)',):
     if y=='(bc)':self.emit(0x0a);return
     if y=='(de)':self.emit(0x1a);return
     self.emit(0x3a);self.w(self.ex(y[1:-1]));return
    self.emit(0x06+R[x]*8,self.ex(y)&255);return
   if x in ('bc','de','hl','sp','ix','iy'):
    if x in ('bc','de','hl','sp') and y.startswith('(') and y.endswith(')'):
     if x=='hl':self.emit(0x2a)
     else:self.emit(0xed,{'bc':0x4b,'de':0x5b,'sp':0x7b}[x])
     self.w(self.ex(y[1:-1]));return
    if x=='sp' and y=='hl':self.emit(0xf9);return
    if x in ('ix','iy'):self.emit(0xdd if x=='ix' else 0xfd,0x21);self.w(self.ex(y));return
    self.emit(0x01+16*RR[x]);self.w(self.ex(y));return
   if x.startswith('(') and x.endswith(')'):
    if x=='(bc)' and y=='a':self.emit(0x02);return
    if x=='(de)' and y=='a':self.emit(0x12);return
    if y=='a':self.emit(0x32);self.w(self.ex(x[1:-1]));return
    if y=='hl':self.emit(0x22);self.w(self.ex(x[1:-1]));return
    if y in ('bc','de','sp'):self.emit(0xed,{'bc':0x43,'de':0x53,'sp':0x73}[y]);self.w(self.ex(x[1:-1]));return
   raise ValueError('unsupported LD '+s)
  if op in ('jp','call'):
   if len(args)==1:
    if op=='jp' and args[0]=='(hl)':self.emit(0xe9);return
    self.emit(0xc3 if op=='jp' else 0xcd);self.w(self.ex(args[0]));return
   if args[0] in COND:
    self.emit((0xc2 if op=='jp' else 0xc4)+8*COND[args[0]]);self.w(self.ex(args[1]));return
  if op=='ret' and len(args)==1 and args[0] in COND:self.emit(0xc0+8*COND[args[0]]);return
  if op=='djnz' or op=='jr':
   if op=='djnz':base=0x10;target=args[0]
   elif len(args)==1:base=0x18;target=args[0]
   else:
    base={'nz':0x20,'z':0x28,'nc':0x30,'c':0x38}[args[0]];target=args[1]
   dest=self.ex(target);offset=dest-(self.pc+2)
   if self.passno==1 and not -128<=offset<=127:raise ValueError(f'JR out of range {s}: {offset}')
   self.emit(base,offset&255);return
  if op=='bit' and args[1] in R:self.emit(0xcb,0x40+8*self.ex(args[0])+R[args[1]]);return
  if op=='set' and args[1] in R:self.emit(0xcb,0xc0+8*self.ex(args[0])+R[args[1]]);return
  if op=='res' and args[1] in R:self.emit(0xcb,0x80+8*self.ex(args[0])+R[args[1]]);return
  if op=='in' and args==['a','(c)']:self.emit(0xed,0x78);return
  if op=='in' and args[0]=='a' and args[1].startswith('('):self.emit(0xdb,self.ex(args[1][1:-1])&255);return
  if op=='out' and args==['(c)','a']:self.emit(0xed,0x79);return
  if op=='out' and args[1]=='a':self.emit(0xd3,self.ex(args[0][1:-1])&255);return
  if op=='rst':self.emit(0xc7+self.ex(args[0]));return
  raise ValueError('unsupported instruction '+s)
 def arith(self,op,y):
  base={'add':0x80,'sub':0x90,'and':0xa0,'xor':0xa8,'or':0xb0,'cp':0xb8}[op]
  imm={'add':0xc6,'sub':0xd6,'and':0xe6,'xor':0xee,'or':0xf6,'cp':0xfe}[op]
  idx=self.idx(y)
  if idx:self.emit(idx[0],base+6,idx[1]);return
  if y in R:self.emit(base+R[y]);return
  self.emit(imm,self.ex(y)&255)
 def run(self):
  for numpass in (0,1):
   self.passno=numpass;self.pc=0;self.data=bytearray()
   for n,orig in enumerate(self.lines,1):
    s=orig.split(';',1)[0].strip()
    if not s:continue
    try:
     mq=re.fullmatch(r'([A-Za-z_][A-Za-z_0-9]*)\s+equ\s+(.+)',s,re.I)
     if mq:
      # V1.1: NOMBRE equ VALOR (constantes y variables fuera del bloque cargado)
      if numpass==0:
       if mq[1] in self.labels:raise ValueError('duplicate label')
      self.labels[mq[1]]=self.ex(mq[2]);continue
     if ':' in s:
      lab,s=s.split(':',1);lab=lab.strip();s=s.strip()
      if numpass==0:
       if lab in self.labels:raise ValueError('duplicate label')
       self.labels[lab]=self.pc
     if not s:continue
     self.instr(s)
    except Exception as e:raise RuntimeError(f'line {n} ({orig}): {e}') from e
  return bytes(self.data)
def main():
 src=pathlib.Path(sys.argv[1]); dest=pathlib.Path(sys.argv[2]);dest.parent.mkdir(exist_ok=True,parents=True)
 a=A(src.read_text());b=a.run();dest.write_bytes(b)
 dest.with_suffix('.sym.json').write_text(json.dumps(a.labels,indent=2,sort_keys=True))
 print(f'assembled {len(b)} bytes, ORG 0x8000, end {0x8000+len(b):04X}; {len(a.labels)} labels')
if __name__=='__main__':main()
