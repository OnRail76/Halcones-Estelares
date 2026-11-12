; HALCONES ESTELARES V1.9: first real MOAI encounter, source image retained.
; 48x88 1bpp bitmap lives in supplemental TAP CODE block at $F401.
; This area does not touch compositor, colour shadow, IM2 trampoline or stack.
; Fight uses original user's exact pixel-art design resized without redrawing.
; Wave stage 3 selects this encounter. No FLASH attribute (eyes timed in software).

boss_start:
 ld a,18                    ; 18 player shot hits to defeat boss (prototype balance).
 ld (boss_hp),a
 call boss_v12_start        ; V1.2: grietas, boca, derrumbe y luna a cero.
 call bg_clear              ; V1.2: el MOAI y Jupiter ocupan el cielo sin fondo.
 ld a,8
 ld (boss_death_left),a  ; Short red/white destruction flash on defeat.
 xor a
 ld (wave_done),a
 ; Install 56x56 Jupiter from user's original image into immutable sky.
 ; V2.7: X128..183, Y96..151. Below the MOAI and wholly inside playfield.
 call boss_planet_install
 ; Install 48x88 face in immutable background D800-EFFF.
 ld hl,0xf401                ; Source MOAI bitmap from secondary 48K TAP CODE block.
 ld (boss_src),hl
 ld a,8                     ; Face top row 8, x=72=character column 9.
 ld (boss_y),a
boss_row:
 ld a,(boss_y)
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)                 ; DE = bitmap screen row, x=0.
 ld a,e
 add a,9                    ; x=72, 9 character columns.
 ld e,a
 ld a,d
 add a,152                  ; $4000 screen -> $D800 immutable background.
 ld d,a
 ld hl,(boss_src)
 ld bc,6                     ; 48px native bitmap: 6 bytes, no clipping.
 ldir
 ld (boss_src),hl
 ld a,(boss_y)
 inc a
 ld (boss_y),a
 cp 96                       ; 8 + 88 rows.
 jr nz,boss_row
 ; Set the MOAI face BRIGHT MAGENTA, exclusive to the boss encounter.
 ; Existing red/dark eye cells still override their own two 8x8 attributes.
 call boss_palette_white
 call boss_planet_palette_cyan ; BRIGHT cyan on black for the static Jupiter.
 ; One-time scene cut: replace work with authoritative sky, then screen.
 call boss_scene_sync
 call sfx_siren               ; V1.2: sirena mientras entra el MOAI
 ret

boss_scene_sync:
 ld hl,0xd800              ; Immutable 6144 byte background source.
 ld de,0xc000              ; First bring complete work buffer into sync.
 ld bc,6144
 ldir
 ; Only present the LEFT 24 bitmap columns; protect the live HUD numbers!
 xor a
 ld (boss_y),a
boss_scene_screen_row:
 ld a,(boss_y)
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)                ; DE = real screen row at x0.
 ld h,d
 ld l,e                   ; HL = same row in real VRAM.
 ld a,h
 add a,128                 ; HL=$C000-based composed background row.
 ld h,a
 ld bc,24
 ldir                       ; Copy only playfield, NOT HUD (x192..255).
 ld a,(boss_y)
 inc a
 ld (boss_y),a
 cp 192
 jr nz,boss_scene_screen_row
 ret

boss_palette_white:
 ld a,0x43                  ; V2.6: BRIGHT MAGENTA, black paper
 jp boss_palette_apply
boss_palette_red:
 ld a,0x42
 jp boss_palette_apply
boss_palette_apply:
 ld (boss_ink),a
 ld hl,0x5829              ; (y=8,x=72) color row 1, cell column 9.
 ld de,0xf129              ; Private shadow cell at the same logical index.
 ld b,11                   ; 88px high, 11 rows of 8x8 attributes.
boss_white_attr_row:
 push bc
 ld c,6                    ; Exactly six 8x8 cells per row (48px).
 ld a,(boss_ink)          ; One dedicated color for the whole portrait.
boss_white_attr_col:
 ld (hl),a                 ; Visible Spectrum attribute.
 ld (de),a                 ; Shadow attribute mirrors it.
 inc hl
 inc de
 dec c
 jr nz,boss_white_attr_col
 ld bc,26                  ; Skip unused 32-6 cells before next row.
 add hl,bc
 ex de,hl
 add hl,bc
 ex de,hl
 pop bc
 djnz boss_white_attr_row
 ret

boss_eye_tick:
 ; V1.2: los ojos se encienden justo antes de cada disparo (y con la boca
 ; abierta); el resto del tiempo estan apagados. Avisan de lo que viene.
 ld a,(boss_hp)
 or a
 ret z
 ld a,(mouth_ticks)
 or a
 ld a,0x42
 jr nz,boss_eye_apply
 ld a,(enemy_fire_cd)
 cp 10
 ld a,0x42
 jr c,boss_eye_apply
 ld a,0x40
boss_eye_apply:
 ld (0x586a),a              ; Eye L: attribute row3 col10 ($5800+96+10).
 ld (0x586d),a              ; Eye R: attribute row3 col13.
 ld (0xf16a),a              ; Same two cells in private palette shadow.
 ld (0xf16d),a
 ret

