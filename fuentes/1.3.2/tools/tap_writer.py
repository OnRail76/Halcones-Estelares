"""Real ZX Spectrum ROM-format TAP with auto-run BASIC + machine code."""
from pathlib import Path
import struct

def block(flag,data):
    payload=bytes([flag])+data
    parity=0
    for byte in payload:parity^=byte
    payload+=bytes([parity])
    return struct.pack('<H',len(payload))+payload

def basic_line(number,tokens):
    payload=tokens+b'\r'
    return struct.pack('>H',number)+struct.pack('<H',len(payload))+payload

def create_tap(code,name,out,origin=32768,extra_code=None,extra_origin=0xf401,low_code=None,low_origin=0x6000):
    assert origin==32768 and len(code)<32768
    # V1.1: CLEAR VAL "24575" (RAMTOP $5FFF): los bloques de $6000 y $8000 quedan
    # por encima de RAMTOP y la pila de la ROM no se pisa al cargar hasta $7FFF.
    prog=(basic_line(10,b'\xfd \xb0 "24575"')+
          basic_line(20,b'\xef "" \xaf')+
          (basic_line(22,b'\xef "" \xaf') if low_code else b'')+
          (basic_line(25,b'\xef "" \xaf') if extra_code else b'')+
          basic_line(30,b'\xf9 \xc0 \xb0 "32768"'))
    label=name.encode('ascii','replace')[:10].ljust(10,b' ')
    head_bas=bytes([0])+label+struct.pack('<HHH',len(prog),10,len(prog))
    head_cod=bytes([3])+label+struct.pack('<HHH',len(code),origin,origin)
    raw=block(0,head_bas)+block(255,prog)+block(0,head_cod)+block(255,code)
    if low_code:
        assert 0x6000<=low_origin and low_origin+len(low_code)<0x8000
        head_low=bytes([3])+b'ESF SPRIT'.ljust(10,b' ')+struct.pack('<HHH',len(low_code),low_origin,low_origin)
        raw+=block(0,head_low)+block(255,low_code)
    if extra_code:
        assert 0xf401<=extra_origin and extra_origin+len(extra_code)<=0xfdfb
        head_extra=bytes([3])+b'ESF EXTRAS'.ljust(10,b' ')+struct.pack('<HHH',len(extra_code),extra_origin,extra_origin)
        raw+=block(0,head_extra)+block(255,extra_code)
    Path(out).write_bytes(raw)
    return raw
