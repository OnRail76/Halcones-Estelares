"""Pantallas de fase superada y GAME OVER 1.2: textos nuevos y estrellas.
Las cifras (puntos, vidas, record) las escribe el juego en columnas fijas."""
import random
from tools.v12_zx import ZX,A,BLK,BLU,RED,MAG,GRN,CYN,YEL,WHT
from tools.v12_font import ctext,text
def _from(scr):
    z=ZX()
    for y in range(192):
        for xb in range(32):
            byte=scr[((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2)|xb]
            for b in range(8):z.px[y][xb*8+b]=1 if byte&(128>>b) else 0
    for r in range(24):
        for c in range(32):z.at[r][c]=scr[6144+r*32+c]
    return z
def stars(z,seed,rows,n=50):
    rnd=random.Random(seed)
    def empty(c,r):return not any(z.px[r*8+j][c*8+i] for j in range(8) for i in range(8))
    for k in range(n):
        c,r=rnd.randrange(32),rnd.choice(rows)
        if empty(c,r):
            z.plot(c*8+rnd.randrange(1,7),r*8+rnd.randrange(1,7))
            z.at[r][c]=rnd.choice([A(WHT),A(WHT,0,0),A(CYN,0,0),A(BLU)])
def phase(scr):
    z=_from(scr)
    ctext(z,128,17,'¡MOAI DERROTADO!');z.attr(0,2,32,3,A(RED,0,1,1))
    text(z,86,136,'PUNTOS');z.attr(0,17,32,18,A(YEL))       # cifras en columnas 16..21
    text(z,26,144,'VIDAS');text(z,92,144,'RECORD')            # vidas en col 8, record 17..22
    z.attr(0,18,32,19,A(WHT,0,0))
    stars(z,5,[0,1,3,6,11,12,23])
    return z.to_scr()
def gameover(scr):
    z=_from(scr)
    ctext(z,128,137,'¡NUEVO RECORD!');z.attr(0,17,32,18,A(BLK,0,0))   # oculto hasta que haya record
    text(z,84,161,'RECORD');z.attr(0,20,32,21,A(CYN))                 # cifras en columnas 16..21
    stars(z,9,[8,9,13,22])
    return z.to_scr()
