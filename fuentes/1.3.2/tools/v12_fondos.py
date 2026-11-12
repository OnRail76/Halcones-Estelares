"""HALCONES ESTELARES 1.2 - fondos lejanos de cada fase.
Cada fondo es un mapa de densidad de bloques de 4x4 px con 4 niveles (2 bits):
0 vacio, 1 muy tenue, 2 tenue, 3 medio. El juego lo expande con tramas fijas
en el cielo inmovil ($D800), en tinta blanca como las estrellas, asi que no
toca los atributos de color. 80x64 px por fondo = 80 bytes de datos."""
import math,random
PAT=[[0,0,0,0],[8,0,2,0],[10,0,5,0],[10,5,10,5]]   # nibbles por nivel y fila
W,H=20,16                                           # bloques (80x64 px)
def _q(v):return 0 if v<0.18 else 1 if v<0.45 else 2 if v<0.85 else 3
def nebulosa():
    r=random.Random(11);pts=[(r.uniform(4,16),r.uniform(3,13),r.uniform(2,5)) for _ in range(9)]
    m=[]
    for y in range(H):
        row=[]
        for x in range(W):
            v=sum(math.exp(-((x-a)**2+(y-b)**2)/(2*c*c)) for a,b,c in pts)*0.32
            v*=0.75+0.5*math.sin(x*1.3+y*0.7)*math.cos(y*1.1-x*0.4)   # filamentos
            row.append(_q(v))
        m.append(row)
    return m
def galaxia():
    m=[]
    for y in range(H):
        row=[]
        for x in range(W):
            dx=(x-9.5);dy=(y-7.5)*2.0                 # disco inclinado
            rr=math.hypot(dx,dy)+1e-6;th=math.atan2(dy,dx)
            arm=max(math.cos(2*th-1.1*math.log(rr+1)*2.2),0)**4
            v=math.exp(-rr/2.2)*1.3+arm*math.exp(-rr/7.0)*0.75
            row.append(_q(v))
        m.append(row)
    return m
def planeta():
    m=[]
    for y in range(H):
        row=[]
        for x in range(W):
            dx=(x-10)/5.2;dy=(y-8)/5.2;rr=dx*dx+dy*dy;v=0
            if rr<1:
                nz=math.sqrt(1-rr);sh=-0.6*dx-0.5*dy+0.6*nz
                v=0.25+0.55*max(sh,0)
            ring=abs(math.hypot((x-10)/9.0,(y-8)/2.4)-1)
            if ring<0.12 and not (rr<1 and dy<0):v=max(v,0.75)
            row.append(_q(v))
        m.append(row)
    return m
def cumulo():
    """Cumulo globular: nucleo denso que se deshace en estrellas sueltas."""
    r=random.Random(7);m=[[0]*W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            rr=math.hypot(x-10,(y-8)*1.2);v=math.exp(-rr/2.6)*1.1
            m[y][x]=_q(v)
    for k in range(26):
        a=r.uniform(0,6.28);d=r.uniform(3,8.5);x=int(10+d*math.cos(a));y=int(8+d*math.sin(a)/1.2)
        if 0<=x<W and 0<=y<H:m[y][x]=max(m[y][x],1)
    return m
# (x en bytes, y en pixeles)
# V1.2: todos en la franja y=88..151, por debajo de las formaciones (los cuervos
# bajan hasta y=91): asi casi nunca comparten celda de color con un enemigo.
FONDOS=[(nebulosa(),13,88),(galaxia(),3,88),(planeta(),13,88),(cumulo(),4,88)]
def asm():
    out=['; V1.2 fondos de fase (generado por tools/v12_fondos.py)','bg_patterns:']
    out.append(' db '+','.join(str(n) for lv in PAT for n in lv))
    for i,(m,xc,y) in enumerate(FONDOS):
        out.append(f'bg_{i}:')
        out.append(f' db {xc},{y}')
        data=[]
        for row in m:
            for k in range(0,W,4):
                b=0
                for j in range(4):b=(b<<2)|row[k+j]
                data.append(b)
        out.append(' db '+','.join(map(str,data)))
    out.append('bg_table: dw '+','.join(f'bg_{i}' for i in range(len(FONDOS))))
    return out
def preview(path):
    from PIL import Image
    im=Image.new('RGB',(4*(W*4+8),H*4),(0,0,0))
    for i,(m,xc,y) in enumerate(FONDOS):
        for by in range(H):
            for bx in range(W):
                lv=m[by][bx]
                for k in range(4):
                    nib=PAT[lv][k]
                    for b in range(4):
                        if nib&(8>>b):im.putpixel((i*(W*4+8)+bx*4+b,by*4+k),(230,230,230))
    im.resize((im.width*3,im.height*3),0).save(path)
if __name__=='__main__':preview('/tmp/fondos.png')
