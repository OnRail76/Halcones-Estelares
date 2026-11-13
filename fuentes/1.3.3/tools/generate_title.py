#!/usr/bin/env python3
"""Rebuild the original V2.7 yellow title with the complete approved IMPERIAL cyborg bird.
Pixel-accurate native ZX Spectrum .SCR, with 16x8-pixel bill integrated below the eyes.
This generator never changes any title letterforms or any other on-screen text.
"""
from pathlib import Path
from PIL import Image
import hashlib, json
R=Path(__file__).resolve().parents[1]
GLYPHS={
 'A':['01110','10001','10001','11111','10001','10001','10001'],
 'B':['11110','10001','10001','11110','10001','10001','11110'],
 'C':['01111','10000','10000','10000','10000','10000','01111'],
 'D':['11110','10001','10001','10001','10001','10001','11110'],
 'E':['11111','10000','10000','11110','10000','10000','11111'],
 'F':['11111','10000','10000','11110','10000','10000','10000'],
 'G':['01111','10000','10000','10111','10001','10001','01111'],
 'H':['10001','10001','10001','11111','10001','10001','10001'],
 'I':['11111','00100','00100','00100','00100','00100','11111'],
 'J':['00111','00010','00010','00010','10010','10010','01100'],
 'K':['10001','10010','10100','11000','10100','10010','10001'],
 'L':['10000','10000','10000','10000','10000','10000','11111'],
 'M':['10001','11011','10101','10101','10001','10001','10001'],
 'N':['10001','11001','10101','10011','10001','10001','10001'],
 'O':['01110','10001','10001','10001','10001','10001','01110'],
 'P':['11110','10001','10001','11110','10000','10000','10000'],
 'Q':['01110','10001','10001','10001','10101','10010','01101'],
 'R':['11110','10001','10001','11110','10100','10010','10001'],
 'S':['01111','10000','10000','01110','00001','00001','11110'],
 'T':['11111','00100','00100','00100','00100','00100','00100'],
 'U':['10001','10001','10001','10001','10001','10001','01110'],
 'V':['10001','10001','10001','10001','10001','01010','00100'],
 'W':['10001','10001','10001','10101','10101','10101','01010'],
 'X':['10001','10001','01010','00100','01010','10001','10001'],
 'Y':['10001','10001','01010','00100','00100','00100','00100'],
 'Z':['11111','00001','00010','00100','01000','10000','11111'],
 '0':['01110','10011','10101','10101','11001','10001','01110'],
 '1':['00100','01100','00100','00100','00100','00100','01110'],
 '2':['01110','10001','00001','00010','00100','01000','11111'],
 '3':['11110','00001','00001','01110','00001','00001','11110'],
 '4':['00010','00110','01010','10010','11111','00010','00010'],
 '5':['11111','10000','10000','11110','00001','00001','11110'],
 '6':['01110','10000','10000','11110','10001','10001','01110'],
 '7':['11111','00001','00010','00100','01000','01000','01000'],
 '8':['01110','10001','10001','01110','10001','10001','01110'],
 '9':['01110','10001','10001','01111','00001','00001','01110'],
 '/':['00001','00001','00010','00100','01000','10000','10000'],
 '.':['00000','00000','00000','00000','00000','00100','00100'],
 ':':['00000','00100','00100','00000','00100','00100','00000'],
 '+':['00000','00100','00100','11111','00100','00100','00000'],
 ' ':['00000']*7,
}
# V2.8.1: original V2.7 yellow letterforms + approved full cyborg hawk #1.
# The two changed attribute cells produce a yellow beak on cyan PAPER,
# at the LOW part of the head, not a detached yellow mark in the neck.
source=R/'assets/TITULO_01_IMPERIAL_SIN_PICO.scr'
scr=bytearray(source.read_bytes())
assert len(scr)==6912
assert hashlib.sha256(scr).hexdigest()=='7fd761bdfb1021252746f3108ee5367d8916e68173fe73563fc837b4d368e738', 'Original bird reference was modified'
# Restore the ENTIRE title band including its original ZX ATTRIBUTES, not only
# the letter pixels. 80 top scanlines (10 character rows) from V2.7 exactly.
v27_source=R/'assets/TITULO_V27_ORIGINAL_INTACTO.scr'
v27=bytearray(v27_source.read_bytes())
assert len(v27)==6912
assert hashlib.sha256(v27).hexdigest()=='be0f19c35caa3ef0e6ad6466cc9dadd31d681cbdfa509b607888e4db06bfadbe'
for yy in range(80):
    off=((yy&0xc0)<<5)+((yy&7)<<8)+((yy&0x38)<<2)
    scr[off:off+32]=v27[off:off+32]
