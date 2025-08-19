import pygame
from os.path import join

# settings.py
SERVER_IP = 'AUTO'   # or put '192.168.1.42' to hardcode
SERVER_PORT = 5555


def make_txt(txt, font, color):
    txt = font.render(txt, True, color)
    
    return txt