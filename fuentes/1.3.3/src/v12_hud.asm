; HALCONES ESTELARES 1.2 - MARCADOR NUEVO (parte que cambia).
; La parte fija (bandas, raíles, logo ESF) se descomprime en hud_install.
; Todo se dibuja en la pantalla real (columnas 25..30), fuera del compositor.
hud_buf equ 0xf030          ; bytes de trabajo para componer cifras
hp_addr equ 0xf040          ; direccion de pantalla en curso (2 bytes)
hp_stride equ 0xf042        ; avance del origen por fila (bytes)
shield_state_shown equ 0xf043
record_words equ 0xf046     ; record de la sesion (impactos, como score_words)
hud_tmp equ 0xf048
face_k equ 0xf049
enemy_count equ 0xf0ab
snd_idle equ 0xf0b4         ; V1.3: rato libre del tick (unidades de 26 T)
snd_budget equ 0xf0b6       ; V1.3: trozo de sonido para la mitad del tick
snd_mid_ok equ 0xf0b8       ; V1.3: 1 = el trozo de mitad de tick aun no ha sonado
badge_pos equ 0xf0b9        ; V1.3: brillo de la insignia ESF (0 = parado)
badge_timer equ 0xf0ba      ; V1.3: ticks hasta el siguiente brillo
; V1.2: MOAI y luna (rutinas en src/v12_bajo.asm)
boss_blocks equ 0xf0a0      ; bloques del MOAI que quedan por derrumbar (0 = sin empezar)
boss_bidx equ 0xf0a1        ; bloque siguiente (0..65), avanza de 37 en 37
mouth_ticks equ 0xf0a2      ; ticks que la boca sigue abierta
crack_seed equ 0xf0a3
crack_x equ 0xf0a4
crack_y equ 0xf0a5
crack_len equ 0xf0a6
mouth_mode equ 0xf0a7
moon_x equ 0xf0a8           ; x de la luna (0 = aun no dibujada)
moon_clock equ 0xf0a9
blk_col equ 0xf0aa
moon_y equ 113

; hud_put: copia B filas de 1 byte a la columna C desde la linea A.
; HL = origen; avanza hp_stride por fila. Destruye AF, B, DE, HL.
hud_put:
 push hl
 ld l,a
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ex de,hl
 pop hl
hud_put_row:
 ld a,(de)
 add a,c
 ld (hp_addr),a
 inc de
 ld a,(de)
 ld (hp_addr+1),a
 inc de
 push de
 ld de,(hp_addr)
 ld a,(hl)
 ld (de),a
 ld a,(hp_stride)
 ld e,a
 ld d,0
 add hl,de
 pop de
 djnz hud_put_row
 ret

; Todo el marcador (al empezar la partida y tras la pantalla de fase).
hud_draw_all:
 ld a,255
 ld (lives_displayed),a
 ld (shield_meter_displayed),a
 ld (shield_state_shown),a
 call score_draw
 call lives_hud_present
 call shield_bar_present
 jp hud_phase_draw

; PUNTOS: "0" + 4 cifras de score_words + "0" en cifras gruesas 7x8.
score_draw:
 call score_to_digits
 ld hl,score_digits
 ld de,hud_buf+1
 ld bc,4
 ldir
 xor a
 ld (hud_buf),a
 ld (hud_buf+5),a
 ld a,1
 ld (hp_stride),a
 ld c,25
 ld hl,hud_buf
score_big_loop:
 push hl
 ld l,(hl)
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,hud_big_digits
 add hl,de
 ld b,8
 ld a,12
 call hud_put
 pop hl
 inc hl
 inc c
 ld a,c
 cp 31
 jr nz,score_big_loop
 ; RECORD: si los puntos lo superan, se actualiza en vivo.
 ld hl,(score_words)
 ld de,(record_words)
 or a
 sbc hl,de
 jr c,record_draw
 ld hl,(score_words)
 ld (record_words),hl
; RECORD en cifras de 3x5, dos por byte, columnas 28..30.
record_draw:
 call record_digits
 ld c,28
 ld hl,hud_buf
