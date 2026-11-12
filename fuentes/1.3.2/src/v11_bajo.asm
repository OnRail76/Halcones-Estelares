; HALCONES ESTELARES 1.2 - bloque de codigo en memoria baja (vacio: la
; memoria baja se usa para graficos). build.py sigue admitiendo codigo aqui.

; Kempston solo si 256 lecturas seguidas tienen los bits 5..7 a cero y nunca
; izquierda+derecha a la vez (sin interfaz el bus flotante da $FF).
kempston_detect:
 xor a
 ld (kempston_ok),a
 ld (kempston_mode),a
 halt
 ld b,0
kd_loop:
 in a,(0x1f)
 ld c,a
 and 0xe0
 ret nz
 ld a,c
 and 3
 cp 3
 ret z
 djnz kd_loop
 ld a,1
 ld (kempston_ok),a
 ret

; Z = algun fuego pulsado (SPACE, 0 de Sinclair o Kempston si existe).
; Usado en titulo y GAME OVER. Destruye AF, BC.
any_fire_pressed:
 ld bc,0x7ffe
 in a,(c)
 and 1
 ret z
 ld b,0xef
 in a,(c)
 and 1
 ret z
 ld a,(kempston_ok)
 or a
 jr z,afp_none
 in a,(0x1f)
 and 0x10
 jr z,afp_none
 xor a
 ret
afp_none:
 or 1
 ret

; Al empezar: se juega con Kempston solo si se pulso SU fuego en el titulo.
title_choose_controls:
 xor a
 ld (kempston_mode),a
 ld a,(kempston_ok)
 or a
 ret z
 in a,(0x1f)
 and 0x10
 ret z
 ld a,1
 ld (kempston_mode),a
 ret





; TITULO: record de la sesion y estrellas que titilan.
title_record_draw:
 call record_digits
 ld a,153
 ld c,16
 jp digits6_draw
twk_i equ 0xf04c
twk_c equ 0xf04d
title_twinkle:
 ld a,(twk_c)
 add a,29
 ld (twk_c),a
 and 0x18
 rrca
 rrca
 rrca
 ld e,a
 ld d,0
 ld hl,twinkle_attrs
 add hl,de
 ld b,(hl)
 ld a,(twk_i)
 inc a
 cp title_star_count
 jr c,title_twinkle_store
 xor a
title_twinkle_store:
 ld (twk_i),a
 add a,a
 ld l,a
 ld h,0
 ld de,title_star_cells
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,b
 ld (de),a
 ret
twinkle_attrs: db 0x47,0x07,0x45,0x01


; FASE SUPERADA: puntos, vidas y record.
phase_stats_draw:
 call score_digits6
 ld a,136
 ld c,16
 call digits6_draw
 ld a,(player_lives)
 ld (hud_buf),a
 ld a,144
 ld c,8
 ld b,1
 ld hl,hud_buf
 call digits_n_draw
 call record_digits
 ld a,144
 ld c,17
 jp digits6_draw
; GAME OVER: record y, si se ha batido en esta partida, NUEVO RECORD.
gameover_record_draw:
 call record_digits
 ld a,161
 ld c,16
 call digits6_draw
 ld a,(new_record)
 or a
 ret z
 ld hl,0x5800+17*32
 ld b,32
gameover_record_attr:
 ld (hl),0xc6
 inc hl
 djnz gameover_record_attr
 ret
; Marca si los puntos de esta partida superan el record con que empezo.
record_check:
 xor a
 ld (new_record),a
 ld hl,(record_start)
 ld de,(score_words)
 or a
 sbc hl,de
 ret nc
 ld a,1
 ld (new_record),a
 ld hl,(score_words)       ; V1.3: el record se guarda tambien aqui, no solo
 ld (record_words),hl      ; al redibujar los puntos.
 ret

; FASE nn (cifras negras sobre la banda magenta), seis casillas de oleada y
; la cifra de OLEADA n.
hud_phase_draw:
 ld a,(phase_number)
 ld c,0