scr[6144:6144+10*32]=v27[6144:6144+10*32]
def _pix_addr(x,y):
    return ((y & 0xc0)<<5)+((y & 7)<<8)+((y & 0x38)<<2)+(x//8)
# ZX Spectrum color: BRIGHT YELLOW INK (6) on BRIGHT CYAN PAPER (5).
# Only two 8x8 cells in the center of the face are changed.
for cx in (120,128):
    scr[6144+(104//8)*32+cx//8]=0x6e
    for yy in range(104,112):
        scr[_pix_addr(cx,yy)]=0
# Anatomically placed, 8-pixel tapered hawk bill just below the eyes.
beak={104:(125,130),105:(124,131),106:(124,131),107:(125,130),
      108:(125,130),109:(126,129),110:(126,129),111:(127,128)}
for yy,(left,right) in beak.items():
    for xx in range(left,right+1):
        addr=_pix_addr(xx,yy)
        scr[addr]|=128>>(xx&7)
scr=bytes(scr)
assert scr[6144:6144+10*32]==v27[6144:6144+10*32]
# This is a full native 6912-byte .SCR, NOT a pre-rendered mockup.
(R/'assets/HALCONES_ESTELARES_TITLE.scr').write_bytes(scr)
(R/'assets/TITULO_V281_LOGO_ORIGINAL_HALCON_COMPLETO.scr').write_bytes(scr)

def pack(data):
    out=bytearray(); i=0
    while i<len(data):
        n=1
        while i+n<len(data) and data[i+n]==data[i] and n<255:n+=1
        if n>=4 or data[i]==255:
            out.extend((255,n,data[i])); i+=n
        else:
            out.append(data[i]); i+=1
    return bytes(out)

encoded=pack(scr)
probe=bytearray(); i=0
while i<len(encoded):
    b=encoded[i];i+=1
    if b==255:
        n,v=encoded[i],encoded[i+1];i+=2;probe.extend([v]*n)
    else:probe.append(b)
assert bytes(probe)==scr
lines=['; Original V2.7 LOGO + full approved IMPERIAL bird; only 2 face cells modified.',
       '; Source: assets/TITULO_01_IMPERIAL_SIN_PICO.scr; beak fixed in native attributes. Existing title unpacker unchanged.',
       'title_rle_data:']
for i in range(0,len(encoded),25):
    lines.append(' db '+','.join(str(v) for v in encoded[i:i+25]))
(R/'build/title_data.asm').write_text('\n'.join(lines)+'\n')
normal=[(0,0,0),(0,0,200),(200,0,0),(200,0,200),(0,160,0),(0,160,160),(200,200,0),(190,190,190)]
bright=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
img=Image.new('RGB',(256,192)); pix=img.load()
for y in range(192):
    for x in range(256):
        addr=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+(x>>3)
        v=(scr[addr]>>(7-(x&7)))&1
        att=scr[6144+(y>>3)*32+(x>>3)]
        pal=bright if att&64 else normal
        pix[x,y]=pal[(att&7) if v else ((att>>3)&7)]
img.save(R/'build/HALCONES_TITULO_NATIVO.png')
img.resize((768,576),Image.Resampling.NEAREST).save(R/'build/HALCONES_TITULO_AMPLIADO.png')
(R/'build/title_manifest.json').write_text(json.dumps({
    'source':'assets/TITULO_V281_LOGO_ORIGINAL_HALCON_COMPLETO.scr',
    'title':'HALCONES ESTELARES — V2.7 ORIGINAL, no extra ornaments',
    'subtitle':'EUROPEAN SPACE FORCE',
    'credit':'© 2026 TONY C. WARE',
    'controls':'O IZQ P DER / A ESCUDO SPACE FUEGO / PULSA SPACE',
    'bitmap_sha256':hashlib.sha256(scr).hexdigest(),
    'rle_size':len(encoded),
    'bitmap_original_logo_unmodified':True},indent=2,ensure_ascii=False))
print('TITLE: V2.7 original logo and completed hawk, native SCR',len(encoded),'bytes RLE')
