; HALCONES ESTELARES / ESF TITLE BOOT, ZX Spectrum 48K.
; Standard Z80 mnemonics; address $8000 set by src/main.asm.
; Screen unpacker writes exactly $4000-$5AFF: 6,144 bitmap + 768 attributes.
; Assembly: uses only instructions from original Z80; no ROM print calls.
;
; title_screen_show: input none; output VRAM filled; destroys AF BC DE HL.
; title_screen_wait: input fire; output on a fresh press.

title_screen_show:
 ld hl,title_lz                ; V1.2: pantalla comprimida LZ (ver tools/lz.py).
 ld de,0x4000
 ; cae en lz_unpack

; V1.2 DESCOMPRESOR LZ. HL = origen, DE = destino. Formato (tools/lz.py):
; byte C: 0 fin; 1..127 = C literales; 128..191 = copia de C-125 bytes desde
; DE-D con D de 1 byte; 192..255 = copia de C-189 bytes con D de 2 bytes.
; Destruye AF, BC, DE, HL.
lz_src equ 0xf04a
lz_unpack:
 ld a,(hl)
 inc hl
 or a
 ret z
 jp m,lz_match
 ld c,a
 ld b,0
 ldir
 jr lz_unpack
lz_match:
 ld b,0
 cp 192
 jr nc,lz_far
 sub 125
 ld c,a
 ld a,(hl)
 inc hl
 ld (lz_src),hl
 ld l,a
 ld h,b
 jr lz_copy
lz_far:
 sub 189
 ld c,a
 ld a,(hl)
 inc hl
 push af
 ld a,(hl)
 inc hl
 ld (lz_src),hl
 ld h,a
 pop af
 ld l,a
lz_copy:
 push de
 ex de,hl
 or a
 sbc hl,de
 pop de
 ldir
 ld hl,(lz_src)
 jr lz_unpack

; Wait until SPACE is released (fresh press requirement), then pressed.
; ROM ISR remains active at 50 Hz, so HALT does not spin at full speed.
title_screen_wait:
 call kempston_detect          ; V1.1: hay Kempston? (bus flotante = no)
 call title_record_draw        ; V1.2: record de la sesion
 ld hl,tune_title              ; V1.2: melodia del titulo; V1.3.2: suena UNA
 ld de,0                       ; vez cada vez que se llega al titulo y luego silencio
 call music_start
 ld a,75                     ; A leisurely attract-mode baseline hold, 1.5s PAL.
 ld (title_pulse_countdown),a
 xor a                       ; Phase zero: display original yellow title.
 ld (title_pulse_phase),a
 title_wait_release:
 call music_frame              ; V1.2: musica hasta la siguiente interrupcion.
 call any_fire_pressed         ; V1.1: SPACE, 0 (Sinclair) o fuego Kempston.
 jr z,title_wait_release       ; If key held at boot, require a release.
title_wait_press:
 call music_frame              ; V1.2: musica hasta la siguiente interrupcion.
 call title_pulse_tick         ; Attract mode: brief white pulse, original logo bitmap untouched.
 call title_twinkle            ; V1.2: estrellas que titilan.
 call any_fire_pressed
 jr nz,title_wait_press        ; Do not start while SPACE remains unpressed.
 call title_choose_controls    ; V1.1: fuego del Kempston = partida con joystick.
 call music_stop               ; V1.2: silencio al empezar.
title_wait_start_release:
 halt                          ; Wait until the start key is released again.
 call any_fire_pressed
 jr z,title_wait_start_release ; Hold here until the key is physically released.
 ret                           ; Start gameplay without reusing the start press as FIRE.

 ; TITLE PULSE ARCADE — original V2.7 logo is NEVER redrawn or relettered.
; Pattern 75 frames ORIGINAL, 6 frames WHITE, 9 frames ORIGINAL,
; 3 frames WHITE, then repeat. The double pulse is subtle and readable.
; Modifies ONLY ink-yellow attribute cells for rows y=8..63.
; Every other character cell (red LEDs, cyan subtitle, credits, controls)
; retains exactly its original attribute. 224 originals reside at $7D40.
; Preserves AF/BC/DE/HL, stack and all game-state variables.
title_pulse_tick:
 push af
 push bc
 push de
 push hl
 ld a,(title_pulse_countdown)
 dec a
 ld (title_pulse_countdown),a
 jr nz,title_pulse_done
 ld a,(title_pulse_phase)
 inc a
 and 3
 ld (title_pulse_phase),a
 ld e,a
 ld d,0
 ld hl,title_pulse_times
 add hl,de
 ld a,(hl)
 ld (title_pulse_countdown),a
 ; V1.2: se devuelven a amarillo solo las celdas que se blanquearon (mascara
 ; de 224 bits en $F070), sin guardar una copia de 224 atributos.
 ld hl,0x5820
 ld de,pulse_mask
 ld b,28
title_pulse_restore:
 ld a,(de)
 ld c,8
title_pulse_restore_bit:
 rrca
 jr nc,title_pulse_restore_skip
 ld (hl),0x46
title_pulse_restore_skip:
 inc hl
 dec c
 jr nz,title_pulse_restore_bit
 xor a
 ld (de),a
 inc de
 djnz title_pulse_restore
 ; Only white-highlight phases 1 & 3; phase 0/2 are the original.
 ld a,(title_pulse_phase)
 and 1
 jr z,title_pulse_done
 ld hl,0x5820
 ld de,pulse_mask
 ld b,28
title_pulse_white:
 push bc
 ld bc,0x0100               ; C = mascara del byte, B = bit en curso
title_pulse_white_bit:
 ld a,(hl)
 and 7
 cp 6                           ; Original bright-yellow INK only.
 jr nz,title_pulse_white_next
 ld (hl),0x47                 ; Change ink to bright WHITE on black.
 ld a,c
 or b
 ld c,a
title_pulse_white_next:
 inc hl
 ld a,b
 add a,a
 ld b,a
 jr nz,title_pulse_white_bit
 ld a,c
 ld (de),a
 inc de
 pop bc
 djnz title_pulse_white
 title_pulse_done:
 pop hl
 pop de
 pop bc
 pop af
 ret
 pulse_mask equ 0xf070
 title_pulse_times: db 75,6,9,3
 title_pulse_countdown: db 75
 title_pulse_phase: db 0