record_pair_loop:
 ld a,(hl)
 inc hl
 ld b,(hl)
 inc hl
 push hl
 push bc
 call nibble_pair
 pop bc
 ld a,1
 ld (hp_stride),a
 ld hl,hud_buf+8
 ld b,5
 ld a,26
 call hud_put
 pop hl
 inc c
 ld a,c
 cp 31
 jr nz,record_pair_loop
 ret

; A = cifra izquierda, B = cifra derecha -> 5 filas en hud_buf+8..+12.
nibble_pair:
 push bc
 call nibble_addr
 ld de,hud_buf+8
 ld b,5
nibble_left:
 ld a,(hl)
 rlca
 rlca
 rlca
 rlca
 ld (de),a
 inc hl
 inc de
 djnz nibble_left
 pop bc
 ld a,b
 call nibble_addr
 ld de,hud_buf+8
 ld b,5
nibble_right:
 ld a,(de)
 or (hl)
 ld (de),a
 inc hl
 inc de
 djnz nibble_right
 ret
nibble_addr:                    ; HL = hud_nibble_digits + A*5
 ld l,a
 ld h,0
 ld d,h
 ld e,l
 add hl,hl
 add hl,hl
 add hl,de
 ld de,hud_nibble_digits
 add hl,de
 ret

; ESCUDO: 8 segmentos; LISTO (verde parpadeante), ACTIVO (cian) o CARGANDO
; (amarillo) con la barra en rojo-amarillo-verde mientras se recarga.
shield_bar_present:
 ld a,(shield_meter)
 ld b,a
 ld a,(shield_state)
 ld c,a
 ld a,(shield_meter_displayed)
 cp b
 jr nz,shield_bar_redraw
 ld a,(shield_state_shown)
 cp c
 ret z
shield_bar_redraw:
 ld a,b
 ld (shield_meter_displayed),a
 ld a,c
 ld (shield_state_shown),a
 ld l,b
 ld h,0
 ld d,h
 ld e,l
 add hl,hl
 add hl,de
 add hl,hl
 ld de,hud_shield_rows
 add hl,de
 xor a
 ld (hp_stride),a
 ld c,25
shield_bar_col:
 push hl
 ld b,4
 ld a,74
 call hud_put
 pop hl
 inc hl
 inc c
 ld a,c
 cp 31
 jr nz,shield_bar_col
 ld a,(shield_state)
 ld hl,hud_txt_listo
 ld b,0xc4
 ld de,shield_colors_ready
 or a
 jr z,shield_text
 ld hl,hud_txt_activo
 ld b,0x45
 ld de,shield_colors_active
 cp 1
 jr z,shield_text
 ld hl,hud_txt_carga
 ld b,0x06
 ld de,shield_colors_charge
shield_text:
 ld a,b
 ld (hud_tmp),a
 push de
 ld a,6
 ld (hp_stride),a
 ld c,25
shield_text_col:
 push hl
 ld b,5
 ld a,82
 call hud_put
 pop hl
 inc hl
 inc c
 ld a,c
 cp 31
 jr nz,shield_text_col
 ld hl,0x5800+10*32+25
 ld a,(hud_tmp)
 ld b,6
shield_text_attr:
 ld (hl),a
 inc hl
 djnz shield_text_attr
 pop hl
 ld de,0x5800+9*32+25
 ld bc,6
 ldir
; La sombra privada de atributos sigue siendo copia exacta de la pantalla
; tambien en el marcador (columnas 24..31), aunque el compositor no lo toque.
hud_attr_sync:
 ld hl,0x5800+24
 ld de,0xf100+24
 ld a,24
has_row:
 ld bc,8
 ldir
 ld bc,24
 add hl,bc
 ex de,hl
 add hl,bc
 ex de,hl
 dec a
 jr nz,has_row
 ret
shield_colors_ready: db 0x44,0x44,0x44,0x44,0x44,0x44
shield_colors_active: db 0x45,0x45,0x45,0x45,0x45,0x45
shield_colors_charge: db 0x42,0x42,0x46,0x46,0x44,0x44

; hud_buf[0..5] = cifras del record: 0, millares, centenas, decenas, unidades, 0.
record_digits:
 ld hl,(score_words)
 push hl
 ld hl,(record_words)
 ld (score_words),hl
 call score_to_digits
 pop hl
 ld (score_words),hl
 ld hl,score_digits
 ld de,hud_buf+1
 ld bc,4
 ldir
 xor a
 ld (hud_buf),a
 ld (hud_buf+5),a
 ret

