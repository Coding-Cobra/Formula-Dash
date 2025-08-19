from settings import *
from button import Button, InputBox
from pathlib import Path
import json
import math

def clamp(x, a, b):
    return max(a, min(b, x))

class Start:
    def __init__(self):
        self.display = pygame.display.get_surface()
        self.display_w = self.display.get_width()
        self.display_h = self.display.get_height()
        
        self.suit_img1 = self.load_img(join('..','resourcess','driver','suit1.png'),scale=0.8)
        self.suit_img2 = self.load_img(join('..','resourcess','driver','suit2.png'),scale=0.8)
        
        self.helmet_img1 = self.load_img(join('..','resourcess','driver','helmet1.png'),scale=0.8)
        self.helmet_img2 = self.load_img(join('..','resourcess','driver','helmet2.png'),scale=0.8)
        
        self.start_back = self.load_img(join('..','resourcess','background','start.png'),scale=2.1)
        self.custom_back = self.load_img(join('..','resourcess','background','customize.png'),scale=1)
        
        padding_left = 40
        slider_w = 120
        start_y = 40
        gap = 50
        
        self.selected_track = 1
        
        self.choose_tracks = False
        
        self.tracks_btns = []
        for i in range(1, sum(1 for child in Path(join('..','tracks')).iterdir() if child.is_dir())  + 1):
            img = pygame.image.load(join('..','tracks',f'track_{i}','map.png'))
            img_w = 150
            ratio = img.get_width() / img_w
            img = pygame.transform.scale(img, (img_w, img.get_height()/ratio))
            self.tracks_btns.append(Track_btn(img))
                
        self.track_start_x = 180
        self.track_start_y = 150
        self.track_spacing_x = 300
        self.track_spacing_y = 200
        self.track_per_row = 4
        
        self.customize = False
        
        self.font = pygame.font.Font(join('..','resourcess', 'font', 'Formula1-Bold-4.ttf'), 15)
        
        self.start_data = self.load_data()
        
        self.suit_sliders = [
            Slider(padding_left, start_y + 0 * gap, slider_w, "Red", initial=self.start_data['suit_color'][0]),
            Slider(padding_left, start_y + 1 * gap, slider_w, "Green", initial=self.start_data['suit_color'][1]),
            Slider(padding_left, start_y + 2 * gap, slider_w, "Blue", initial=self.start_data['suit_color'][2])]
        
        self.helmet_sliders = [
            Slider(self.display_w - padding_left - slider_w, start_y + 0 * gap, slider_w, "Red", initial=self.start_data['helmet_color'][0], fliped=True),
            Slider(self.display_w - padding_left - slider_w, start_y + 1 * gap, slider_w, "Green", initial=self.start_data['helmet_color'][1] , fliped=True),
            Slider(self.display_w - padding_left - slider_w, start_y + 2 * gap, slider_w, "Blue", initial=self.start_data['helmet_color'][2], fliped=True)]
        
        
        self.contu = False
        
        self.play_btn = Button(0.5, '< PLAY >', 18, 'white', 'normal', 'hover','pressed')
        self.costom_back_btn = Button(0.4, '< BACK >', 13, 'white', 'normal', 'hover','pressed')
        self.to_costom_btn = Button(0.4, '< CUSTOMIZE >', 12, 'white', 'normal', 'hover','pressed')
        self.to_track_btn = Button(0.4, '< TRACKS >', 12, 'white', 'normal', 'hover','pressed')
        
        self.name_i_box = InputBox(self.font)
        self.name_i_box.input_box_text = self.start_data['name']
        self.name = ''
        
        self.suit_color = (self.start_data['suit_color'][0],self.start_data['suit_color'][1],self.start_data['suit_color'][2])
        self.helmet_color = (self.start_data['helmet_color'][0],self.start_data['helmet_color'][1],self.start_data['helmet_color'][2])
        
    def load_img(self, path,scale=1):
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.scale(img, (img.get_width()*scale, img.get_height()*scale))
        return img
    
    def load_data(self):
        path = join('..', 'data', 'saves.json')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def save_data(self):
        data = {"name" : self.name_i_box.input_box_text, "suit_color":self.suit_color, "helmet_color":self.helmet_color,}
        path = join('..', 'data', 'saves.json')
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def input(self):
        keys = pygame.key.get_pressed()
        
    def costomize(self):
        r_suit, g_suit, b_suit = [s.value for s in self.suit_sliders]
        r_helmet, g_helmet, b_helmet = [s.value for s in self.helmet_sliders]
        
        self.suit_color = (r_suit, g_suit, b_suit)
        self.helmet_color = (r_helmet, g_helmet, b_helmet)

        # call input poll for each slider
        for s in self.suit_sliders:
            s.handle_input()
            
        for s in self.helmet_sliders:
            s.handle_input()

        # tint suit_img1 by multiplying with colour
        colored_suit = self.suit_img1.copy()
        colored_suit.fill((r_suit, g_suit, b_suit, 255), special_flags=pygame.BLEND_MULT)
        colored_helmet = self.helmet_img1.copy()
        colored_helmet.fill((r_helmet, g_helmet, b_helmet, 255), special_flags=pygame.BLEND_MULT)

        self.racer_surf = pygame.Surface(self.suit_img1.get_size(), pygame.SRCALPHA)
        self.racer_surf.blit(colored_suit, (0, 0))
        self.racer_surf.blit(self.suit_img2, (0, 0))
        
        self.racer_surf.blit(colored_helmet, (0, 0))
        self.racer_surf.blit(self.helmet_img2, (0, 0))

        self.display.blit(self.racer_surf,
                        (self.display_w/2 - self.racer_surf.get_width()/2, 160))

        for s in self.suit_sliders:
            s.draw(self.display)
        for s in self.helmet_sliders:
            s.draw(self.display)

    def update(self):
        if self.customize:
            self.display.blit(self.custom_back, (0,0))
            self.costomize()
            
            if self.costom_back_btn.draw(self.display, self.display_w/2, self.display_h - 50):
                self.customize = False
        else:
            self.display.blit(self.start_back, (0,0))
            if not self.choose_tracks:
                self.name = self.name_i_box.input_box_text
                self.name_i_box.draw(self.display, self.display_w/2, self.display_h - 50)
                if self.play_btn.draw(self.display, self.display_w/2, self.display_h - 250):
                    if not self.name_i_box.input_box_text in ['Click to type in a name', '', ' ']:
                        self.save_data()
                        self.contu = True
            
                if self.to_costom_btn.draw(self.display, self.display_w/2, self.display_h - 100):
                    self.customize = True
                    
                if self.to_track_btn.draw(self.display, self.display_w/2, self.display_h - 175):
                    self.choose_tracks = True
                    
            else:
                if self.costom_back_btn.draw(self.display, self.display_w/2, self.display_h - 100):
                    self.choose_tracks = False
            
                for i, btn in enumerate(self.tracks_btns):
                    col = i % self.track_per_row
                    row = i // self.track_per_row
                    x = self.track_start_x + col * self.track_spacing_x
                    y = self.track_start_y + row * self.track_spacing_y

                    color = (10, 10, 10)
                    if i + 1 == self.selected_track:
                        color = (225, 215, 0)

                    if btn.draw(self.display, x, y, color):
                        self.selected_track = (i + 1)
        
