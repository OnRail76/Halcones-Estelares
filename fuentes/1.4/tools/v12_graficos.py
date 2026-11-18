"""HALCONES ESTELARES 1.2 - generador de datos graficos y de sonido.
Se ejecuta desde build.py despues de los generadores historicos. Produce:
  build/v12_data.asm      datos del bloque principal (pantallas LZ, HUD LZ, fuentes...)
  build/gameover_lz.bin   pantalla de GAME OVER comprimida (bloque de extras)
  build/assets_v12.asm    assets.asm sin el HUD antiguo sin comprimir
"""
from pathlib import Path
import re
from tools.lz import compress,decompress
R=Path(__file__).resolve().parents[1]
B=R/'build'
def rle_decode(b):
    out=bytearray();i=0
    while len(out)<6912:
        if b[i]==255:out+=bytes([b[i+2]])*b[i+1];i+=3
        else:out.append(b[i]);i+=1
    return bytes(out[:6912])
def db_lines(label,data):
    rows=[f'{label}:']
    for i in range(0,len(data),24):rows.append(' db '+','.join(map(str,data[i:i+24])))
    return rows
def asm_bytes(text,label):
    """Bytes de un bloque 'label:' seguido de lineas db en un .asm generado."""
    out=bytearray();on=False
    for line in text.splitlines():
        t=line.split(';',1)[0].strip()
        if not t:continue
        if t.endswith(':'):
            if on:break
            on=(t[:-1]==label);continue
        if on and t.startswith('db '):out+=bytes(int(x) for x in t[3:].split(','))
    return bytes(out)
assets=(B/'assets.asm').read_text()
hud=asm_bytes(assets,'hud_bitmap_data')+asm_bytes(assets,'hud_attr_data')
assert len(hud)==1728
cut=assets.index('hud_bitmap_data:')
(B/'assets_v12.asm').write_text(assets[:cut])
SCREENS={
 'title':None,
 'phase':rle_decode((B/'phase_rle_v24.bin').read_bytes()),
 'gameover':rle_decode((B/'gameover_rle_v20.bin').read_bytes()),
}
HUD=hud
from tools.v12_title import title as _title
_tz,TITLE_STARS=_title()
SCREENS['title']=_tz.to_scr()
from tools import v12_screens as _scr
SCREENS['phase']=_scr.phase(SCREENS['phase'])
SCREENS['gameover']=_scr.gameover(SCREENS['gameover'])
(B/'FASE_V12.scr').write_bytes(SCREENS['phase']);(B/'GAMEOVER_V12.scr').write_bytes(SCREENS['gameover'])
(B/'TITULO_V12.scr').write_bytes(SCREENS['title'])
# --- V1.2: HUD nuevo (la parte fija sale de tools/v12_hud.py, el logo ESF es el original) ---
from tools.v12_hud import static_hud,hud_blob,tables as hud_tables
_logo=[[1 if hud[y*8+c]&(128>>b) else 0 for c in range(8) for b in range(8)] for y in range(120,184)]
HUD_Z=static_hud(_logo)
HUD=hud_blob(HUD_Z)
def build():
    out=['; HALCONES ESTELARES 1.2 - datos generados por tools/v12_graficos.py']
    t=compress(SCREENS['title']);out+=db_lines('title_lz',t)
    p=compress(SCREENS['phase']);out+=db_lines('phase_lz',p)
    h=compress(HUD);out+=db_lines('hud_lz',h)
    for name,data in hud_tables():out+=db_lines(name,data)
    from tools.v12_sprites import build as sprites_build
    out+=sprites_build(SCREENS['title'])
    out.append('title_star_cells:')
    for c,r in TITLE_STARS:out.append(f' dw {0x5800+r*32+c}')
    out.append(f'title_star_count equ {len(TITLE_STARS)}')
    g=compress(SCREENS['gameover']);(B/'gameover_lz.bin').write_bytes(g)
    for d,c in ((SCREENS['title'],t),(SCREENS['phase'],p),(HUD,h),(SCREENS['gameover'],g)):assert decompress(c)==d
    (B/'v12_data.asm').write_text('\n'.join(out)+'\n')
    print(f'V12 LZ: titulo {len(t)}, fase {len(p)}, HUD {len(h)}, game over {len(g)} bytes')
build()
