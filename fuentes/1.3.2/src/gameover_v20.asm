; HALCONES ESTELARES V2.0: real arcade GAME OVER, fixed 3-second input gate.
; Screen artwork is authentic 6912-byte Spectrum SCR, RLE encoded into a
; supplementary CODE block in RAM $F799, separate from main program.
; No BASIC/ROM calls, no auto-return to title when SPACE is held from death.
; gameover_mode=1 is timed by IM2 at precisely 50Hz, independently of FPS.

; IM2 safe: modifies ONLY AF and HL; ISR preserves them around this call.
gameover_irq_tick:
 ld a,(gameover_mode)       ; 0 outside Game Over.
 or a
 ret z
 ld hl,(gameover_timer)    ; 150 ticks loaded on entry.
 ld a,h
 or l
 ret z                      ; Saturate at zero until loop observes it.
 dec hl                     ; Count one actual hardware IRQ.
 ld (gameover_timer),hl
 ret

; Called once when player_lives becomes 0, exits main combat loop.
gameover_enter:
 call gameover_screen_show  ; Native GAME OVER screen, "PULSA SPACE" hidden.
 call gameover_score_draw   ; The ACTUAL final points from kills * 10.
 call record_check          ; V1.2: record batido?
 call gameover_record_draw  ; V1.2: record y NUEVO RECORD.
 ; START COUNTING ONLY AFTER THE COMPLETE SCREEN IS VISIBLE.
 di                         ; Timer/state changed atomically relative to IM2.
 ld hl,150                  ; PAL Spectrum: 3 complete seconds at 50Hz.
 ld (gameover_timer),hl
 ld a,1
 ld (gameover_mode),a
 ei
 ld hl,tune_gameover        ; V1.2: melodia triste, o alegre si hay record
 ld a,(new_record)
 or a
 jr z,gameover_tune
 ld hl,tune_record
gameover_tune:
 ld de,0
 call music_start
gameover_wait_3_seconds:
 call music_frame           ; V1.2: (antes HALT) sin leer mandos.
 ld hl,(gameover_timer)
 ld a,h
 or l
 jr nz,gameover_wait_3_seconds
 xor a
 ld (gameover_mode),a     ; Stop IRQ gate after timer expires.
 call gameover_prompt_show  ; Reveal pre-existing pixel text by ATTR change.
gameover_wait_release:
 call music_frame
 call any_fire_pressed      ; V1.1: cualquier fuego (teclado, Sinclair, Kempston).
 jr z,gameover_wait_release ; Require released SPACE before allowing return.
gameover_wait_press:
 call music_frame
 call any_fire_pressed
 jr nz,gameover_wait_press
 jp title_session_start     ; Exactly one SPACE returns to TITLE, not game.

; Same validated FF/RLE decompressor as title. 6912 native screen bytes.
gameover_screen_show:
 ld hl,0xf799               ; Supplement follows 528 MOAI + 392 Jupiter bytes.
 ld de,0x4000               ; Fresh physical native Spectrum VRAM destination.
 jp lz_unpack               ; V1.2: comprimida LZ.

; Make hidden PULSA SPACE visible in native attribute row21, cols11..20.
; Bitmap pixels were decoded during the first GAME OVER SCR load.
gameover_prompt_show:
 ld hl,0x5aab               ; 0x5800 + 21*32 + 11.
 ld b,10                    ; Exactly ten 8x8 character cells.
 ld a,0x44                  ; BRIGHT GREEN foreground / black background.
gameover_prompt_cell:
 ld (hl),a
 inc hl
 djnz gameover_prompt_cell
 ret

; Display six digits, 00xxxx0 with actual 0..255 kills multiplied by ten.
; Columns 13..18, at pixel Y126, all safe inside prepared cyan attr cells.
gameover_score_draw:
 xor a
 ld e,13
 call gameover_digit_draw
 call score_to_digits        ; V1.1: marcador de 16 bits.
 ld a,(score_digits)
 ld e,14
 call gameover_digit_draw
 ld a,(score_digits+1)
 ld e,15
 call gameover_digit_draw
 ld a,(score_digits+2)
 ld e,16
 call gameover_digit_draw
 ld a,(score_digits+3)
 ld e,17
 call gameover_digit_draw
 xor a
 ld e,18
 call gameover_digit_draw
 ret

; A=decimal digit 0..9, E=8px column, uses original native 7-byte font.
gameover_digit_draw:
 push af
 ld a,e
 ld (go_col),a
 pop af
 ld hl,digit_bitmaps
 or a
 jr z,gameover_glyph_found
 ld b,a
 ld de,7
gameover_glyph_advance:
 add hl,de
 djnz gameover_glyph_advance
gameover_glyph_found:
 ld (go_glyph),hl
 ld a,126
 ld (go_y),a
gameover_digit_row:
 ld a,(go_y)
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld a,(go_col)
 ld c,a
 ld b,0
 add hl,bc
 ld de,(go_glyph)
 ld a,(de)
 ld (hl),a
 inc de
 ex de,hl
 ld (go_glyph),hl
 ld a,(go_y)
 inc a
 ld (go_y),a
 cp 133
 jr nz,gameover_digit_row
 ret

gameover_mode: db 0
gameover_timer: dw 0
go_col: db 0
go_y: db 0
go_glyph: dw 0
