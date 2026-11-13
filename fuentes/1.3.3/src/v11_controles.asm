; HALCONES ESTELARES 1.1 — CONTROLES, RITMO FIJO Y PAUSA
; Variables de trabajo en $F001..$F0FF (libre, entre el testigo $F000 y los
; atributos privados $F100). Se ponen a cero al arrancar (v11_boot_clear).
input_bits equ 0xf010      ; bit0 dcha, 1 izda, 2 abajo, 3 arriba, 4 fuego (1=pulsado)
kempston_ok equ 0xf011     ; 1 = hay interfaz Kempston (detectada en el titulo)
kempston_mode equ 0xf012   ; 1 = la partida se juega con el joystick Kempston
tick_irqs equ 0xf013       ; interrupciones desde el ultimo tick de juego
game_paused equ 0xf014     ; 1 = pausa: el IM2 no avanza ningun temporizador
pause_held equ 0xf015      ; flanco de la tecla H
grace_irqs equ 0xf016      ; V1.1: invulnerabilidad extra tras reaparecer (IRQs)
enemy_fire_cd equ 0xf017   ; V1.1: ticks hasta el proximo disparo enemigo
card_ticks equ 0xf018      ; V1.1: ticks que quedan del cartel de oleada
card_wave equ 0xf019       ; V1.1: numero de oleada (1..6) del cartel
life_next equ 0xf01a       ; V1.1: millares de puntos para la proxima vida extra
score_words equ 0xf020     ; V1.1: kills de 16 bits (puntos/10), tope 9999
score_digits equ 0xf022    ; V1.1: millares, centenas, decenas, unidades
boss_eye equ 0xf01b        ; V1.1: ojo del MOAI que dispara (alterna)
card_len equ 40            ; cartel: 40 ticks = 1,6 s

tick_frames equ 2          ; 2 interrupciones por tick = 25 ticks/s constantes

; Lee teclado (O/P/A/Q/SPACE), Sinclair (6/7/8/9/0) y, si se eligio, Kempston.
; Salida: input_bits. Destruye AF, BC, DE.
input_poll:
 ld d,0
 ld bc,0xdffe              ; P (bit0) dcha, O (bit1) izda
 in a,(c)
 cpl
 and 3
 ld d,a
 ld b,0xfd                 ; A = escudo (abajo)
 in a,(c)
 rra
 jr c,ip_q
 set 2,d
ip_q:
 ld b,0xfb                 ; Q = escudo (arriba)
 in a,(c)
 rra
 jr c,ip_space
 set 3,d
ip_space:
 ld b,0x7f                 ; SPACE = fuego
 in a,(c)
 rra
 jr c,ip_sinclair
 set 4,d
ip_sinclair:
 ld b,0xef                 ; 6 izda, 7 dcha, 8 abajo, 9 arriba, 0 fuego
 in a,(c)
 cpl
 ld e,a
 and 1
 jr z,ip_s9
 set 4,d
ip_s9:
 bit 1,e
 jr z,ip_s8
 set 3,d
ip_s8:
 bit 2,e
 jr z,ip_s7
 set 2,d
ip_s7:
 bit 3,e
 jr z,ip_s6
 set 0,d
ip_s6:
 bit 4,e
 jr z,ip_kempston
 set 1,d
ip_kempston:
 ld a,(kempston_mode)
 or a
 jr z,ip_store
 in a,(0x1f)
 and 0x1f
 or d
 ld d,a
ip_store:
 ld a,d
 ld (input_bits),a
 ret

; Espera a que pasen tick_frames interrupciones desde el ultimo tick: el juego
; avanza siempre a 25 ticks/s, ni mas rapido en escenas ligeras ni a saltos.
tick_wait:
 xor a                      ; V1.3: el juego ya acabo su trabajo: aqui no
 ld (snd_mid_ok),a          ; hace falta el trozo de mitad de tick.
