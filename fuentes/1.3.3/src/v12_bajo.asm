; HALCONES ESTELARES 1.2 - MOAI CON DANO, BOCA, DERRUMBE Y LUNA (memoria baja).
; Todo esto corre solo durante el MOAI, la escena mas ligera del juego.

; Al empezar el MOAI.
boss_v12_start:
 xor a
 ld (boss_blocks),a
 ld (mouth_ticks),a
 ld (moon_x),a
 ld (moon_clock),a
 ret

; B = x, C = y: borra ese pixel en pantalla, imagen de trabajo y cielo.
boss_pixel_clear:
 ld l,c
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,b
 rrca
 rrca
 rrca
 and 31
 add a,e
 ld e,a
 ld a,b
 and 7
 ld l,a
 ld h,0
 push de
 ld de,bitmask_table
 add hl,de
 ld a,(hl)
 cpl
 ld c,a
 pop hl
 and (hl)
 ld (hl),a                 ; pantalla
 ld a,h
 add a,0x80
 ld h,a
 ld a,c
 and (hl)
 ld (hl),a                 ; trabajo C000
 ld a,h
 add a,0x18
 ld h,a
 ld a,c
 and (hl)
 ld (hl),a                 ; cielo D800
 ret

; A = vida que le queda al MOAI: grietas nuevas al bajar a 12, 6 y 3.
boss_damage_check:
 ld b,0
 cp 12
 jr z,boss_crack
 inc b
 cp 6
 jr z,boss_crack
 inc b
 cp 3
 ret nz
; B = etapa 0..2: grieta de 2 px de ancho que baja serpenteando.
boss_crack:
 ld a,b
 add a,a
 add a,b
 ld e,a
 ld d,0
 ld hl,crack_starts
 add hl,de
 ld a,(hl)
 ld (crack_x),a
 inc hl
 ld a,(hl)
 ld (crack_y),a
 inc hl
 ld a,(hl)
 ld (crack_len),a
 ld a,(frame_index)
 ld (crack_seed),a
bc_loop:
 ld a,(crack_x)
 ld b,a
 ld a,(crack_y)
 ld c,a
 call boss_pixel_clear
 ld a,(crack_x)
 inc a
 ld b,a
 ld a,(crack_y)
 ld c,a
 call boss_pixel_clear
 ld a,(crack_seed)
 ld b,a
 add a,a
 add a,a
 add a,b
 add a,17
 ld (crack_seed),a
 rlca
 rlca
 and 3                     ; 0 izquierda, 1-2 recto, 3 derecha
 ld hl,crack_x
 or a
 jr nz,bc_right
 dec (hl)
 jr bc_down
bc_right:
 cp 3
 jr nz,bc_down
 inc (hl)
bc_down:
 ld hl,crack_y
 inc (hl)
 ld hl,crack_len
 dec (hl)
 jr nz,bc_loop
 ret
crack_starts: db 98,9,24, 84,38,30, 106,44,34

; El MOAI dispara: la boca se abre (franja negra) unos ticks.
mouth_open:
 ld a,8
 ld (mouth_ticks),a
 xor a
 jr mouth_set
mouth_close:
 ld a,1
mouth_set:
 ld (mouth_mode),a
 ld c,65
ms_row:
 push bc
 ld l,c
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,e
 add a,11
 ld e,a                    ; DE = pantalla (x=88)
 ld b,2
ms_col:
 ld a,(mouth_mode)
 or a
 jr z,ms_put               ; abrir: 0
 ld a,d
 add a,0x98
 ld h,a
 ld l,e
 ld a,(hl)                 ; cerrar: lo que hay en el cielo
ms_put:
 ld (de),a
 ld l,a
 ld a,d
 add a,0x80
 ld h,a
 ld a,l
 ld l,e
 ld (hl),a                 ; misma copia en la imagen de trabajo
 inc e
 djnz ms_col
 pop bc
 inc c
 ld a,c
 cp 68
 jr nz,ms_row
 ret

