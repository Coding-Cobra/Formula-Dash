from settings import *
from race import Race
from start import Start
from sound import Sound

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption('Real Racing')
        self.clock = pygame.time.Clock()
        
        self.sound = Sound()
        self.start_menu = Start()
        self.race_init = False
        
        self.running = True
        
        self.avarage = 0
        self.icount = 0
        
    def run(self):
        while self.running:
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
                if not self.start_menu.contu: self.start_menu.name_i_box.handle_event(event)
            
            dt = self.clock.tick() / 1000
            
            self.screen.fill('green')
            if not self.start_menu.contu: 
                self.start_menu.update()
            
            if self.start_menu.contu:   
                if not self.race_init:
                    self.race = Race(self.sound, self.start_menu.selected_track, self.start_menu.suit_color, 
                                     self.start_menu.helmet_color, self.start_menu.name)
                    self.race_init = True
                    
                if self.race.main_menu:
                    self.race_init = False
                    self.start_menu.contu = False
                    self.race.main_menu = False
                self.race.update(dt)
            self.avarage += dt
            self.icount += 1
            pygame.display.update()
            
        if self.start_menu.contu:
            if self.race.debug_track:
                self.race.track_pos += ']'
                print(self.race.track_pos)

        pygame.quit() 

if __name__ == '__main__':
    game = Game()
    game.run()
