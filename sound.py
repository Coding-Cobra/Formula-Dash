from settings import *

class Sound:
    def __init__(self):
        
        self.car_fx = {
            'start_beep' : pygame.mixer.Sound(join('..','resourcess','sound','start_beep.wav')),
            'start' : pygame.mixer.Sound(join('..','resourcess','sound','start.wav')),
            'breaking' : pygame.mixer.Sound(join('..','resourcess','sound','breaking.wav')),
            'max' : pygame.mixer.Sound(join('..','resourcess','sound','max_velocity.wav')),
            'acelerate' : pygame.mixer.Sound(join('..','resourcess','sound','acelerate.wav'))
        }