; Cada tick con el MOAI vivo: boca y luna.
boss_alive_tick:
 ld a,(mouth_ticks)
 or a
 jr z,moon_tick
 dec a
 ld (mouth_ticks),a
 call z,mouth_close
; La luna cruza por delante de Jupiter, 1 px cada 8 ticks.
moon_tick:
 ld a,(moon_clock)
 inc a
 and 7
 ld (moon_clock),a
 ret nz
 call moon_erase
 ld a,(moon_x)
 or a
 jr nz,moon_next
 ld a,23                   ; primera vez: entra por la izquierda (x=24)
moon_next:
 inc a
 cp 184
 jr c,moon_store
 ld a,24
moon_store:
 ld (moon_x),a
 call moon_draw
 jp moon_sync

; Quita la luna del cielo y repone esas filas de Jupiter.
moon_erase:
 ld a,(moon_x)
 or a
 ret z
 ld c,moon_y
me_row:
 push bc
 call moon_row_addr        ; HL = cielo (D800) en la columna de la luna
 xor a
 ld (hl),a
 inc hl
 ld (hl),a
 ; fila de Jupiter (7 bytes en x=128) desde los datos del planeta
 ld a,c
 sub 96
 ld l,a
 ld h,0
 ld d,h
 ld e,l
 add hl,hl
 add hl,hl
 add hl,hl
 or a
 sbc hl,de                 ; (y-96)*7
 ld de,0xf611
 add hl,de
 push hl
 ld l,c
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,e
 add a,16
 ld e,a
 ld a,d
 add a,0x98
 ld d,a
 pop hl
 ld bc,7
 ldir
 pop bc
 inc c
 ld a,c
 cp moon_y+7
 jr nz,me_row
 ret

; C = y -> HL = byte del cielo (D800) donde empieza la luna.
moon_row_addr:
 ld l,c
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,(moon_x)
 rrca
 rrca
 rrca
 and 31
 add a,e
 ld l,a
 ld a,d
 add a,0x98
 ld h,a
 ret

; Dibuja la luna (disco de 7 px con crateres) tapando lo que haya detras.
moon_draw:
 ld c,moon_y
 ld ix,moon_art
md_row:
 push bc
 call moon_row_addr
 ld d,(ix+0)               ; disco (mascara)
 ld e,0
 ld b,(ix+7)               ; dibujo
 ld c,0
 ld a,(moon_x)
 and 7
 jr z,md_shifted
md_shift:
 push af
 ld a,d
 or a
 rra
 ld d,a
 ld a,e
 rra
 ld e,a
 ld a,b
 or a
 rra
 ld b,a
 ld a,c
 rra
 ld c,a
 pop af
 dec a
 jr nz,md_shift
md_shifted:
 ld a,d
 cpl
 and (hl)
 or b
 ld (hl),a
 inc hl
 ld a,e
 cpl
 and (hl)
 or c
 ld (hl),a
 inc ix
 pop bc
 inc c
 ld a,c
 cp moon_y+7
 jr nz,md_row
 ret
moon_art:
 db 0x38,0x7c,0xfe,0xfe,0xfe,0x7c,0x38   ; disco
 db 0x38,0x5c,0xee,0xfa,0xbe,0x74,0x38   ; luna con crateres

; Lleva las 7 filas de la luna del cielo a la imagen de trabajo y a la pantalla
; (columnas 2..23). Los sprites que pasen por ahi se repintan en el tick siguiente.
moon_sync:
 ld c,moon_y
msy_row:
 push bc
 ld l,c
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc e
 inc e                     ; columna 2
 ld h,d
 ld l,e
 ld a,h
 add a,0x98
 ld h,a                    ; HL = cielo
 push de
 push hl
 ld a,d
 add a,0x80
 ld d,a                    ; DE = trabajo
 ld bc,22
 ldir
 pop hl
 pop de                    ; DE = pantalla
 ld bc,22
 ldir
 pop bc
 inc c
 ld a,c
 cp moon_y+7
 jr nz,msy_row
 ret

