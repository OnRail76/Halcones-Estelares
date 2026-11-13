; ZX48 HALCONES V2.4: ROM-free victory interlude for EACH defeated MOAI.
; '¡MUY BIEN!' / 'ENTRANDO EN FASE: XX' in genuine 6912-byte SCR.
; Blocks for exactly 150 IM2 interrupts (~3s PAL), then resumes automatically.
; Reuses gameover_irq_tick counter (mode=2); GAME OVER mode remains 1.
; Full screen restoration preserves kills/lives/shield state and compositor.

phase_interlude_enter:
 call phase_screen_show
 call phase_number_draw
 call phase_stats_draw      ; V1.2: puntos, vidas y record.
 di                         ; Atomic 16-bit IRQ timer initialization.
 ld hl,150
 ld (gameover_timer),hl
 ld a,2
 ld (gameover_mode),a
 ei
 ld hl,tune_victory         ; V1.2: fanfarria de victoria
 ld de,0
 call music_start
phase_interlude_wait:
 call music_frame           ; V1.2: (antes HALT) sin leer mandos.
 ld hl,(gameover_timer)
 ld a,h
 or l
 jr nz,phase_interlude_wait
 xor a
 ld (gameover_mode),a
 ; Rebuild exactly the same screen environment as before victory.
 ; Immutable sky at D800 is already free of Jupiter and the defeated MOAI.
 call arcade_screen_clear
 call hud_install
 call frame_install
 call boss_scene_sync         ; Work buffer and live 192px playfield in sync.
 call stars_v13_draw_all      ; Restore all 32 star pixels erased by scene sync.
 call stars_v13_present_initial ; Keep visible star state identical to work.
 call color_shadow_init      ; Restore private attribute palette from real VRAM.
 jp hud_draw_all             ; V1.2: marcador completo (puntos, caras, escudo, fase).

phase_screen_show:
 ld hl,phase_lz              ; V1.2: comprimida LZ.
 ld de,0x4000
 jp lz_unpack

phase_number_draw:
 ; Decimal 01..99, rendered using the exact native Z80 digit blitter.
 ld a,(phase_number)
 ld c,0
phase_divide10:
 cp 10
 jr c,phase_tens_done
 sub 10
 inc c
 jr phase_divide10
phase_tens_done:
 ld (phase_units),a
 ld a,c
 ld e,15
 call gameover_digit_draw    ; Y=126..132, columns prepared in CYAN.
 ld a,(phase_units)
 ld e,16
 call gameover_digit_draw
 ret

phase_number: db 1           ; First cycle is FASE 01, first victory -> FASE 02.
phase_units: db 0
