; Shadow framebuffer is fixed at 0x6000..0x7AFF and stack 0x7FF0.
; Dirty flags correspond to 32x24 Spectrum cells, not per pixel.
full_redraw: db 0
dirty_count: db 0
blit_src: dw 0
blit_attr: db 7
blit_x: db 0
blit_y: db 0
mask_src: dw 0
paint_attr: db 7
text_attr: db 0x47
map_data: ds 768
dirty_flags: ds 768
dirty_pairs: ds 480
move_dx: db 0
move_dy: db 0
fire_down: db 0
