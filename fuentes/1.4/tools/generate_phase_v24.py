#!/usr/bin/env python3
"""Authentic ZX Spectrum 6912-byte intermission screen, RLE packed in main Z80.

Typography is original 5x7 bitmaps; the two-digit phase number is drawn in real
screen RAM by Z80 after decompression. This is NOT an image generation mockup.
"""
from pathlib import Path
from PIL import Image,ImageDraw
from tools.generate_title import GLYPHS
R=Path(__file__).resolve().parents[1]
BL=(0,0,0);Y=(255,255,0);CY=(0,255,255);W=(255,255,255); RED=(255,0,0)
glyphs=dict(GLYPHS)
glyphs['!']=['00100','00100','00100','00100','00100','00000','00100']
glyphs['¡']=['00100','00000','00100','00100','00100','00100','00100']
im=Image.new('RGB',(256,192),BL);d=ImageDraw.Draw(im)
def word(s,y,scale,color):
    gap=scale
    x=(256-(len(s)*(5*scale+gap)-gap))//2
    for ch in s:
        for yy,row in enumerate(glyphs[ch]):
            for xx,b in enumerate(row):
                if b=='1':d.rectangle((x+xx*scale,y+yy*scale,x+(xx+1)*scale-1,y+(yy+1)*scale-1),fill=color)
        x+=5*scale+gap
# Distinctive but lightweight 1984-era arcade win intermission.
for y,color in [(32,RED),(43,CY),(152,CY),(163,RED)]:
    for x in range(42,214,4):
        d.line([(x,y),(x+1,y)],fill=color)
word('¡MUY BIEN!',62,3,Y)
word('ENTRANDO EN FASE:',109,1,CY)
word('EUROPEAN SPACE FORCE',174,1,W)
# y126..132, columns 15 and 16 reserved for dynamic phase number.
pix=im.load();bitmap=bytearray(6144);attr=bytearray(768)
colours={BL:0, RED:2, CY:5, Y:6,W:7}
for cy in range(24):
    for cx in range(32):
        count={c:0 for c in colours if c!=BL}
        for y in range(cy*8,cy*8+8):
            for x in range(cx*8,cx*8+8):
                if pix[x,y]!=BL:count[pix[x,y]]+=1
        dominant=max(count,key=count.get)
        attr[cy*32+cx]=0x40|colours[dominant] if count[dominant] else 0x47
        if cy in (15,16) and cx in (15,16):attr[cy*32+cx]=0x45
        for y in range(cy*8,cy*8+8):
            off=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+cx
            bitmap[off]=sum(128>>i for i in range(8) if pix[cx*8+i,y]!=BL)
scr=bytes(bitmap+attr)
(R/'assets/FASE_V24.scr').write_bytes(scr)
def pack(blob):
    out=bytearray();i=0
    while i<len(blob):
        n=1
        while i+n<len(blob) and blob[i+n]==blob[i] and n<255:n+=1
        if n>=4 or blob[i]==255:out.extend((255,n,blob[i]));i+=n
        else:out.append(blob[i]);i+=1
    return bytes(out)
rle=pack(scr)
(R/'build/phase_rle_v24.bin').write_bytes(rle)
with (R/'build/phase_rle_v24.asm').open('w') as f:
    f.write('; Screen RAM asset created from the 6912-byte native Spectrum SCR.\nphase_rle_data:\n')
    for i in range(0,len(rle),28):f.write(' db '+','.join(str(x) for x in rle[i:i+28])+'\n')
# Visual preview of EXACT screen bytes, with the dynamic number 02 patched
# to y126 with original 7-bit type from the same digit routine as the game.
from PIL import Image
out=Image.new('RGB',(256,192),BL);dst=out.load()
palette=[(0,0,0),(0,0,220),(240,0,0),(240,0,200),(0,235,0),(0,235,245),(250,238,20),(245,245,245)]
for y in range(192):
    for x in range(256):
        off=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+(x>>3)
        bit=(bitmap[off]>>(7-(x&7)))&1
        a=attr[(y>>3)*32+(x>>3)]
        dst[x,y]=palette[(a&7) if bit else (a>>3)&7]
for cx,ch in [(15,'0'),(16,'2')]:
    for yy,row in enumerate(glyphs[ch]):
        for xx,z in enumerate(row):
            if z=='1':dst[cx*8+xx+1,126+yy]=palette[5]
preview=R/'build/V24_FASE_02_PREVIEW.png'
out.resize((768,576),Image.Resampling.NEAREST).save(preview)
print('FASE SCR=',len(scr),'Z80-RLE=',len(rle),'bytes; rendered',preview)