; V1.3: sin DI. Con HALT hacia falta para no dormirse si la IRQ llegaba entre
; la comprobacion y el HALT; ahora la espera compara tick_irqs con E sin parar
; (si cambia, vuelve enseguida) y una IRQ nunca se pierde.
tick_wait_loop:
 ld a,(tick_irqs)
 cp tick_frames
 jr nc,tick_go
 ld e,a
 call snd_slice              ; V1.2: el efecto suena en el tiempo que sobra.
 jr tick_wait_loop
tick_go:
 xor a
 ld (tick_irqs),a
 call snd_budget_set        ; V1.3: sonido a mitad del tick que empieza.
 jp snd_tick                 ; V1.2: barrido y segmentos del efecto, 1 vez por tick.

; IM2 (guarda AF y HL el llamador).
grace_irq_tick:
 ld a,(grace_irqs)
 or a
 ret z
 dec a
 ld (grace_irqs),a
 ret


v11_boot_clear:
 ld hl,0xf001
 ld de,0xf002
 ld bc,254
 ld (hl),0
 ldir
 ld a,0x5a                   ; V1.2: semilla del ruido del beeper (no puede ser 0).
 ld (snd_rng),a
 ret

; Ticks (a 25/s) entre disparos enemigos: cuervos, cazadores, kamikazes, MOAI.
; Fase 1 = la de siempre algo mas tranquila; despues se acelera poco a poco.
fire_period_first: db 80,64,32,48
fire_period_later: db 64,48,20,28


; ---- V1.2: rutinas que en la 1.1 estaban en memoria baja ----

; ---------------------------------------------------------------------------
; MARCADOR DE 16 BITS Y VIDA EXTRA
; score_words cuenta impactos (puntos/10) hasta 9999 = 99.990 puntos.
; Cada 100 impactos (1.000 puntos) se gana una vida, si quedan menos de 3.
score_add_kill:
 ld a,(kills)               ; Byte historico (sin uso para el marcador).
 inc a
 ld (kills),a
 ld hl,(score_words)
 ld de,9999
 or a
 sbc hl,de
 jr nc,sak_counted
 add hl,de
 inc hl
 ld (score_words),hl
sak_counted:
 ld a,(life_next)
 inc a
 cp 100
 jr c,sak_store
 ld a,(player_lives)
 or a
 jr z,sak_reset             ; Ya sin vidas: no se resucita en la explosion final.
 cp 3
 jr nc,sak_reset
 inc a
 ld (player_lives),a        ; lives_hud_present dibuja la sonrisa nueva.
 call badge_shine           ; V1.3: la insignia brilla
 call sfx_life                ; V1.2: arpegio de vida extra
sak_reset:
 xor a
sak_store:
 ld (life_next),a
 jp score_draw

; score_words -> 4 cifras en score_digits. Destruye AF, BC, DE, HL.
score_to_digits:
 ld hl,(score_words)
 ld de,1000
 call sd_div
 ld (score_digits),a
 ld de,100
 call sd_div
 ld (score_digits+1),a
 ld de,10
 call sd_div
 ld (score_digits+2),a
 ld a,l
 ld (score_digits+3),a
 ret
sd_div:
 ld b,0
sd_loop:
 or a
 sbc hl,de
 jr c,sd_done
 inc b
 jr sd_loop
sd_done:
 add hl,de
 ld a,b
 ret

; ---------------------------------------------------------------------------
; CARTEL "OLEADA n" (1..6) ANTES DE CADA FORMACION
; Se escribe en la imagen de trabajo (C000) y en pantalla, fila 11 (y=88..94),
; columnas 9..16, en amarillo brillante. Al acabar se repone el cielo (D800).
wave_card_start:
 ld a,card_len
 ld (card_ticks),a
 ld a,(wave_stage)
 add a,a
 ld b,a
 ld a,(wave_repeat)
 add a,b
 inc a
 ld (card_wave),a
 call hud_phase_draw         ; V1.2: casillas de oleada y numero en el marcador.
 call badge_shine           ; V1.3: la insignia brilla
 call sfx_card
 ld a,0x46
 jp wave_card_attr

