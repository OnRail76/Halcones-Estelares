"""Titulo 1.2: el original con letras en degradado, halcon nuevo, cielo
estrellado que titila y la parte baja con record y controles nuevos."""
import random
from pathlib import Path
from tools.v12_zx import ZX,A,BLK,BLU,RED,MAG,GRN,CYN,YEL,WHT
from tools.v12_font import ctext,text,width
from tools import v12_hawk
R=Path(__file__).resolve().parents[1]
def title():
    z=ZX.from_scr(str(R/'assets/HALCONES_ESTELARES_TITLE.scr'))
    grad={1:A(YEL),2:A(YEL),3:A(YEL),4:A(RED),5:A(YEL),6:A(YEL),7:A(RED)}
    for r,a in grad.items():
        for c in range(32):
            if z.at[r][c]&7==YEL:z.at[r][c]=a
    credit=[row[:] for row in z.px[148:155]]
    v12_hawk.draw(z)                          # borra 84..143 y dibuja el halcon
    z.clear(0,144,256,192)
    for j,row in enumerate(credit):z.px[145+j]=row
    z.attr(0,18,32,19,A(WHT))
    # RECORD: la etiqueta es fija; las 6 cifras se escriben en columnas 16..21
    text(z,84,153,'RECORD');z.attr(0,19,32,20,A(YEL))
    ctext(z,128,161,'O-P/6-7 MOVER   A/8 ESCUDO');z.attr(0,20,32,21,A(CYN))
    ctext(z,128,169,'SPACE/0 FUEGO   H PAUSA');z.attr(0,21,32,22,A(GRN))
    ctext(z,128,177,'KEMPSTON: PULSA SU FUEGO');z.attr(0,22,32,23,A(WHT,0,0))
    ctext(z,128,185,'PULSA FUEGO');z.attr(0,23,32,24,A(YEL,0,1,1))
    # cielo: estrellas en celdas vacias (filas 0..10); su atributo titila
    rnd=random.Random(3);stars=[]
    def empty(c,r):return not any(z.px[r*8+j][c*8+i] for j in range(8) for i in range(8))
    tries=0
    while len(stars)<36 and tries<2000:
        tries+=1
        c,r=rnd.randrange(32),rnd.randrange(0,11)
        if (c,r) in stars or not empty(c,r):continue
        z.plot(c*8+rnd.randrange(1,7),r*8+rnd.randrange(1,7))
        z.at[r][c]=rnd.choice([A(WHT),A(WHT,0,0),A(CYN,0,0),A(BLU)])
        stars.append((c,r))
    return z,stars
