import struct
from z80emu import Z80,disasm
from pathlib import Path
TAP=str(Path(__file__).resolve().parents[2]/'build'/'HALCONES_ESTELARES_V281.tap')
def blocks(tap=None):
    d=open(tap or TAP,'rb').read();i=0;out=[];hdr=None
    while i<len(d):
        L=struct.unpack('<H',d[i:i+2])[0];b=d[i+2:i+2+L]
        if b[0]==0:hdr=struct.unpack('<HHH',b[12:18])+(b[1],)
        else:out.append((hdr,b[1:-1]))
        i+=2+L
    return out
def load(z,tap=None):
    for (ln,p1,p2,t),data in blocks(tap):
        if t==3:z.m[p1:p1+len(data)]=data