wave_card_tick:
 ld a,(card_ticks)
 dec a
 ld (card_ticks),a
 jr z,wave_card_end
 ret

; Tras componer la imagen: redibuja el texto (estrellas y disparos lo pisan)
; en trabajo y pantalla a la vez, asi ambas coinciden al acabar cada tick.
card_draw:
 ld a,(card_ticks)
 or a
 ret z
 ld hl,card_glyphs
 ld e,0x69                  ; Columna 9 de la fila de pixel 88.
 ld c,7
wct_loop:
 ld a,(hl)
 inc hl
 push hl
 ld h,(hl)
 ld l,a
 call card_glyph
 pop hl
 inc hl
 dec c
 jr nz,wct_loop
 ld a,(card_wave)           ; La cifra sale de la fuente del marcador.
 ld l,a
 ld h,0
 ld d,h
 ld b,l
 add hl,hl
 add hl,hl
 add hl,hl
 ld a,l
 sub b
 ld l,a                     ; HL = cifra*7 (cabe en un byte)
 ld bc,digit_bitmaps
 add hl,bc
 call card_glyph
 ret

wave_card_end:
 ld hl,0xe069               ; Cielo inmutable de esas 7 filas -> trabajo y pantalla.
 ld b,7
wce_row:
 push bc
 push hl
 ld b,8
wce_col:
 ld a,(hl)
 ld e,a
 ld a,h
 sub 0x18
 ld d,a                     ; D = fila en C000..
 ld a,e
 ld e,l
 ld (de),a
 res 7,d                    ; .. y en la pantalla (4000..)
 ld (de),a
 inc l
 djnz wce_col
 pop hl
 inc h
 pop bc
 djnz wce_row
 ld a,0x47
 call wave_card_attr
 jp wave_spawn_now

; A = atributo para las 8 celdas del cartel. Se escribe en la sombra privada;
; card_attr_present lo pasa a la pantalla despues del color de los sprites.
wave_card_attr:
 ld hl,0xf269
 ld b,8
wca_loop:
 ld (hl),a
 inc hl
 djnz wca_loop
 ret
card_attr_present:
 ld hl,0xf269
 ld de,0x5969
 ld bc,8
 ldir
 ret

; HL = 7 bytes de la letra, E = byte bajo (0x60+columna). Conserva C y E.
card_glyph:
 ld d,0x48
 ld b,7
cg_row:
 ld a,(hl)
 ld (de),a
 set 7,d
 ld (de),a
 res 7,d
 inc hl
 inc d
 djnz cg_row
 inc e
 ret

card_glyphs:
 dw glyph_o,glyph_l,glyph_e,glyph_a,glyph_d,glyph_a,glyph_sp
glyph_o: db 56,68,68,68,68,68,56
glyph_l: db 64,64,64,64,64,64,124
glyph_e: db 124,64,64,120,64,64,124
glyph_a: db 56,68,68,124,68,68,68
glyph_d: db 120,68,68,68,68,68,120
glyph_sp: db 0,0,0,0,0,0,0


; H = pausa. Borde azul; el IM2 deja quietos escudo, invulnerabilidad y
; reagrupamientos. Otra pulsacion de H continua.
pause_check:
 ld bc,0xbffe
 in a,(c)
 and 16
 jr z,pc_down
 xor a
 ld (pause_held),a
 ret
pc_down:
 ld a,(pause_held)
 or a
 ret nz
 ld a,1
 ld (pause_held),a
 ld (game_paused),a
 call beep_enemy_destroy     ; V1.2: pitido de pausa
 ld a,1
 out (0xfe),a
pc_wait_release:
 halt
 ld bc,0xbffe
 in a,(c)
 and 16
 jr z,pc_wait_release
pc_wait_press:
 halt
 ld bc,0xbffe
 in a,(c)
 and 16
 jr nz,pc_wait_press
 call beep_enemy_destroy
 xor a
 out (0xfe),a
 ld (game_paused),a
 ld (tick_irqs),a
 ret
