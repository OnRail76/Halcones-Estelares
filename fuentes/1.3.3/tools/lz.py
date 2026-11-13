"""Compresor LZ sencillo para el Z80 (descompresor lz_unpack en title_screen.asm).
Formato: byte de control C
  C=0          -> fin
  C=1..127     -> C literales a continuacion
  C=128..191   -> copia de C-125 bytes desde destino-D, D en 1 byte (1..255)
  C=192..255   -> copia de C-189 bytes desde destino-D, D en 2 bytes"""
from collections import defaultdict
def compress(data):
    out=bytearray();i=0;lit=bytearray();n=len(data);idx=defaultdict(list)
    def flush():
        nonlocal lit
        while lit:
            ch=lit[:127];out.append(len(ch));out.extend(ch);lit=lit[127:]
    while i<n:
        best=(0,0)
        if i+3<=n:
            for p in reversed(idx[bytes(data[i:i+3])][-200:]):
                l=0
                while i+l<n and l<66 and data[p+l]==data[i+l]:l+=1
                d=i-p;cost=2 if d<256 else 3
                if best[0]==0 or l-cost>best[0]-(2 if best[1]<256 else 3):best=(l,d)
        if best[0]>=3 and not (best[1]>=256 and best[0]<4):
            flush();l,d=best
            if d<256:out.append(128+l-3);out.append(d)
            else:out.append(192+l-3);out.append(d&255);out.append(d>>8)
            for k in range(i,i+l):
                if k+3<=n:idx[bytes(data[k:k+3])].append(k)
            i+=l
        else:
            if i+3<=n:idx[bytes(data[i:i+3])].append(i)
            lit.append(data[i]);i+=1
    flush();out.append(0);return bytes(out)
def decompress(c):
    out=bytearray();i=0
    while True:
        k=c[i];i+=1
        if k==0:return bytes(out)
        if k<128:out+=c[i:i+k];i+=k;continue
        if k<192:l=k-125;d=c[i];i+=1
        else:l=k-189;d=c[i]|c[i+1]<<8;i+=2
        for _ in range(l):out.append(out[-d])