hud_phase_div:
 cp 10
 jr c,hud_phase_digits
 sub 10
 inc c
 jr hud_phase_div
hud_phase_digits:
 ld (hud_tmp),a
 ld a,c
 ld c,29
 ld e,90
 call hud_s5
 ld a,(hud_tmp)
 ld c,30
 ld e,90
 call hud_s5
 ld a,(card_wave)
 ld c,30
 ld e,107
 call hud_s5
 ld c,26
 xor a
 ld (face_k),a
hud_pip_col:
 ld a,(face_k)
 call pip_pattern
 ex de,hl
 ld hl,hud_buf
 ld b,5
hud_pip_left:
 ld a,(de)
 rlca
 rlca
 rlca
 rlca
 ld (hl),a
 inc de
 inc hl
 djnz hud_pip_left
 ld a,(face_k)
 inc a
 call pip_pattern
 ld de,hud_buf
 ld b,5
hud_pip_right:
 ld a,(de)
 or (hl)
 ld (de),a
 inc de
 inc hl
 djnz hud_pip_right
 ld a,1
 ld (hp_stride),a
 ld hl,hud_buf
 ld b,5
 ld a,99
 call hud_put
 ld a,(face_k)
 add a,2
 ld (face_k),a
 inc c
 ld a,c
 cp 29
 jr nz,hud_pip_col
 ret
; A = casilla 0..5 -> HL = dibujo (llena si es de una oleada ya empezada).
pip_pattern:
 ld b,a
 ld a,(card_wave)
 ld hl,pip_full
 cp b
 jr z,pip_hollow_sel
 ret nc
pip_hollow_sel:
 ld hl,pip_hollow
 ret
pip_full: db 14,14,14,14,14
pip_hollow: db 14,10,10,10,14
; A = cifra, C = columna, E = linea: cifra 5x5.
hud_s5:
 push de
 ld l,a
 ld h,0
 ld d,h
 ld e,l
 add hl,hl
 add hl,hl
 add hl,de
 ld de,hud_s5_digits
 add hl,de
 ld a,1
 ld (hp_stride),a
 pop de
 ld a,e
 ld b,5
 jp hud_put

; V1.2: color de los rombos de plasma enemigos en la sombra de atributos.
; Primero se devuelven a blanco las celdas magenta de las posiciones viejas y
; luego se pintan de magenta las nuevas, pero solo sobre celdas blancas: un
; enemigo o la nave conservan su color. Cerca de la nave (y>=136) no se pinta.
enemy_bullet_colors:
 ld ix,old_enemy_bullets
 ld de,0x4703               ; si es magenta oscuro (E) -> blanco (D)
 call ebc_list
 ld ix,enemy_bullet_slots
 ld de,0x0347               ; si es blanco -> magenta oscuro (no brillante:
                            ; distinto del MOAI, que es magenta brillante 0x43)
ebc_list:
 ld b,3
ebc_loop:
 push bc
 ld a,(ix+2)
 or a
 jr z,ebc_next
 ld a,(ix+1)
 cp 136
 jr c,ebc_paint
 ld a,e
 cp 0x47
 jr z,ebc_next             ; abajo solo se borra, no se pinta
ebc_paint:
 ld a,(ix+1)
 and 0xf8
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 ld a,(ix+0)
 rrca
 rrca
 rrca
 and 31
 ld c,a
 ld b,0
 add hl,bc
 ld bc,0xf100
 add hl,bc
 call ebc_cell
 inc hl
 call ebc_cell
 ld bc,31
 add hl,bc
 call ebc_cell
 inc hl
 call ebc_cell
ebc_next:
 ld bc,3
 add ix,bc
 pop bc
 djnz ebc_loop
 ret
ebc_cell:
 ld a,(hl)
 cp e
 ret nz
 ld (hl),d
 ret

