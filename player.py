import pygame
from settings import *
import math

import json

class Player:
    def __init__(self, id):
        self.pos =(0,0)
        self.id = id
        self.body_image = None
        self.wheels_image = None
        self.car_surf = None
        self.image = None
        
    def create(self, track_data, sound, track_num):
        self.name = ''
        self.color = 'black'
        self.helmet_color = (0, 200, 0)
        self.inf_laps = False
        self.active = False
        self.race_completed = False
        self.ready = False
        if self.inf_laps: self.can_move = True
        else: self.can_move = False
        self.last_checkpoint = 0
        self.check_distance = 0
        self.prev_check_distance = 0
        self.start_line = track_data['start_line']
        self.track_record = track_data['lap_record']
        self.check_points = track_data['checks']
        self.track_data = track_data
        self.track_num = track_num
        self.lap = []
        
        self.true_lap = True
        
        self.ceck_times = [[],[]]
        for i in range(0,2):
            for j in range(1, len(self.check_points)):
                self.ceck_times[i].append(0)
                
        self.ceck_times_reset = False
        
        self.total_lap = track_data['laps']
        self.current_lap = 1
        
        self.track_position = 1
        
        self.og_pos = track_data['start'][self.id-1][0]
        self.pos = pygame.Vector2(self.og_pos)
        self.prev_pos = self.pos.copy()
        self.angle = track_data['start'][self.id-1][1] # -35
        self.og_angle = self.angle

        # Tuned physics
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = 4  # lerp strength per second
        self.acceleration_time = 0.1
        self.friction = 0.001   # low friction (F1 cars have high grip)
        self.og_brake_strenght = 2.5
        self.brake_strength = self.og_brake_strenght
        self.rotation_speed = 330  # max rotation at zero speed
        self.max_speed = 1050  # fast like F1
        self.drift_correction = 0.2  # allow some slip for realism
        
        self.correct_lap = []
        for i in range(1,len(self.check_points)):
            self.correct_lap.append(i)
        self.correct_lap.append(0)
        
        self.start_lap_time = pygame.time.get_ticks()
        self.fastes_lap = 999999.999999
        
        self.prev_lap_time = None
        self.time_lap_displayed = pygame.time.get_ticks()
                
        self.og_angle = self.angle
        self.display = pygame.display.get_surface()
        self.og_body_image = self.car_image_load('..','resourcess','car','body.png')
        self.body_image = self.og_body_image.copy()
        self.body_image.fill(self.color, special_flags=pygame.BLEND_RGB_MULT)
        
        self.wheels_image = self.car_image_load('..','resourcess','car','wheels.png')
        self.left_wheels_image = self.car_image_load('..','resourcess','car','wheels_left.png')
        self.right_wheels_image = self.car_image_load('..','resourcess','car','wheels_right.png')
        
        self.car_surf = pygame.Surface(self.body_image.get_size(), pygame.SRCALPHA)
        self.car_surf.blit(self.wheels_image, (0,0))
        self.car_surf.blit(self.body_image, (0,0))
        
        self.helmet1_og_image = self.car_image_load('..','resourcess','car','helmet1.png')
        self.helmet1_image = self.helmet1_og_image.copy()
        self.helmet2_image = self.car_image_load('..','resourcess','car','helmet2.png')

        self.car_surf.blit(self.helmet1_image, (0,0))
        self.car_surf.blit(self.helmet2_image, (0,0))
        
        self.image = self.car_surf
        
        self.rect = self.car_surf.get_frect(center=self.pos)
        
        self.start_font = pygame.font.Font(join('..','resourcess','font','Formula1-Regular-1.ttf'), 90)
        self.pos_font = pygame.font.Font(join('..','resourcess','font','Formula1-Regular-1.ttf'), 40)
        self.time_font = pygame.font.Font(join('..','resourcess','font','Formula1-Regular-1.ttf'), 30)
        self.lap_time_font = pygame.font.Font(join('..','resourcess','font','Formula1-Regular-1.ttf'), 20)
        self.record_time_font = pygame.font.Font(join('..','resourcess','font','Formula1-Black.ttf'), 20)
        
        self.import_light()
        self.start_start_timer = False
        self.start_beep_played = [False, False, False, False, False, False]
        self.quali = True
        self.start_time = pygame.time.get_ticks()
        
        self.sound = sound
        self.acs_sound = None
        
        self.time_to_prev_point = 1000
        self.time_to_nxt_point = 1000
        
        
    def draw_helmet(self):
        self.car_surf.blit(self.helmet1_image, (self.car_surf.get_width()/2 - self.helmet1_image.get_width()/1.8, 
                                                self.car_surf.get_height()/2 - self.helmet1_image.get_height()/1.9))
        
        self.car_surf.blit(self.helmet2_image, (self.car_surf.get_width()/2 - self.helmet2_image.get_width()/1.8, 
                                                self.car_surf.get_height()/2 - self.helmet2_image.get_height()/1.9))
        
    def recolor_player(self):
        self.body_image = self.og_body_image.copy()
        self.body_image.fill(self.color, special_flags=pygame.BLEND_RGB_MULT)
        
        self.helmet1_image = self.helmet1_og_image.copy()
        self.helmet1_image.fill(self.helmet_color, special_flags=pygame.BLEND_RGB_MULT)
        
        self.car_surf = pygame.Surface(self.body_image.get_size(), pygame.SRCALPHA)
        self.car_surf.blit(self.wheels_image, (0,0))
        self.car_surf.blit(self.body_image, (0,0))
        
        self.draw_helmet()
               
    def import_light(self):
        self.starting_lights = []
        for i in range(0,6):
            image = pygame.image.load(join('..','resourcess','start_light',f'{i}.png')).convert_alpha()
            image = pygame.transform.scale(image, (image.get_width()//3.8,image.get_height()//3.8))
            self.starting_lights.append(image)
            

        self.light_image = self.starting_lights[5]
        
    def lines_intersect(self, p1, p2, q1, q2):
        """Check if two line segments p1→p2 and q1→q2 intersect."""
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
        return ccw(p1, q1, q2) != ccw(p2, q1, q2) and ccw(p1, p2, q1) != ccw(p1, p2, q2)

    def past_points(self, camera_x, camera_y):
        old_pos = (self.prev_pos.x, self.prev_pos.y)
        new_pos = (self.pos.x, self.pos.y)

        for i, checkpoint in enumerate(self.check_points):
            cp_start = (checkpoint[0][0], checkpoint[0][1])
            cp_end   = (checkpoint[1][0], checkpoint[1][1])

            if self.lines_intersect(old_pos, new_pos, cp_start, cp_end):
                self.last_checkpoint = i
                if i not in self.lap:
                    self.lap.append(i)
                    self.check_lap()
                    if self.last_checkpoint != len(self.check_points)-1:
                        self.ceck_times[int(self.ceck_times_reset)][self.last_checkpoint] = (pygame.time.get_ticks() - self.start_lap_time)
                    else:
                        self.ceck_times[int(self.ceck_times_reset)][0] = (pygame.time.get_ticks() - self.start_lap_time)
                if i == 0:
                    self.start_lap()

    def distance_next_checkpoint(self):      
        if (self.last_checkpoint + 1) > len(self.check_points):
            mid_pnt = ((self.check_points[self.last_checkpoint + 1][0][0] + self.check_points[self.last_checkpoint + 1][1][0])/2,
                    (self.check_points[self.last_checkpoint + 1][0][1] + self.check_points[self.last_checkpoint + 1][1][1])/2)
        else:
            mid_pnt = ((self.check_points[0][0][0] + self.check_points[0][1][0])/2,
                    (self.check_points[0][0][1] + self.check_points[0][1][1])/2)
        
        dx = mid_pnt[0] - self.rect.centerx
        dy = mid_pnt[1] - self.rect.centery

        self.check_distance = math.sqrt(dx**2 + dy**2)
        
    def distance_prev_checkpoint(self):      
        if (self.last_checkpoint) > 0:
            mid_pnt = ((self.check_points[self.last_checkpoint][0][0] + self.check_points[self.last_checkpoint][1][0])/2,
                    (self.check_points[self.last_checkpoint][0][1] + self.check_points[self.last_checkpoint][1][1])/2)
        else:
            mid_pnt = ((self.check_points[0][0][0] + self.check_points[0][1][0])/2,
                    (self.check_points[0][0][1] + self.check_points[0][1][1])/2)
        
        dx = mid_pnt[0] - self.rect.centerx
        dy = mid_pnt[1] - self.rect.centery

        return math.sqrt(dx**2 + dy**2)
      
    def get_time_to_prev_point(self):
        self.prev_check_distance = self.distance_prev_checkpoint()
        d = float(getattr(self, 'prev_check_distance', 0.0))
        v = float(self.velocity.length())
        if v < 1.0:
            return math.inf
        else:
            return (d / v) * 1000
    
    def get_time_to_next_checkpoint(self, method='simple', deceleration=-300.0, min_speed=5.0):
        self.distance_next_checkpoint()

        d = float(getattr(self, 'check_distance', 0.0))
        v = float(self.velocity.length())

        # if practically not moving, we can't estimate reliably
        if v < min_speed:
            return math.inf

        if method == 'simple':
            return (d / v) * 1000

        if method == 'constant_accel':
            a = float(deceleration)  # negative if braking
            # if acceleration is nearly zero, fallback to simple estimate
            if abs(a) < 1e-6:
                return d / v * 1000

            # Solve: 0.5*a*t^2 + v*t - d = 0
            A = 0.5 * a
            B = v
            C = -d
            disc = B * B - 4 * A * C
            if disc < 0:
                return math.inf
            sqrt_disc = math.sqrt(disc)

            t1 = (-B + sqrt_disc) / (2 * A)
            t2 = (-B - sqrt_disc) / (2 * A)

            times = [t for t in (t1, t2) if t > 1e-6]
            return min(times) * 1000 if times else math.inf

        raise ValueError("Unknown method for time_to_next_checkpoint")
         
    def start_lap(self):
        self.lap = []
        self.true_lap = True
        self.start_lap_time = pygame.time.get_ticks()
        self.last_checkpoint = 0
        
    def check_lap(self):
        if self.lap == self.correct_lap and self.true_lap:
            self.ceck_times_reset = not(self.ceck_times_reset)
            lap_time = pygame.time.get_ticks() - self.start_lap_time
            self.prev_lap_time = lap_time
            self.time_lap_displayed = pygame.time.get_ticks()
            if lap_time < self.fastes_lap:
                self.fastes_lap = float(lap_time)
            self.lap = []
            self.start_lap_time = pygame.time.get_ticks()
            self.current_lap += 1
        
    def starting_clock(self):
        if not self.quali:
            if self.start_start_timer:
                time = ((pygame.time.get_ticks() - self.start_time)/1000)
                if time <= 5.2:
                    self.start_lap_time = pygame.time.get_ticks()
                    if time <= 1: 
                        self.light_image = self.starting_lights[5]
                    elif time <= 2: 
                        self.light_image = self.starting_lights[4]
                        if not self.start_beep_played[1]:
                            self.sound.car_fx['start_beep'].play()
                            self.start_beep_played[1] = True
                    elif time <= 3: 
                        self.light_image = self.starting_lights[3]
                        if not self.start_beep_played[2]:
                            self.sound.car_fx['start_beep'].play()
                            self.start_beep_played[2] = True
                    elif time <= 4: 
                        self.light_image = self.starting_lights[2]
                        if not self.start_beep_played[3]:
                            self.sound.car_fx['start_beep'].play()
                            self.start_beep_played[3] = True
                    elif time <= 5.2:
                        if not self.start_beep_played[4]:
                            self.sound.car_fx['start_beep'].play()
                            self.start_beep_played[4] = True
                        self.light_image = self.starting_lights[1]
                else:
                    self.can_move = True
                    self.light_image = self.starting_lights[0]
                    if not self.start_beep_played[5]:
                        self.sound.car_fx['start_beep'].play()
                        self.start_beep_played[5] = True
                if time <= 6:
                    self.display.blit(self.light_image, (self.display.get_width()/2 - self.light_image.get_width()/2, 80))
                else:
                    self.start_start_timer = False
                    self.can_move = True
            
    def get_state(self):
        return {
            "id": self.id,
            "name": self.name,
            "active": self.active,
            "ready": self.ready,
            "pos": (self.pos.x, self.pos.y),
            "angle": self.angle,
            "color": self.color,
            "helmet_color" : self.helmet_color,
            "velocity": (self.velocity.x, self.velocity.y),
            "last checkpoint" : self.last_checkpoint,
            "current_lap" : self.current_lap,
            "fastes_lap" : self.fastes_lap,
            "check_distance" : self.check_distance,
            "prev_check_distance" : self.prev_check_distance,
            "time_to_prev_point" : self.time_to_prev_point,
            "ceck_times" : self.ceck_times,
            "ceck_times_reset" : self.ceck_times_reset,
            "time_to_nxt_point" : self.time_to_nxt_point,
            'race_completed' : self.race_completed,
        }

    def set_state(self, state):
        state.pop('id', None)
        if 'pos' in state: self.pos = pygame.Vector2(state['pos'])
        if 'name' in state: self.name = state['name']
        if "active" in state: self.active = bool(state['active'])
        if "ready" in state: self.ready = bool(state['ready'])
        if 'angle' in state:self.angle = state['angle']
        if 'color' in state: self.color = state['color']
        if 'helmet_color' in state: self.helmet_color = state['helmet_color']
        if 'velocity' in state: self.velocity = pygame.Vector2(state['velocity'])
        if "last checkpoint" in state : self.last_checkpoint = state['last checkpoint']
        if 'current_lap' in state: self.current_lap = state['current_lap']
        if 'fastes_lap' in state: self.fastes_lap = state['fastes_lap']
        if 'check_distance' in state: self.check_distance = state['check_distance']
        if "prev_check_distance" in state: self.prev_check_distance = state["prev_check_distance"]
        if 'time_to_prev_point' in state: self.time_to_prev_point = state['time_to_prev_point']
        if "ceck_times" in state: self.ceck_times = state['ceck_times']
        if "ceck_times_reset" in state: self.ceck_times_reset = bool(state['ceck_times_reset'])
        if "time_to_nxt_point" in state : self.time_to_nxt_point = state['time_to_nxt_point']
        if 'race_completed' in state : self.race_completed = state['race_completed']
        
    def remote_update(self, dt, camera_x, camera_y):
        # apply movement and visuals for a remote player (no input)
        self.move(dt)
        # rotate image to match facing
        # ensure car_surf exists (create() must have been called earlier)
        self.recolor_player()
        if self.car_surf:
            self.image = pygame.transform.rotate(self.car_surf, self.angle)
            self.rect = self.image.get_frect(center=self.pos)
            self.display.blit(self.image, self.rect.topleft - pygame.Vector2(camera_x, camera_y))
        
    def car_image_load(self, *path):
        temp_image = pygame.image.load(join(*path)).convert_alpha()
        temp_image = pygame.transform.scale(temp_image, (temp_image.get_width()/15,temp_image.get_height()/15))
        
        return temp_image
    
    def helmet_image_load(self, *path):
        temp_image = pygame.image.load(join(*path)).convert_alpha()
        temp_image = pygame.transform.scale(temp_image, (temp_image.get_width()/40,temp_image.get_height()/40))
        
        return temp_image
        
    def input(self, dt):
        keys = pygame.key.get_pressed()

        # Facing direction based on angle
        facing_dir = pygame.Vector2(
            math.cos(math.radians(self.angle)),
            -math.sin(math.radians(self.angle))
        )

        # Improved Speed-dependent Steering with Clamp
        speed_ratio = self.velocity.length() / self.max_speed
        steering_ratio = 1 - min(speed_ratio, 1)
        steering_ratio = max(steering_ratio, 0.4)  # ⬅ minimum 40% steering strength
        steering = steering_ratio * self.rotation_speed * dt
        
        self.car_surf = pygame.Surface(self.body_image.get_size(), pygame.SRCALPHA)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            if self.velocity.length() == 0: self.angle += 0.05
            else: self.angle += steering
            
            self.car_surf.blit(self.left_wheels_image, (0,0))
            self.car_surf.blit(self.body_image, (0,0))
            self.draw_helmet()
        
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            if self.velocity.length() == 0: self.angle -= 0.05
            else: self.angle -= steering
            
            self.car_surf.blit(self.right_wheels_image, (0,0))
            self.car_surf.blit(self.body_image, (0,0))
            
            self.draw_helmet()
            
        if not(keys[pygame.K_a] or keys[pygame.K_RIGHT] or keys[pygame.K_d] or keys[pygame.K_RIGHT]):
            self.car_surf.blit(self.wheels_image, (0,0))
            self.car_surf.blit(self.body_image, (0,0))
            
            self.draw_helmet()

        # Smooth Acceleration
        target_velocity = pygame.Vector2()

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            if self.velocity.length() < 5:
                #self.sound.car_fx['start'].play()
                pass
            else:
                #self.sound.car_fx['acelerate'].play()
                pass
            self.acceleration_time += dt
            accel_multiplyer = min(1.0, 1 -math.exp(-3*self.acceleration_time))
            target_velocity = facing_dir * self.max_speed * accel_multiplyer
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.sound.car_fx['start'].stop()
            self.acceleration_time = 0
            target_velocity = -facing_dir * self.max_speed * 0.5 
        if not(keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_s] or keys[pygame.K_DOWN]):
            self.acceleration_time = 0

        # Smoothly interpolate toward target velocity
        self.velocity = self.velocity.lerp(target_velocity, min(self.acceleration * dt, 1))


        # Friction (smooth deceleration)
        if target_velocity.length_squared() == 0 and self.velocity.length_squared() > 0:
            self.velocity = self.velocity.lerp(pygame.Vector2(), self.friction)
            if self.velocity.length() < 0.05:
                self.velocity = pygame.Vector2()

        # Clamp max speed
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        # Drift correction
        if self.velocity.length() > 0:
            drift_correction_vec = facing_dir * self.velocity.dot(facing_dir)
            self.velocity = self.velocity.lerp(drift_correction_vec, self.drift_correction)
        
        # reset
        if keys[pygame.K_r]:
            self.reset_player()
        
        # Break
        if keys[pygame.K_SPACE]:
            self.sound.car_fx['start'].stop()
            self.sound.car_fx['acelerate'].stop()
            self.sound.car_fx['max'].stop()
            if self.velocity.length_squared() > 0:
                self.brake_strength += 2.5 * dt
                brake_dir = -self.velocity.normalize()
                self.acceleration_time -= 0.12 *dt
                self.velocity += brake_dir * self.brake_strength *2.5
                
                # Stop if we're going too slow (to avoid flipping direction)
                if self.velocity.length() < 30:
                    self.velocity = pygame.Vector2()
                    
                #self.sound.car_fx['breaking'].play(-1)
        else:
            self.brake_strength = self.og_brake_strenght
            
            if self.max_speed - self.velocity.length() < 10:
                if self.acs_sound:
                    self.acs_sound.queue(self.sound.car_fx['max'])
            else:
                self.sound.car_fx['max'].stop()
            self.sound.car_fx['breaking'].stop()
        
    def ind_input(self):
        keys_once = pygame.key.get_just_pressed()
        
        if (not(self.start_start_timer) or self.quali) and not self.can_move and (keys_once[pygame.K_LSHIFT] or keys_once[pygame.K_RSHIFT]):
            self.ready = not self.ready
            
    def move(self, dt):
        self.prev_pos = self.pos.copy()
        self.pos += self.velocity * dt
        self.rect.center = self.pos
        
    def on_track(self, track):
        if 0 <= self.rect.centerx < track.get_size()[0] and 0 <= self.rect.centery < track.get_size()[1]:
            if not(track.get_at((self.rect.centerx, self.rect.centery))):
                self.velocity = pygame.math.Vector2() - self.velocity
                #pass
                        
        else:
            self.reset_player()
                        
    def reset_player(self):
        self.start_lap_time = pygame.time.get_ticks()
        self.true_lap = False
        self.pos = pygame.Vector2(self.og_pos)
        self.velocity = pygame.math.Vector2()
        self.rect.center = self.pos
        self.angle = self.og_angle
        
    def get_track_position(self, race_order):
        for pos, i in enumerate(race_order):
            if i == self.id:
                self.track_position = pos +1
              
    def update(self, dt, camera_x, camera_y, track, race_order, track_record, player_color, helmet_color):
        #print(self.angle, self.pos)
        self.color = player_color
        self.helmet_color = helmet_color
        self.recolor_player()
        self.active = True
        self.track_record = track_record
        self.time_to_prev_point = self.get_time_to_prev_point()
        self.time_to_nxt_point = self.get_time_to_next_checkpoint()
        self.distance_next_checkpoint()
        self.prev_check_distance = self.distance_prev_checkpoint()
        
        if self.inf_laps:
            self.move(dt)
            self.input(dt)
        elif self.can_move:
            self.move(dt)
            self.input(dt)
            
        self.ind_input()
        
        self.get_track_position(race_order)
        
        self.on_track(track)
        
        self.past_points(camera_x, camera_y)

        # Rotate image to match facing
        if self.car_surf: self.image = pygame.transform.rotate(self.car_surf, self.angle)
        self.rect = self.image.get_frect(center=self.pos)
        self.display.blit(self.image, self.rect.topleft - pygame.Vector2(camera_x, camera_y))
        
        self.ui()
        if not self.inf_laps: self.starting_clock()
        
    def ui(self):
        
        if self.can_move:
            if self.fastes_lap < (pygame.time.get_ticks() - self.start_lap_time):
                self.lap_time_txt =  make_txt(f'{((pygame.time.get_ticks() - self.start_lap_time)/1000):.3f}s', self.time_font, 'red')
            else:
                self.lap_time_txt =  make_txt(f'{((pygame.time.get_ticks() - self.start_lap_time)/1000):.3f}s', self.time_font, 'white')
            self.display.blit(self.lap_time_txt, (self.display.get_width()/2 - self.lap_time_txt.get_width()/2, 70))
        
        if self.fastes_lap < 999999:
            self.fastes_lap_txt = make_txt(f'Fastes: {(self.fastes_lap/1000):.3f}s', self.lap_time_font, 'white')
            self.display.blit(self.fastes_lap_txt, (self.display.get_width() - self.fastes_lap_txt.get_width()*1.1, self.display.get_height()-100))
            
        if self.prev_lap_time:
            if (pygame.time.get_ticks() - self.time_lap_displayed)/1000 < 5:
                self.prev_lap_txt = make_txt(f'{(self.prev_lap_time/1000):.3f}s', self.lap_time_font, 'white')
                self.display.blit(self.prev_lap_txt, (self.display.get_width() - self.prev_lap_txt.get_width()*1.1, self.display.get_height() - 100 - self.fastes_lap_txt.get_height()*1.2))

        if self.track_record[1] < 999999:
            track_record_txt = make_txt(f'Track record: {self.track_record[0]} - {(self.track_record[1] /1000):.3f}s', self.lap_time_font, (129,68,146))
            self.display.blit(track_record_txt, (self.display.get_width() - track_record_txt.get_width()*1.1, 
                                                self.display.get_height() - 70))
        
        if not self.inf_laps and not self.can_move and not self.race_completed:
            if not self.quali:
                self.display.blit(self.light_image, (self.display.get_width()/2 - self.light_image.get_width()/2, 80))
            txt = make_txt(f'Press Shift to start', self.pos_font, 'white')
            if not self.ready: self.display.blit(txt, (self.display.get_width()/2 - txt.get_width()/2, self.display.get_height() - 200))

        # Optional: Draw direction line
        #dir_vector = pygame.Vector2(math.cos(math.radians(self.angle)), -math.sin(math.radians(self.angle))) * 20
        #pygame.draw.line(self.display, 'white', self.pos, self.pos + dir_vector, 2)
