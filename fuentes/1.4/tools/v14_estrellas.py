#!/usr/bin/env python3
"""V1.4: constelacion fija del cielo inmovil (D800). Genera src/v14_estrellas.asm.
Las estrellas se pintan una vez en el cielo; el compositor las repone solo
cuando pasa algo por encima. Nunca donde estan el MOAI, Jupiter, el recorrido
de la luna ni la fila del cartel de OLEADA (se borran o se pintan alli)."""
import random
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def libre(x,y):
    if not(22<=x<=186 and 4<=y<=186):return False
    if 64<=x<=127 and y<=101:return False          # MOAI y sus grietas
    if 122<=x<=189 and 90<=y<=157:return False     # Jupiter
    if 106<=y<=126:return False                    # recorrido de la luna
    if 82<=y<=101:return False                     # cartel de OLEADA
    return True
def estrellas(n_pix=34,n_cruz=8,seed=1986):
    rnd=random.Random(seed);pts=[];centros=[]
    def lejos(x,y,d):return all(abs(x-a)+abs(y-b)>=d for a,b in centros)
    while len(centros)<n_pix+n_cruz:
        x,y=rnd.randrange(22,187),rnd.randrange(4,187)
        cruz=len(centros)>=n_pix
        forma=[(0,0)]+([(1,0),(-1,0),(0,1),(0,-1)] if cruz else [])
        if all(libre(x+a,y+b) for a,b in forma) and lejos(x,y,16):
            centros.append((x,y));pts+=[(x+a,y+b) for a,b in forma]
    return pts
def addr(x,y):return 0xd800+(((y&0xc0)<<5)|((y&7)<<8)|((y&0x38)<<2))+(x>>3)
def asm():
    p=estrellas()
    out=['; Generado por tools/v14_estrellas.py: no editar a mano.',
         '; V1.4: estrellas fijas. Se pintan (OR) en el cielo inmovil D800.',
         'sky_stars_draw:',' ld hl,sky_stars',' ld b,%d'%len(p),'sky_stars_loop:',
         ' ld e,(hl)',' inc hl',' ld d,(hl)',' inc hl',' ld a,(de)',' or (hl)',' ld (de),a',' inc hl',' djnz sky_stars_loop',' ret',
         'sky_stars:']
    for x,y in p:
        a=addr(x,y);out.append(' db %d,%d,%d'%(a&255,a>>8,0x80>>(x&7)))
    return out,p
if __name__=='__main__':
    lines,p=asm()
    (R/'src/v14_estrellas.asm').write_text('\n'.join(lines)+'\n')
    print(len(p),'pixeles')
