"""Sprites 1.2: enemigos nuevos (mismo sitio y tamano), cuervo 8x8 nuevo,
explosion 16x16 en 3 tiempos (se desplaza al arrancar en $5B00), rombo de
disparo enemigo y llama de motores. Parchea build/sprites_reloc_v22.bin."""
from pathlib import Path
from tools.v12_spr_art import CUERVO,CAZADOR,HALCON,EXPLO
R=Path(__file__).resolve().parents[1]
B=R/'build'
def shifted(frames,w,h):
    bpr=w//8+1;out=bytearray()
    for fr in frames:
        for ph in range(8):
            for y in range(h):
                for bx in range(bpr):
                    v=0
                    for px in range(8):
                        sx=bx*8+px-ph
                        if 0<=sx<w and fr[y][sx]=='#':v|=128>>px
                    out.append(v)
    return bytes(out)
CROW8=[[
"#......#",
"##....##",
".##..##.",
"..####..",
".#.##.#.",
"..####..",
"...##...",
"...##..."],[
"........",
"...##...",
"..####..",
"########",
"#.#..#.#",
"..####..",
".#.##.#.",
"...##..."]]
PLASMA=[".#......","###.....","###.....",".#......"]
FLAME=[[".##..##.",".##..##.","..#..#..","........"],
       [".##..##.","..#..#..","........","........"]]
def build(title_scr):
    blob=bytearray((B/'sprites_reloc_v22.bin').read_bytes())
    def put(off,data):
        assert len(blob)>=off+len(data);blob[off:off+len(data)]=data
    put(0x300,shifted(CAZADOR,16,16))   # tipo 0 (amarillo)
    put(0x600,shifted(CUERVO,16,16))    # tipo 1 (rojo)
    put(0x900,shifted(HALCON,16,16))    # tipo 2 (cian)
    put(0xcc0,shifted(CROW8,8,8))       # cuervos de la primera oleada (8x8)
    put(0xc00,shifted(FLAME,8,4))       # llama (128 bytes, sitio de la explosion vieja)
    assert len(blob)==0x1e20
    del blob[0x1d40:]          # la copia de atributos del logo ya no hace falta (mascara en $F070)
    # V1.2: la explosion del ESF (3 tiempos x 8 fases x 96 bytes) se queda con las
    # fases pares (desplazamiento de 2 en 2 px: no se nota en una explosion).
    # Se liberan 1.152 bytes de memoria baja para el codigo nuevo.
    BL,SH,FR=0x0dc0,0x16c0,0x1bc0
    blast=bytearray()
    for f in range(3):
        for ph in (0,2,4,6):blast+=blob[BL+f*768+ph*96:BL+f*768+ph*96+96]
    # El escudo (32x32, 5 bytes x 32 lineas) tambien se queda con las fases pares:
    # (en la V1.3 ese hueco fue para los fondos de fase; desde la 1.3.3 queda libre).
    shield=b''.join(bytes(blob[SH+ph*160:SH+ph*160+160]) for ph in (0,2,4,6))
    frame=bytes(blob[FR:FR+384])
    del blob[BL:]
    blast_at=len(blob);blob+=blast
    shield_at=len(blob);blob+=shield
    frame_at=len(blob);blob+=frame
    extra=bytearray()
    shot_off=len(blob);extra+=shifted([PLASMA],8,4)
    exp_off=len(blob)+len(extra)
    for fr in EXPLO:
        for row in fr:
            v=int(''.join('1' if c=='#' else '0' for c in row),2);extra+=bytes([v>>8,v&255])
    blob+=extra
    (B/'sprites_reloc_v22.bin').write_bytes(blob)
    lo=0x6000
    asm=['; V1.2 punteros de sprites nuevos (generado por tools/v12_sprites.py)']
    asm.append(f'frame_bitmap_low equ {lo+frame_at}')
    # punteros de la explosion del ESF y del escudo, recolocados
    ca=(B/'combat_assets_v22.asm').read_text()
    cut=ca.index('ship_blast_phase_ptrs_f0:')
    tail=['']
    for f in range(3):
        tail.append(f'ship_blast_phase_ptrs_f{f}:')
        tail+=[f' dw {lo+blast_at+f*384+(p//2)*96}' for p in range(8)]
    tail.append('shield_phase_ptrs:')
    tail+=[f' dw {lo+shield_at+(p//2)*160}' for p in range(8)]
    (B/'combat_assets_v22.asm').write_text(ca[:cut]+'\n'.join(tail)+'\n')
    asm.append('enemy_shot_phase_ptrs:');asm+=[f' dw {lo+shot_off+p*8}' for p in range(8)]
    for f in range(2):
        asm.append(f'flame_phase_ptrs_f{f}:');asm+=[f' dw {lo+0xc00+f*64+p*8}' for p in range(8)]
    asm.append(f'explosion_src equ {lo+exp_off}')
    for f in range(3):
        asm.append(f'explosion_phase_ptrs_f{f}:');asm+=[f' dw {0x5b00+(f*8+p)*48}' for p in range(8)]
    return asm
