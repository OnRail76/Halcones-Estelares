; ESF V1.0: reversible-free compositor on RAM 0xC000..0xD7FF.
; Static starfield snapshot: 0xD800..0xEFFF. Screen remains 0x4000..0x57FF.
; No XOR rendering: overlapping white sprites are composed by OR, not torn out.
; Alternate phases are prepared at assembly time, not shifted during the game.
; GRIT ENGINE / ARCADE XOR SPRITE MODULE v0.2 (opt-in). ZX Spectrum 48K.
; Based on shifted sprite concepts described by David M. Webb, chapter 12.
; This implementation is independently authored and tested, not a transcription.
; No ROM dependencies, fixed screen. Do not include with shadow framebuffer engine.
; INPUTS spr_data -> table of 8 DW addresses of pre-shifted 1bpp frames
;        spr_x, spr_y -> pixel coords, spr_cols=2/3/4, spr_height=height
; Each phase occupies cols*height bytes. Each sprite is applied by OR.
; Old rectangles are restored from an immutable background; never XOR erase.
; Caller must ensure 0<=spr_y<=192-spr_height and horizontal bytes stay x<192.
; Requires scanline_table: DW address for 192 scanlines, built in asset generator.

sprite_render:
 call sprite_fits         ; FINAL 1.0.1: nunca pintar fuera de las 192 lineas
 ret nc
 ; V1.1: bucles con el estado en registros (HL origen, DE destino, B filas).
 ; La linea siguiente se calcula con la aritmetica de la pantalla del
 ; Spectrum en vez de leer scanline_table en cada fila: la mitad de T-states.
 ld a,(spr_x)
 and 7
 add a,a
 ld e,a
 ld d,0
 ld hl,(spr_data)
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 push de                  ; Origen: fase preparada del sprite.
 call spr_dest            ; DE = byte de destino en la imagen privada C000.
 ld a,d
 add a,128
 ld d,a
 pop hl
 ld a,(spr_height)
 ld b,a
 ld a,(spr_cols)
 cp 5
 jp z,sprite_row5
 cp 4
 jp z,sprite_row4
 cp 3
 jp z,sprite_row3
 jp sprite_row2

; DE = direccion de pantalla (base 4000) de (spr_x,spr_y). Destruye AF,HL.
spr_dest:
 ld a,(spr_y)
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,(spr_x)
 rrca
 rrca
 rrca
 and 31
 add a,e
 ld e,a
 ret

sprite_row2:
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 ld a,e
 sub 1
 ld e,a
 inc d
 ld a,d
 and 7
 jp nz,sprite_row2_n
 ld a,e
 add a,32
 ld e,a
 jp c,sprite_row2_n
 ld a,d
 sub 8
 ld d,a
sprite_row2_n:
 djnz sprite_row2
 ret

sprite_row3:
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 ld a,e
 sub 2
 ld e,a
 inc d
 ld a,d
 and 7
 jp nz,sprite_row3_n
 ld a,e
 add a,32
 ld e,a
 jp c,sprite_row3_n
 ld a,d
 sub 8
 ld d,a
sprite_row3_n:
 djnz sprite_row3
 ret

sprite_row4:
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 ld a,e
 sub 3
 ld e,a
 inc d
 ld a,d
 and 7
 jp nz,sprite_row4_n
 ld a,e
 add a,32
 ld e,a
 jp c,sprite_row4_n
 ld a,d
 sub 8
 ld d,a
sprite_row4_n:
 djnz sprite_row4
 ret

sprite_row5:
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc e
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 ld a,e
 sub 4
 ld e,a
 inc d
 ld a,d
 and 7
 jp nz,sprite_row5_n
 ld a,e
 add a,32
 ld e,a
 jp c,sprite_row5_n
 ld a,d
 sub 8
 ld d,a
sprite_row5_n:
 djnz sprite_row5
 ret

spr_data: dw 0
spr_x: db 0
spr_y: db 0
spr_cols: db 0
spr_height: db 0

; Initialize TWO private 6144-byte pixel planes while the screen shows static stars.
; Shadow image = 0xC000...0xD7FF, immutable sky = 0xD800...0xEFFF.
compositor_init:
 ld hl,0x4000
 ld de,0xC000
 ld bc,6144
 ldir
 ld hl,0x4000
 ld de,0xD800
 ld bc,6144
 ldir
 ret

; V1.1: restaurar (cielo D800 -> trabajo C000) y presentar (C000 -> pantalla)
; con LDI y el contador de bytes en BC: LDI deja P/V=0 al agotarlo, asi que
; no hace falta otro contador. Mismas entradas: spr_x, spr_y, spr_cols, spr_height.
composite_setup:
 call sprite_fits         ; FINAL 1.0.1: si no cabe, no se restaura ni presenta
 jp nc,composite_skip
 call spr_dest            ; DE = destino base 4000
 ld a,(spr_height)
 ld c,a
 ld a,(spr_cols)
 ld b,a
 xor a
composite_mul:
 add a,c
 djnz composite_mul
 ld c,a                   ; BC = filas * columnas (como mucho 160)
 ld a,(spr_cols)
 ret

; Abandona sprite_restore / sprite_present (ambas empiezan con la llamada).
composite_skip:
 pop hl
 ret

; FINAL 1.0.1: comprueba el contrato del compositor (0 <= spr_y y
; spr_y + spr_height <= 192). Carry = cabe. Conserva BC.
sprite_fits:
 push bc
 ld a,(spr_height)
 ld b,a
 ld a,(spr_y)
 add a,b
 jp c,sprite_fits_no
 cp 193
 pop bc
 ret
