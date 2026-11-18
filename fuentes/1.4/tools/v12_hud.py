"""HUD 1.2: parte fija (va comprimida) + tablas para las partes que cambian."""
from tools.v12_zx import ZX,A,BLK,BLU,RED,MAG,GRN,CYN,YEL,WHT
from tools.v12_font import S5,BIG,T3,sctext,stext,ctext
FACE={
'feliz':["....######....","..##########..",".############.",".###..##..###.","####..##..####","##############","##############","##.########.##","###.######.###",".###......###.",".############.","..##########..","....######....","..............",],
'apurado':["....######....","..##########..",".##.######.##.",".###.####.###.","####..##..####","####..##..####","##############","##############","####......####","###.######.###",".############.","..##########..","....######....","..............",],
'vacia':["....#.##.#....","..#........#..","..............",".#..........#.","..............","#............#","..............","#............#","..............",".#..........#.","..............","..#........#..","....#.##.#....","..............",],
}
MOAI_ICON=["..###.","######",".#.#..","######",".####.",".####.","######"]
def band(z,r,ink,label,x=None):
    y0=r*8
    for y in range(y0,y0+8):
        for xx in range(192,256):z.px[y][xx]=0
    z.attr(24,r,32,r+1,A(BLK,ink))
    for x_,y in ((192,y0),(193,y0),(192,y0+1),(255,y0),(254,y0),(255,y0+1),(192,y0+7),(255,y0+7)):z.px[y][x_]=1
    if x is None:sctext(z,224,y0+2,label)
    else:stext(z,x,y0+2,label)
def rails(z,r0,r1,ink):
    z.vline(193,r0*8,r1*8);z.vline(254,r0*8,r1*8)
    z.attr(24,r0,25,r1,A(ink));z.attr(31,r0,32,r1,A(ink))
def static_hud(logo_rows):
    """Lienzo con solo lo fijo. logo_rows = 64 filas x 64 px del logo ESF original."""
    z=ZX();z.attr(0,0,32,24,A(WHT))
    band(z,0,YEL,'PUNTOS');rails(z,1,4,YEL);z.attr(25,1,31,3,A(WHT))
    stext(z,201,26,'REC');z.attr(25,3,31,4,A(CYN,0,0))
    band(z,4,CYN,'VIDAS');rails(z,5,8,CYN)
    for i in range(3):z.attr(25+i*2,5,27+i*2,8,A(YEL))
    band(z,8,GRN,'ESCUDO');rails(z,9,11,GRN)
    for k in range(8):                      # bordes superior e inferior de los 8 segmentos
        x=200+k*6
        for dx in range(5):z.plot(x+dx,73);z.plot(x+dx,78)
    z.attr(25,9,31,10,A(GRN));z.attr(25,10,31,11,A(GRN))
    band(z,11,MAG,'FASE',x=205);rails(z,12,14,MAG)
    z.blit(234,98,MOAI_ICON)
    stext(z,201,107,'OLEADA')
    z.attr(25,12,31,13,A(MAG));z.attr(25,13,31,14,A(MAG,0,0))
    for j,row in enumerate(logo_rows):
        for i,v in enumerate(row):
            if v:z.px[120+j][192+i]=1
    z.attr(24,14,32,24,A(WHT));z.attr(24,14,25,24,A(RED));z.attr(31,14,32,24,A(RED))
    z.attr(24,14,32,15,A(RED));z.attr(24,23,32,24,A(RED))
    z.hline(196,252,113);z.hline(196,252,190);z.vline(193,116,188);z.vline(254,116,188)
    for p in ((194,114),(195,114),(194,115),(253,114),(252,114),(253,115),(194,189),(195,189),(194,188),(253,189),(252,189),(253,188)):z.plot(*p)
    return z
def hud_blob(z):
    """1536 bytes de bitmap (8 por linea, x192..255) + 192 de atributos (8 por fila)."""
    out=bytearray()
    for y in range(192):
        for c in range(8):
            v=0
            for b in range(8):
                if z.px[y][192+c*8+b]:v|=128>>b
            out.append(v)
    for r in range(24):out+=bytes(z.at[r][24:32])
    return bytes(out)
def glyph_bytes(rows,width_bits,shift):
    """Filas de '#' a bytes, empezando en el bit 'shift' (0 = bit 7)."""
    out=[]
    for r in rows:
        v=0
        for i,ch in enumerate(r):
            if ch=='#':
                bit=shift+i
                v|=1<<(width_bits-1-bit)
        out.append(v)
    return out
def tables():
    t=[]
    big=[];[big.extend(glyph_bytes(BIG[str(d)],8,0)) for d in range(10)]
    t.append(('hud_big_digits',big))                       # 7x8, bits 7..1
    nib=[];[nib.extend(glyph_bytes(T3[str(d)],4,0)) for d in range(10)]
    t.append(('hud_nibble_digits',nib))                    # 3x5 en un nibble (bits 3..1)
    s5=[];[s5.extend(glyph_bytes(S5[str(d)],8,1)) for d in range(10)]
    t.append(('hud_s5_digits',s5))                         # 5x5, bits 6..2
    for k in ('feliz','apurado','vacia'):
        fb=[]
        for r in FACE[k][:13]:
            v=0
            for i,ch in enumerate(r):
                if ch=='#':v|=1<<(15-(i+1))
            fb+= [v>>8,v&255]
        t.append(('hud_face_'+k,fb))                       # 13 filas x 2 bytes
    # fila central de la barra del escudo para 0..8 segmentos (6 bytes)
    bars=[]
    for m in range(9):
        bits=[0]*48
        for k in range(8):
            for dx in range(5):
                if k<m or dx in (0,4):bits[k*6+dx]=1
        for c in range(6):bars.append(sum(bits[c*8+b]<<(7-b) for b in range(8)))
    t.append(('hud_shield_rows',bars))
    # textos de estado del escudo (6 bytes x 5 filas, centrados en x200..247)
    for name,txt in (('listo','LISTO'),('activo','ACTIVO'),('carga','CARGANDO')):
        z=ZX();sctext(z,224,0,txt)
        tb=[]
        for y in range(5):
            for c in range(6):tb.append(sum(z.px[y][200+c*8+b]<<(7-b) for b in range(8)))
        t.append(('hud_txt_'+name,tb))
    return t