; Derrumbe del MOAI: 3 bloques de 8x8 por tick en orden salteado (66 bloques).
; Devuelve Z cuando ha terminado.
boss_blocks_tick:
 ld a,(boss_blocks)
 or a
 jr nz,bbt_go
 ld a,66
 ld (boss_blocks),a
 xor a
 ld (boss_bidx),a
 call moon_erase           ; la luna se va con el MOAI
 xor a
 ld (moon_x),a
bbt_go:
 call sfx_explode
 ld b,3
bbt_loop:
 push bc
 call boss_block_erase
 pop bc
 ld a,(boss_blocks)
 dec a
 ld (boss_blocks),a
 ret z
 djnz bbt_loop
 or 1                      ; NZ: quedan bloques
 ret

boss_block_erase:
 ld a,(boss_bidx)
 ld c,0
bbe_div:
 cp 6
 jr c,bbe_ok
 sub 6
 inc c
 jr bbe_div
bbe_ok:
 add a,9
 ld (blk_col),a
 ld a,c
 add a,a
 add a,a
 add a,a
 add a,8
 ld c,a                    ; primera linea del bloque
 ld b,8
bbe_row:
 push bc
 ld l,c
 ld h,0
 add hl,hl
 ld de,scanline_table
 add hl,de
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,(blk_col)
 add a,e
 ld e,a
 xor a
 ld (de),a                 ; pantalla
 ld a,d
 add a,0x80
 ld d,a
 xor a
 ld (de),a                 ; trabajo
 ld a,d
 add a,0x18
 ld d,a
 xor a
 ld (de),a                 ; cielo
 pop bc
 inc c
 djnz bbe_row
 ld a,(boss_bidx)
 add a,37
 cp 66
 jr c,bbe_store
 sub 66
bbe_store:
 ld (boss_bidx),a
 ret

; V1.3.3: los fondos lejanos de fase (V1.3) se han quitado: compartian celdas
; de color con cuervos, balas y explosiones. Quedan la luna y Jupiter del MOAI.

; V1.3 (sonido, desde tick_go; aqui en memoria baja: no es critico en tiempo)
; Al empezar cada tick: presupuesto = 3/4 del rato libre del tick anterior
; menos 200, entre 0 y 1400 (10 ms, siempre menos de un fotograma).
snd_budget_set:
 ld hl,(snd_idle)
 ld d,h
 ld e,l
 ld b,2
snd_budget_q:
 ld a,d                     ; DE = rato libre / 4
 or a
 rra
 ld d,a
 ld a,e
 rra
 ld e,a
 djnz snd_budget_q
 or a
 sbc hl,de                  ; HL = 3/4 del rato libre
 ld de,200                  ; margen por si el tick siguiente pesa mas
 sbc hl,de
 jr nc,snd_budget_pos
 ld hl,0
snd_budget_pos:
 ld de,1400                 ; tope: 36 400 T (10 ms), menos de un fotograma
 push hl
 sbc hl,de
 pop hl
 jr c,snd_budget_ok
 ex de,hl
snd_budget_ok:
 ld (snd_budget),hl
 ld hl,0
 ld (snd_idle),hl
 ld a,1
 ld (snd_mid_ok),a
 ret


; V1.3: LEDs del marco (antes en gameplay.asm; aqui hay sitio).
; Three left-rail signal LEDs, sequence top→middle→bottom→middle→top.
; Their original bitmap remains immutable: only native 8x8 INK attributes
; and private color shadow are changed. No sprite/compositor memory writes.
led_frame_tick:
 call badge_tick            ; V1.3: brillo de la insignia ESF del marcador.
 ; V1.2: los LEDs del marco informan. MOAI: los tres fijos en rojo. Enemigo
 ; bajando cerca de la nave: los tres parpadean rapido. Si no, el barrido de
 ; siempre: verde con el escudo listo, rojo mientras no lo esta.
 ld a,(wave_stage)
 cp 3
 ld a,0x42
 jr z,led_all
 call led_danger
 jr z,led_sweep
 ld a,(frame_index)
 and 2
 ld a,0x42
 jr nz,led_all
 ld a,0x02
led_all:
 ld b,a
 jr led_write
