; HALCONES ESTELARES 1.2 - datos del bloque de extras ($F401..$FDF9), tras el
; MOAI, Jupiter y el GAME OVER. Solo datos (lo ensambla build.py aparte).
; Semiperiodos (iteraciones de 26 T): C4 D4 Eb4 E4 F4 G4 Ab4 A4 Bb4 C5 D5 Eb5 E5 F5 G5 Ab5 Bb5 C6
note_hp: dw 253,225,212,200,189,168,158,149,141,125,111,104,98,93,82,77,68,60
; notas: 1 C4 2 D4 3 Eb4 4 E4 5 F4 6 G4 7 Ab4 8 A4 9 Bb4 10 C5 11 D5 12 Eb5
;        13 E5 14 F5 15 G5 16 Ab5 17 Bb5 18 C6
tune_title:
 db 6,8, 10,8, 11,8, 12,16, 11,8, 10,8, 6,16, 7,8, 9,8, 10,16, 9,8, 7,8, 6,24, 0,8
 db 6,8, 10,8, 11,8, 12,16, 14,8, 15,16, 14,8, 12,8, 11,16, 9,8, 10,32, 0,24
 db 255
tune_victory:
 db 10,6, 13,6, 15,6, 18,18, 15,6, 18,30, 0,10, 255
tune_gameover:
 db 6,16, 5,16, 3,16, 2,16, 1,48, 255
tune_record:
 db 10,8, 13,8, 15,8, 18,8, 15,8, 18,24, 0,8, 15,6, 18,30, 255
