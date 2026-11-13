#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
from tools.build_ship_assets import R as _sprite_root
from tools.build_combat_assets import R as _combat_root
from tools.generate_assets import R
from tools.generate_assets import __name__ as _unused  # generates assets when imported
from tools.generate_title import GLYPHS as _title_font
from tools.generate_moai_v19 import R as _boss_root
from tools.generate_jupiter_v20 import R as _jupiter_root
from tools.generate_gameover_v20 import R as _gameover_root
from tools.generate_phase_v24 import R as _phase_root
from tools.generate_frame_v17 import R as _frame_root  # produces native title SCR and packed ASM
from tools.z80_assembler import A
from tools.tap_writer import create_tap
from tools import relocate_sprite_assets_v22
from tools import v12_graficos  # V1.2: datos nuevos (LZ, HUD, sprites, sonido)
source='\n'.join((R/p).read_text() for p in ['src/main.asm','src/irq_im2_v15.asm','src/title_screen.asm','src/gameover_v20.asm','src/phase_interlude_v24.asm','src/gameplay.asm','src/arcade_rules_v18.asm','src/boss_moai_v19.asm','src/sound_v19.asm','src/arcade_compositor.asm','src/stars_scroll_v13.asm','src/arcade_fast.asm','src/v11_controles.asm','src/v12_hud.asm','src/v12_sound.asm','build/assets_v12.asm','build/combat_assets_v22.asm','build/v12_data.asm','build/frame_data_v17.asm'])
# V1.1: rutinas frias en memoria baja, a continuacion de los sprites reubicados.
# Dos ensamblados enlazados por direcciones absolutas (solo JP/CALL entre ellos).
import re as _re
low_src=(R/'src/v11_bajo.asm').read_text()+'\n'+(R/'src/v12_bajo.asm').read_text()
low_bin_sprites=(R/'build/sprites_reloc_v22.bin').read_bytes()
LOW_ORG=0x6000+len(low_bin_sprites)
low_names=[m[1] for m in _re.finditer(r'^([a-z_0-9]+):',low_src,_re.M)]
def _equs(d,skip=()):return '\n'.join(f'{k} equ {v}' for k,v in d.items() if k not in skip)+'\n'
# V1.2: bloque de extras ($F401): MOAI + Jupiter + GAME OVER LZ + datos de sonido.
_ex_bin=(R/'build/moai_bitmap_v19.bin').read_bytes()+(R/'build/jupiter_bitmap_v20.bin').read_bytes()+(R/'build/gameover_lz.bin').read_bytes()
assert len(_ex_bin)>=920
_ex_src=' org 0xf401\n'+'\n'.join(' db '+','.join(map(str,_ex_bin[i:i+32])) for i in range(0,len(_ex_bin),32))+'\n'+(R/'src/v12_extras.asm').read_text()
_ex=A(_ex_src);extras_code=_ex.run()
assert 0xf401+len(extras_code)<=0xfdf9,('extras llenos',hex(0xf401+len(extras_code)))
extras_labels={k:v for k,v in _ex.labels.items()}
print(f'EXTRAS: F401..{0xf401+len(extras_code)-1:04X} ({len(extras_code)} bytes); libres hasta FDF9: {0xfdf9-0xf401-len(extras_code)}')
source=_equs(extras_labels)+source
a0=A(_equs({k:LOW_ORG for k in low_names})+source);a0.run()
main_labels={k:v for k,v in a0.labels.items() if k not in low_names and k not in extras_labels}
lo=A(f' org {LOW_ORG}\n'+_equs(main_labels,set(low_names))+low_src);low_code=lo.run()
low_labels={k:lo.labels[k] for k in low_names}
source=_equs(low_labels)+source
(R/'build/starter.asm').write_text(source)
a=A(source);code=a.run()
assert {k:v for k,v in a.labels.items() if k not in low_names and k not in extras_labels}==main_labels,'enlace inestable'
assert 0x8000+len(code)<0xC000,("bloque principal lleno",hex(0x8000+len(code)))
assert LOW_ORG+len(low_code)<=0x8000,('memoria baja llena',hex(LOW_ORG+len(low_code)))
(R/'build/starter.bin').write_bytes(code)
(R/'build/v11_bajo.bin').write_bytes(low_code)
(R/'build/starter.sym.json').write_text(json.dumps(a.labels,indent=2))
print(f'MEMORIA BAJA: {LOW_ORG:04X}..{LOW_ORG+len(low_code)-1:04X} ({len(low_code)} bytes); libres hasta 7FFF: {0x8000-LOW_ORG-len(low_code)}')
print(f'BLOQUE PRINCIPAL: 8000..{0x8000+len(code)-1:04X}; libres hasta BFFF: {0x4000-len(code)}')
tap=R/'build/HALCONES_ESTELARES_V281.tap'
create_tap(code,'HALCONES',tap,extra_code=extras_code,extra_origin=0xf401,low_code=low_bin_sprites+low_code,low_origin=0x6000)
print(f'ASSEMBLED {len(code)} bytes; SHA256={hashlib.sha256(tap.read_bytes()).hexdigest()}')