sprite_fits_no:
 or a
 pop bc
 ret

sprite_restore:
 call composite_setup
 ex af,af'
 ld a,d
 add a,0x98               ; Origen: cielo inmutable D800..EFFF
 ld h,a
 ld l,e
 add a,-24                ; Destino: imagen de trabajo C000..D7FF
 ld d,a
 ex af,af'
 cp 5
 jp z,rest_row5
 cp 4
 jp z,rest_row4
 cp 3
 jp z,rest_row3
 jp rest_row2
rest_row2:
 ldi
 ldi
 ret po
 ld a,e
 sub 2
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,rest_row2
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,rest_row2
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp rest_row2
rest_row3:
 ldi
 ldi
 ldi
 ret po
 ld a,e
 sub 3
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,rest_row3
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,rest_row3
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp rest_row3
rest_row4:
 ldi
 ldi
 ldi
 ldi
 ret po
 ld a,e
 sub 4
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,rest_row4
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,rest_row4
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp rest_row4
rest_row5:
 ldi
 ldi
 ldi
 ldi
 ldi
 ret po
 ld a,e
 sub 5
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,rest_row5
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,rest_row5
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp rest_row5

; Present completed bytes from RAM. No screen erase stage is ever visible.
sprite_present:
 call composite_setup
 ex af,af'
 ld a,d
 add a,128                ; Origen: imagen de trabajo C000; destino: pantalla
 ld h,a
 ld l,e
 ex af,af'
 cp 4
 jp z,pres_row4
 cp 5
 jp z,pres_row5
 cp 3
 jp z,pres_row3
 jp pres_row2
pres_row2:
 ldi
 ldi
 ret po
 ld a,e
 sub 2
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,pres_row2
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,pres_row2
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp pres_row2
pres_row3:
 ldi
 ldi
 ldi
 ret po
 ld a,e
 sub 3
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,pres_row3
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,pres_row3
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp pres_row3
pres_row4:
 ldi
 ldi
 ldi
 ldi
 ret po
 ld a,e
 sub 4
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,pres_row4
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,pres_row4
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp pres_row4
pres_row5:
 ldi
 ldi
 ldi
 ldi
 ldi
 ret po
 ld a,e
 sub 5
 ld e,a
 ld l,a
 inc d
 inc h
 ld a,d
 and 7
 jp nz,pres_row5
 ld a,e
 add a,32
 ld e,a
 ld l,a
 jp c,pres_row5
 ld a,d
 sub 8
 ld d,a
 ld a,h
 sub 8
 ld h,a
 jp pres_row5

; --------------- PROGRESSIVE REPAIR OF PHYSICAL VRAM ---------------------
; Last resort for a persistent stray pixel in *actual* Spectrum VRAM, which
; cannot be reproduced by the partial Z80 functional interpreter. A renderer
; presentation bug or an unlucky on-screen write should never leave a fixed
; enemy forever. This checks the completed private image ($C000..$D7FF),
; not the stars-only background, and copies 4 different visible scanlines
; each update. Thus all 192 scanlines are re-synchronized within 48 ticks.
; This DOES NOT prove the source of corruption has been fixed. It limits its
; lifetime while the optimized compositor is studied under Fuse.
; Entradas: no arguments; corrupts AF/BC/DE/HL, not IX/IY.
compositor_scrub:
 ld a,4                    ; Low-cost safety check: 4 scanlines per tick.
 ld (scrub_rows_left),a    ; Store the loop count away from BC (LDIR clobbers).
scrub_row:
 ld a,(scrub_y)           ; Current scanline index 0..191.
 ld l,a                   ; HL low = scanline Y.
 ld h,0                   ; HL is 16-bit unsigned Y.
 add hl,hl                ; Each scanline_table entry is a word (2 bytes).
 ld de,scanline_table     ; Table maps real Spectrum scanline addresses.
 add hl,de                ; HL = &scanline_table[Y].
 ld e,(hl)                ; DE low = offset of corresponding real screen row.
 inc hl                   ; Advance to high byte.
 ld d,(hl)                ; DE = $4000-based screen scanline address.
 ld h,d                   ; Copy high byte to source pointer.
 ld l,e                   ; Copy low byte to source pointer.
 ld a,h                   ; Source is current composed work screen + $8000.
 add a,128                ; $40xx -> $C0xx ... $57xx -> $D7xx.
 ld h,a                   ; HL points at authoritative composed pixels.
 ld bc,24                 ; Copy only 192px left playfield (do not touch HUD).
 ldir                     ; 24-byte LDIR, source HL, real screen destination DE.
 ld a,(scrub_y)           ; Advance repair cursor.
 inc a                    ; Y++.
 cp 192                   ; End of playfield scanlines?
 jp nz,scrub_advance      ; Continue until next wrap.
 xor a                    ; Scanline zero after 191.
scrub_advance:
 ld (scrub_y),a           ; Save cursor for next update.
 ld a,(scrub_rows_left)   ; Remaining rows in this update.
 dec a                    ; One scanline repaired.
 ld (scrub_rows_left),a   ; Save updated counter.
 jp nz,scrub_row          ; Continue 4 lines.
 ret                      ; Done: no duplicate colors or HUD writes.

scrub_y: db 0             ; Scanline repair cursor, 0..191.
scrub_rows_left: db 0     ; Countdown over 8 rows.