class Track_btn:
    def __init__(self, image):
        self.image = image
        self.rect = self.image.get_frect()
        self.clicked = False
        
        self.normal_color = (50, 50, 50)
        self.hover_color = (75, 75, 75)
        self.click_color = (25, 25, 25)
        
        self.color = self.normal_color
        
        #self.play_sound = play_sound

    def draw(self, surface, x, y, border_color):
        self.rect.center = (x, y)
        action = False

        #get mouse position
        pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # True while button is held

        if self.rect.collidepoint(pos):
            if mouse_pressed and not self.clicked:
                self.clicked = True
                self.color = self.click_color
            elif not mouse_pressed and self.clicked:
                self.clicked = False
                action = True
                self.color = self.hover_color
            elif self.clicked:
                self.color = self.click_color
            else:
                self.color = self.hover_color
        else:
            self.color = self.normal_color
            if not mouse_pressed:
                self.clicked = False

        # draw button
        pygame.draw.rect(surface, border_color, self.rect.inflate(20,30), border_radius=3)
        pygame.draw.rect(surface, self.color, self.rect.inflate(10,20), border_radius=3)
        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action
    
class Slider:
    """Horizontal slider mapping a position to 0..255."""

    def __init__(self, x, y, w, label, initial=0, fliped=False):
        self.display = pygame.display.get_surface()
        self.rect = pygame.Rect(x, y, w, 20)  # bar rectangle
        self.handle_radius = 10
        self.label = label
        self.value = clamp(int(initial), 0, 255)
        self.dragging = False
        self.font = pygame.font.Font(join('..','resourcess','font','Formula1-Bold-4.ttf'), 14)
        self.fliped = fliped

    def handle_x(self):
        # map value (0..255) -> x on the slider bar
        return int(self.rect.x + (self.value / 255) * self.rect.w)

    def draw(self, surf):
        # bar background
        pygame.draw.rect(surf, 'black', self.rect, border_radius=6)
        # colored fill for visual feedback
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, int((self.value / 255) * self.rect.w), self.rect.h)
        pygame.draw.rect(surf, pygame.Color(self.label.lower()), fill_rect, border_radius=6)

        # handle
        hx = self.handle_x()
        hy = self.rect.centery
        pygame.draw.circle(surf, pygame.Color("white"), (hx, hy), self.handle_radius + 2)  # border
        pygame.draw.circle(surf, pygame.Color(self.label.lower()), (hx, hy), self.handle_radius)

        # text label and numeric value
        lbl = self.font.render(f"{self.label}: {self.value}", True, 'black')
        if not self.fliped:
            surf.blit(lbl, (self.rect.right + 12, self.rect.y - 2))
        else:
            surf.blit(lbl, (self.rect.left - 12 - self.rect.width, self.rect.y - 2))

    def set_by_pos(self, px):
        # px is mouse x: map it to value 0..255
        rel = (px - self.rect.x) / float(self.rect.w)
        self.value = clamp(int(round(rel * 255)), 0, 255)

    def handle_input(self):
        """Call once per frame (no event parameter)."""
        mouse_down = pygame.mouse.get_pressed()[0]  # left button
        mx, my = pygame.mouse.get_pos()

        handle_rect = pygame.Rect(self.handle_x() - 12, self.rect.centery - 12, 24, 24)

        # If mouse just pressed inside handle/bar, begin dragging
        if mouse_down and (handle_rect.collidepoint(mx, my) or self.rect.collidepoint(mx, my)):
            self.dragging = True
            self.set_by_pos(mx)
            return True

        # If mouse is held and we're already dragging, update value
        if mouse_down and self.dragging:
            self.set_by_pos(mx)
            return True

        # Mouse released -> stop dragging
        if not mouse_down and self.dragging:
            self.dragging = False

        return False