led_sweep:
 ld a,(led_anim_clock)
 inc a
 cp 8
 jp c,led_frame_clock_store
 xor a
 ld (led_anim_clock),a
 ld a,(led_anim_phase)
 inc a
 and 3
 ld (led_anim_phase),a
 jp led_frame_apply
led_frame_clock_store:
 ld (led_anim_clock),a
led_frame_apply:
 ld bc,0x0242               ; B = apagado, C = encendido (rojo)
 ld a,(shield_state)
 or a
 jr nz,led_colors_ok
 ld bc,0x0444               ; escudo listo: verde
led_colors_ok:
 call led_write             ; los tres apagados...
 ld a,(led_anim_phase)      ; ...y se enciende el que toca (0 arriba, 1/3 centro, 2 abajo)
 ld hl,0x58c0
 or a
 jr z,led_one
 ld hl,0x5a40
 cp 2
 jr z,led_one
 ld hl,0x5980
led_one:
 ld (hl),c
 ld a,h
 add a,0x99                 ; $58xx -> $F1xx (sombra privada)
 ld h,a
 ld (hl),c
 ret
led_write:                  ; B = atributo para las tres lamparas
 ld a,b
 ld (0x58c0),a
 ld (0x5980),a
 ld (0x5a40),a
 ld (0xf1c0),a
 ld (0xf280),a
 ld (0xf340),a
 ret
; NZ si algun enemigo vivo (no en explosion ni reagrupado) esta en y>=112.
led_danger:
 ld hl,enemy_slots+1
 ld a,(enemy_count)       ; V1.2: 10 con los cuervos, 6 en el resto
 ld b,a
led_danger_loop:
 ld a,(hl)
 cp 112
 jr c,led_danger_next
 inc hl
 ld a,(hl)
 dec hl
 or a
 jr z,led_danger_next
 cp 3
 jr z,led_danger_next
 cp 5
 ret nz
led_danger_next:
 ld de,6
 add hl,de
 djnz led_danger_loop
 xor a
 ret

; ---------------------------------------------------------------------------
; V1.3: BRILLO DE LA INSIGNIA ESF. La insignia (celdas 25..30 x 15..22, tinta
; blanca brillante) se cruza en diagonal con una franja cian-amarillo-cian, una
; diagonal por tick (16 ticks, 0,6 s). Solo cambian atributos (pantalla y
; sombra), nunca pixeles. Brilla sola cada 8 s y al empezar cada oleada, con
; la vida extra y cuando el escudo vuelve a estar listo (badge_shine).
badge_shine:
 ld a,1
 ld (badge_pos),a
 xor a
 ld (badge_timer),a
 ret

badge_tick:
 ld a,(badge_pos)
 or a
 jr nz,badge_step
 ld hl,badge_timer
 inc (hl)
 ld a,(hl)
 cp 200                     ; 8 s a 25 ticks/s
 ret c
 jr badge_shine
badge_step:
 ld hl,0x5800+15*32+25
 ld d,0                     ; D = fila de la insignia (0..7)
badge_row:
 ld e,0                     ; E = columna (0..5)
badge_col:
 ld a,d
 add a,e
 inc a
 ld c,a                     ; C = diagonal + 1
 ld a,(badge_pos)
 sub c                      ; 0 y 2: cian (bordes), 1: amarillo (centro)
 ld c,0x45
 jr z,badge_put
 dec a
 ld c,0x46
 jr z,badge_put
 dec a
 ld c,0x45
 jr z,badge_put
 ld c,0x47
badge_put:
 ld (hl),c
 ld a,h
 add a,0x99                 ; $58xx -> $F1xx (sombra privada)
 ld h,a
 ld (hl),c
 sub 0x99
 ld h,a
 inc hl
 inc e
 ld a,e
 cp 6
 jr nz,badge_col
 ld bc,26
 add hl,bc
 inc d
 ld a,d
 cp 8
 jr nz,badge_row
 ld hl,badge_pos
 inc (hl)
 ld a,(hl)
 cp 17                      ; en 16 ya esta toda blanca otra vez
 ret c
 ld (hl),0
 ret
