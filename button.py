from settings import *

def import_image(*path, alpha = True, format = 'png', size = 1):
	full_path = join(*path) + f'.{format}'
	surf = pygame.image.load(full_path).convert_alpha() if alpha else pygame.image.load(full_path).convert()
	surf = pygame.transform.scale(surf, (surf.get_width()*size, surf.get_height()*size))
	return surf

class Button():
    def __init__(self, scale, txt, txt_size, txt_color, normal_img, hover_img, pressed_img):
        
        self.normal_img = import_image('..', 'resourcess', 'ui', 'buttons', normal_img, size=scale)    
        self.hover_img = import_image('..', 'resourcess', 'ui', 'buttons', hover_img, size=scale)
        self.pressed_image = import_image('..', 'resourcess', 'ui', 'buttons', pressed_img, size=scale)

        self.image = self.normal_img
        self.rect = self.normal_img.get_frect()
        self.clicked = False
        
        # text
        self.font = pygame.font.Font(join('..','resourcess', 'font', 'Formula1-Bold-4.ttf'), txt_size)
        self.txt = txt
        self.txt_color = txt_color
        self.txt_surf = self.font.render(str(self.txt), False, txt_color)
        
        if self.txt_surf.get_width() > self.normal_img.get_width():
            pygame.transform.scale(self.normal_img, (self.txt_surf.get_width() + 10, self.normal_img.get_width()))
            pygame.transform.scale(self.hover_img, (self.txt_surf.get_width() + 10, self.hover_img.get_width()))
            pygame.transform.scale(self.pressed_image, (self.txt_surf.get_width() + 10, self.pressed_image.get_width()))
        
        #self.play_sound = play_sound

    def draw(self, surface, x, y, change_txt = False):
        self.rect.center = (x, y)
        action = False

        if change_txt:
            self.txt_surf = self.font.render(str(self.txt), False, self.txt_color)    

        #get mouse position
        pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]  # True while button is held

        if self.rect.collidepoint(pos):
            if mouse_pressed and not self.clicked:
                self.clicked = True
                self.image = self.pressed_image
            elif not mouse_pressed and self.clicked:
                self.clicked = False
                action = True
                self.image = self.hover_img
            elif self.clicked:
                self.image = self.pressed_image
            else:
                self.image = self.hover_img
        else:
            self.image = self.normal_img
            if not mouse_pressed:
                self.clicked = False

        # draw button
        surface.blit(self.image, (self.rect.x, self.rect.y))
        surface.blit(self.txt_surf, (self.rect.centerx - self.txt_surf.get_width()/2, self.rect.centery - self.txt_surf.get_height()/1.9))
    
        return action
    
class InputBox():
    def __init__(self, font):
        self.input_box_width = 140
        self.input_box = pygame.FRect(650 /2 - 50, 400, self.input_box_width, 32)
        self.input_color_inactive = pygame.Color('#313131')
        self.input_color_active = pygame.Color('#3e3e3e')
        self.input_box_text = 'Click to type in a name'
        self.input_active = False
        self.font = font   
        self.Enter = False
        
    def handle_event(self, event):
        self.Enter = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.input_box.collidepoint(event.pos):
                self.input_box_text = ''
                self.input_active = True
            else:
                self.input_active = False

        elif event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_BACKSPACE:
                self.input_box_text = self.input_box_text[:-1]
            elif event.key == pygame.K_RETURN:
                if not self.input_box_text in ['Click to type in a name', '', ' ']:
                    self.Enter = True
            elif len(self.input_box_text) < 30:
                self.input_box_text += (event.unicode).upper()
    def draw(self, surf, x, y):
        # Recalculate box position and width
        self.input_box = pygame.FRect(x - (self.input_box.w // 2), y, self.input_box_width, 32)
        text_surface = self.font.render(self.input_box_text, True, '#1d1d1d')
        self.input_box.w = max(100, text_surface.get_width() + 10)
        self.input_box_width = self.input_box.w
        
        color = self.input_color_active if self.input_active else self.input_color_inactive
        pygame.draw.rect(surf, color, self.input_box.inflate(8,8), border_radius=20)
        pygame.draw.rect(surf, 'white', self.input_box, border_radius=20)
        surf.blit(text_surface, (self.input_box.left + self.input_box_width/2 - text_surface.get_width()/2, 
                                 self.input_box.y + self.input_box.height/2 - text_surface.get_height()//2))
        
        if self.Enter:
            self.input_active = False
        
        return self.Enter