; A = linea, C = primera columna: 6 cifras de hud_buf con la fuente de 5x7.
digits6_draw:
 ld hl,hud_buf
 ld b,6
; A = linea, C = columna, B = numero de cifras, HL = cifras.
digits_n_draw:
 ld (hud_tmp),a
digits6_loop:
 push bc
 push hl
 ld l,(hl)
 ld h,0
 ld d,h
 ld e,l
 add hl,hl
 add hl,hl
 add hl,hl
 or a
 sbc hl,de                  ; cifra*7
 ld de,digit_bitmaps
 add hl,de
 ld a,1
 ld (hp_stride),a
 ld b,7
 ld a,(hud_tmp)
 call hud_put
 pop hl
 inc hl
 pop bc
 inc c
 djnz digits6_loop
 ret

new_record equ 0xf04e
record_start equ 0xf062
; hud_buf[0..5] = cifras de los puntos (0, 4 cifras, 0).
score_digits6:
 call score_to_digits
 ld hl,score_digits
 ld de,hud_buf+1
 ld bc,4
 ldir
 xor a
 ld (hud_buf),a
 ld (hud_buf+5),a
 ret

; VIDAS: tres caras; con la ultima vida la que queda pone cara apurada; las
; perdidas son un circulo azul punteado.
lives_hud_present:
 ld a,(player_lives)
 ld b,a
 ld a,(lives_displayed)
 cp b
 ret z
 ld a,b
 ld (lives_displayed),a
 xor a
 ld (face_k),a
lives_face_loop:
 ld a,(face_k)
 ld b,a
 ld a,(player_lives)
 ld hl,hud_face_vacia
 ld c,0x01
 cp b
 jr z,lives_face_ready
 jr c,lives_face_ready
 ld c,0x46
 ld hl,hud_face_feliz
 cp 1
 jr nz,lives_face_ready
 ld hl,hud_face_apurado
lives_face_ready:
 ld a,c
 ld (hud_tmp),a
 ld a,2
 ld (hp_stride),a
 ld a,(face_k)
 add a,a
 add a,25
 ld c,a
 push hl
 ld b,13
 ld a,42
 call hud_put
 pop hl
 inc hl
 inc c
 ld b,13
 ld a,42
 call hud_put
 ld a,(face_k)
 add a,a
 add a,25
 ld l,a
 ld h,0
 ld de,0x5800+5*32
 add hl,de
 ld a,(hud_tmp)
 ld (hl),a
 inc hl
 ld (hl),a
 ld de,31
 add hl,de
 ld (hl),a
 inc hl
 ld (hl),a
 ld a,(face_k)
 inc a
 ld (face_k),a
 cp 3
 jr nz,lives_face_loop
 jp hud_attr_sync



; V1.2: genera en $5B00..$5F7F las 8 fases desplazadas de los 3 tiempos de la
; explosion (16x16 -> 3 bytes x 16 filas). La memoria de $5B00 (buffer de
; impresora y variables del BASIC) no se usa una vez arrancado el juego.
explosion_shift_init:
 ld hl,explosion_src
 ld de,0x5b00
 ld c,3
esi_frame:
 push bc
 ld b,16
esi_phase0:
 ld a,(hl)
 ld (de),a
 inc hl
 inc de
 ld a,(hl)
 ld (de),a
 inc hl
 inc de
 xor a
 ld (de),a
 inc de
 djnz esi_phase0
 ld c,7
esi_phase:
 push hl
 ld a,e
 sub 48
 ld l,a
 ld a,d
 jr nc,esi_prev
 dec a
esi_prev:
 ld h,a                     ; HL = fase anterior (DE-48)
 ld b,16
esi_row:
 or a
 ld a,(hl)
 rra
 ld (de),a
 inc hl
 inc de
 ld a,(hl)
 rra
 ld (de),a
 inc hl
 inc de
 ld a,(hl)
 rra
 ld (de),a
 inc hl
 inc de
 djnz esi_row
 pop hl
 dec c
 jr nz,esi_phase
 pop bc
 dec c
 jr nz,esi_frame
 ret
