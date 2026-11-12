"""Lienzo ZX Spectrum: pixeles 256x192 + atributos 32x24 (tinta/papel/brillo por celda)."""
from PIL import Image
P=[(0,0,0),(0,0,205),(205,0,0),(205,0,205),(0,205,0),(0,205,205),(205,205,0),(205,205,205)]
B=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
BLK,BLU,RED,MAG,GRN,CYN,YEL,WHT=range(8)
def A(ink,paper=0,bright=1,flash=0):return ink|paper<<3|bright<<6|flash<<7
class ZX:
    def __init__(s):s.px=[[0]*256 for _ in range(192)];s.at=[[A(WHT)]*32 for _ in range(24)]
    @classmethod
    def from_scr(c,path):
        s=c();m=open(path,'rb').read()
        for y in range(192):
            for xb in range(32):
                byte=m[((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2)|xb]
                for b in range(8):s.px[y][xb*8+b]=1 if byte&(128>>b) else 0
        for r in range(24):
            for c in range(32):s.at[r][c]=m[6144+r*32+c]
        return s
    @classmethod
    def from_mem(c,m):
        s=c()
        for y in range(192):
            for xb in range(32):
                byte=m[0x4000+(((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2)|xb)]
                for b in range(8):s.px[y][xb*8+b]=1 if byte&(128>>b) else 0
        for r in range(24):
            for c in range(32):s.at[r][c]=m[0x5800+r*32+c]
        return s
    def clear(s,x0,y0,x1,y1):
        for y in range(y0,y1):
            for x in range(x0,x1):s.px[y][x]=0
    def plot(s,x,y,v=1):
        if 0<=x<256 and 0<=y<192:s.px[y][x]=v
    def attr(s,c0,r0,c1,r1,a):
        for r in range(r0,r1):
            for c in range(c0,c1):s.at[r][c]=a
    def blit(s,x,y,rows,mode='or'):
        for j,row in enumerate(rows):
            for i,ch in enumerate(row):
                if ch in '#X@':s.plot(x+i,y+j,1)
                elif mode=='set' and ch in '.':s.plot(x+i,y+j,0)
    def hline(s,x0,x1,y,pat=None):
        for x in range(x0,x1):
            if pat is None or pat[(x-x0)%len(pat)]=='#':s.plot(x,y)
    def vline(s,x,y0,y1,pat=None):
        for y in range(y0,y1):
            if pat is None or pat[(y-y0)%len(pat)]=='#':s.plot(x,y)
    def rect(s,x0,y0,x1,y1):
        s.hline(x0,x1,y0);s.hline(x0,x1,y1-1);s.vline(x0,y0,y1);s.vline(x1-1,y0,y1)
    def img(s,scale=3):
        im=Image.new('RGB',(256,192));p=im.load()
        for y in range(192):
            for x in range(256):
                a=s.at[y>>3][x>>3];pal=B if a&64 else P
                p[x,y]=pal[a&7] if s.px[y][x] else pal[(a>>3)&7]
        return im.resize((256*scale,192*scale),Image.NEAREST)

def to_scr(z):
    m=bytearray(6912)
    for y in range(192):
        for xb in range(32):
            v=0
            for b in range(8):
                if z.px[y][xb*8+b]:v|=128>>b
            m[((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2)|xb]=v
    for r in range(24):
        for c in range(32):m[6144+r*32+c]=z.at[r][c]
    return bytes(m)
ZX.to_scr=to_scr