boss_update:
 ld a,(boss_hp)
 or a
 jp nz,boss_alive_tick      ; V1.2: boca que se cierra y luna que cruza.
 ld a,(boss_death_left)    ; Eight update flashes before cleaning the stage.
 or a
 jp z,boss_erase_start
 dec a
 ld (boss_death_left),a
 and 1
 jp z,boss_flash_red
 call boss_palette_white
 ret
boss_flash_red:
 call boss_palette_red
 ret
boss_erase_start:
 call boss_blocks_tick      ; V1.2: se derrumba por bloques (3 por tick).
 ret nz
 call boss_planet_erase
 call boss_scene_sync
 call boss_planet_palette_white  ; Restore white starfield attributes for next wave.
 ld a,0x47
 ld (0x586a),a
 ld (0x586d),a
 ld (0xf16a),a
 ld (0xf16d),a
 call stars_v13_init       ; Reintroduce star positions into clean shadow.
 call beep_boss_destroy      ; Powerful extended beeper destruction cue.
 ld a,(wave_cycle)
 inc a
 cp 5
 jr c,boss_cycle_keep
 ld a,4
boss_cycle_keep:
 ld (wave_cycle),a         ; Difficulty ceiling unchanged: 4.
 ld a,(phase_number)       ; Display count is independent of difficulty ceiling.
 cp 99
 jr nc,boss_phase_count_done
 inc a
 ld (phase_number),a
boss_phase_count_done:
 call bg_draw               ; V1.2: fondo de la fase nueva (se ve al volver).
 call phase_interlude_enter ; Black screen, 150 real IM2 ticks, automatic return.
 xor a
 ld (wave_stage),a       ; Start next circuit with CROW.
 ld (wave_repeat),a      ; First of two CROW waves on next phase.
 jp wave_spawn            ; Begin next playable phase with preserved lives/score.

; V2.0: Jupiter is part of the immutable background, NOT a moving sprite.
; Data in supplementary CODE block directly after 528-byte MOAI at $F611.
; Screen and work are updated by boss_scene_sync once on scene change.
; V2.7 placement x=128..183, y=96..151; 7 bytes/row x 56 rows.
boss_planet_install:
 ld hl,0xf611                 ; Data source starts just after 48*88/8 MOAI.
 ld (planet_source),hl
 ld a,1                       ; 1 means copy planet image.
 ld (planet_mode),a
 jp boss_planet_blit
boss_planet_erase:
 xor a                         ; 0 means restore empty sky.
 ld (planet_mode),a
 jp boss_planet_blit
boss_planet_blit:
 ld a,96                      ; V2.7: Jupiter starts below MOAI (8..95).
 ld (planet_y),a
planet_bitmap_row:
 ld a,(planet_y)
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)                 ; $4000 logical screen line.
 ld a,e
 add a,16                   ; X128: byte column 16.
 ld e,a
 ld a,d
 add a,152                  ; $4000 => $D800 immutable base.
 ld d,a
 ld a,(planet_mode)
 or a
 jr z,planet_blank_row
 ld hl,(planet_source)
 ld bc,7                     ; Seven source bytes per row.
 ldir
 ld (planet_source),hl
 jr planet_next_row
planet_blank_row:
 xor a
 ld b,7
planet_blank_byte:
 ld (de),a
 inc de
 djnz planet_blank_byte
planet_next_row:
 ld a,(planet_y)
 inc a
 ld (planet_y),a
 cp 152                      ; Y96 + 56 rows, stops before ESF-01 row.
 jr nz,planet_bitmap_row
 ret

; Set exactly 7x7 Spectrum color cells at x128,y96. Both visible
; attributes and shadow palette must agree or the next tick reverts cyan.
boss_planet_palette_cyan:
 ld a,0x45                   ; BRIGHT CYAN, black PAPER, no FLASH.
 jp boss_planet_palette_apply
boss_planet_palette_white:
 ld a,0x47                   ; BRIGHT WHITE for normal starfield.
boss_planet_palette_apply:
 ld (planet_ink),a
 ld hl,0x5990                ; $5800 + row12*32 + col16.
 ld de,0xf290                ; Same cell in private color shadow.
 ld b,7                      ; Seven 8-pixel-high cell rows.
planet_attr_row:
 push bc
 ld c,7                      ; Seven columns at x128..183.
planet_attr_col:
 ld a,(planet_ink)
 ld (hl),a
 ld (de),a
 inc hl
 inc de
 dec c
 jr nz,planet_attr_col
 ld bc,25                     ; Skip 32 - 7 attribute cells.
 add hl,bc
 ex de,hl
 add hl,bc
 ex de,hl
 pop bc
 djnz planet_attr_row
 ret

planet_source: dw 0
planet_mode: db 0
planet_y: db 0
planet_ink: db 0x45

boss_hp: db 0
boss_death_left: db 0
boss_ink: db 0x43
boss_y: db 0
boss_src: dw 0
