# race.py (complete — supports up to 8 players, only draws active players)
from settings import *
from player import Player
from network import Network
import json
from os.path import join
import pygame
import math

class Race:
    def __init__(self, sound, track_num, suit_color, helmet_color, player_name):
        # display & sound
        self.display = pygame.display.get_surface()
        self.display_w = self.display.get_width()
        self.display_h = self.display.get_height()
        self.sound = sound
        
        self.main_menu = False

        # Max players
        self.max_players = 8
        # Provide a color for each potential player (8 colors)

        self.create_p2 = False
        self.player2 = None

        # network
        self.n = Network()
        assignment = self.n.get_initial_assignment()
        assigned_id = 1
        if isinstance(assignment, dict) and 'assigned_id' in assignment:
            assigned_id = assignment['assigned_id']
            
        
        # local player
        self.player = Player(assigned_id)
        # If track_data not yet loaded we'll create the player with an empty dict and later call create again.
            
        self.track_num = getattr(self, 'track_num', track_num)
        #self.track_num = getattr(self, 'track_num', int(input('Enter the track number you want to race on: ')))

        # attempt to load track data now (if it fails we'll still create a player)
        try:
            self.track_data = self.load_data()
        except Exception:
            self.track_data = {}
            
        self.track_record = self.track_data['lap_record']

        self.player.create(self.track_data, self.sound, self.track_num)
        self.player.name = player_name
        self.suit_color = suit_color
        self.helmet_color = helmet_color

        # dict of remote Player objects keyed by id
        self.remote_players = {}

        # racers is rebuilt every frame from active players (local always included)
        self.racers = [self.player]

        # some other state
        self.players_can_move = True
        self.start = True
        
        self.qualifying = True
        self.quali_fastes_lap = 99999999
        self.qualifying_time = None
        
        self.debug_track = False
        self.create_track = True
        self.track_pos = '['
        
                # --- ground (world surface) ---
        self.ground = pygame.image.load(join('..','tracks',f'track_{self.track_num}','ground.png')).convert_alpha()
        self.ground = pygame.transform.scale(self.ground, (int(self.ground.get_width()*2.6), int(self.ground.get_height()*2.6)))

        # --- minimap image (may contain padding or margins) ---
        self.minimap = pygame.image.load(join('..','tracks',f'track_{self.track_num}','map.png')).convert_alpha()
        # keep the same scale you were using (minimap is smaller than ground)
        self.minimap = pygame.transform.scale(self.minimap, (int(self.minimap.get_width()/3), int(self.minimap.get_height()/3)))

        self.mini_x_off = self.ground.get_width() / self.minimap.get_width()
        self.mini_y_off = self.ground.get_height() / self.minimap.get_height()
        
        self.first_suit1, self.first_suit2, self.first_helmet1, self.first_helmet2 = self.load_racer(0.7)
        self.second_suit1, self.second_suit2, self.second_helmet1, self.second_helmet2 = self.load_racer(0.65)
        self.third_suit1, self.third_suit2, self.third_helmet1, self.third_helmet2 = self.load_racer(0.65)
        
        self.track_mask = pygame.mask.from_surface(self.ground)
        
        # if you already have a track surface elsewhere keep it, otherwise create a placeholder
        if not hasattr(self, 'track') or self.track is None:
            self.track = pygame.Surface((1000, 1000))

        self.race_order = []
        
        self.podium_back_img = pygame.image.load(join('..','resourcess','background','podium.png')).convert_alpha()
        
        self.lb_image = pygame.image.load(join('..','resourcess','ui','logo.png')).convert_alpha()
        self.lb_image = pygame.transform.scale(self.lb_image, (self.lb_image.get_width()//9, self.lb_image.get_height()//9))
        
        self.fastest_l_image = pygame.image.load(join('..','resourcess','ui','fastest.png')).convert_alpha()
        self.fastest_l_image = pygame.transform.scale(self.fastest_l_image, (self.fastest_l_image.get_width()//8, self.fastest_l_image.get_height()//8))
        
        self.done_image = pygame.image.load(join('..','resourcess','ui','complete.png')).convert_alpha()
        self.done_image = pygame.transform.scale(self.done_image, (self.done_image.get_width()//14, self.done_image.get_height()//14))
        
        self.font_25 = pygame.font.Font(join('..','resourcess','font','Formula1-Bold-4.ttf'), 25)
        self.font_18_b = pygame.font.Font(join('..','resourcess','font','Formula1-Black.ttf'), 18)
        self.font_17 = pygame.font.Font(join('..','resourcess','font','Formula1-Bold-4.ttf'), 17)
        self.font_16 = pygame.font.Font(join('..','resourcess','font','Formula1-Bold-4.ttf'), 16)
        self.font_16_b = pygame.font.Font(join('..','resourcess','font','Formula1-Black.ttf'), 16)
        self.font_14_i = pygame.font.Font(join('..','resourcess','font','Formula1-Italic.ttf'), 14)
        self.font_14 = pygame.font.Font(join('..','resourcess','font','Formula1-Bold-4.ttf'), 14)
        self.font_13_i = pygame.font.Font(join('..','resourcess','font','Formula1-Italic.ttf'), 13)
        
        self.race_txt = make_txt('RACE', self.font_18_b, (190, 190, 190))
        self.lap_txt = make_txt('LAP', self.font_14_i, (190, 190, 190))
        
        self.Q1_txt = make_txt('Q1', self.font_18_b, 'white')
        
        self.total_lap_txt = make_txt(f'/{self.track_data['laps']}', self.font_14_i, (190, 190, 190))
        
        self.tack_fastest_lap = 999999
        
        self.fastest_y_pos = 0
        
        self.display_track_record = False
        self.track_record_img = pygame.image.load(join('..','resourcess','ui','record.png')).convert_alpha()
        self.track_record_img = pygame.transform.scale(self.track_record_img, (self.track_record_img.get_width()//4, self.track_record_img.get_height()//4))
        self.record_txt = make_txt('NEW LAP RECORD', self.font_16, (129,68,146))
        self.track_record_y = -30
        self.move_down_record = True
        self.time_record_display = pygame.time.get_ticks()

        self.update_time_player = pygame.time.get_ticks()
        
        self.time_between_surf = [None, None]
        
        self.podium = False
        
        self.race_complete_order = []
        
        
    def load_racer(self, scale):
        suit1 = pygame.image.load(join('..','resourcess','driver','suit1.png')).convert_alpha()
        suit1 = pygame.transform.scale(suit1, (suit1.get_width()*scale, suit1.get_height()*scale))
        
        suit2 = pygame.image.load(join('..','resourcess','driver','suit2.png')).convert_alpha()
        suit2 = pygame.transform.scale(suit2, (suit2.get_width()*scale, suit2.get_height()*scale))
        
        helmet1 = pygame.image.load(join('..','resourcess','driver','helmet1.png')).convert_alpha()
        helmet1 = pygame.transform.scale(helmet1, (helmet1.get_width()*scale, helmet1.get_height()*scale))
        
        helmet2 = pygame.image.load(join('..','resourcess','driver','helmet2.png')).convert_alpha()
        helmet2 = pygame.transform.scale(helmet2, (helmet2.get_width()*scale, helmet2.get_height()*scale))
        
        return suit1, suit2, helmet1, helmet2

    def load_data(self):
        """Load track data JSON for the current track_num. Adjust path to your project layout if needed."""
        path = join('..', 'tracks', f'track_{self.track_num}', 'data.json')
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    def input(self):
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_ESCAPE]:
            self.main_menu = True
            
    def race_end(self):
        self.podium = True
        for racer in self.race_order:
            if racer.current_lap == racer.total_lap + 1:
                racer.race_completed = True
                racer.velocity = pygame.math.Vector2()
                racer.can_move = False
                if not racer in self.race_complete_order: self.race_complete_order.append(racer)
            self.podium = racer.race_completed
        #print(self.podium)
        
        if self.podium:
            self.display.blit(self.podium_back_img, (0,0))
            for player in self.race_order:
                player.can_move = False
                
            for i in range(0, min(3, len(self.race_complete_order))):
                if self.race_order[i].active:
                    name_txt = make_txt(self.race_complete_order[i].name,self.font_25, 'white')
                    if i == 0:
                        color_suit = self.first_suit1.copy()
                        color_suit.fill(self.race_order[i].color, special_flags=pygame.BLEND_MULT)
                        
                        color_helmet = self.first_helmet1.copy()
                        color_helmet.fill(self.race_order[i].helmet_color, special_flags=pygame.BLEND_MULT)
                        
                        surf = pygame.Surface(color_suit.get_size(), pygame.SRCALPHA)
                        surf.blit(color_suit, (0,0))
                        surf.blit(self.first_suit2, (0,0))
                        surf.blit(color_helmet, (0,0))
                        surf.blit(self.first_helmet2, (0,0))
                        
                        self.display.blit(surf, (self.display_w/2 - surf.get_width()/2,140))
                        self.display.blit(name_txt, (self.display_w/2 - name_txt.get_width()/2,110))
                        
                    if i == 1:
                        color_suit = self.second_suit1.copy()
                        color_suit.fill(self.race_order[i].color, special_flags=pygame.BLEND_MULT)
                        
                        color_helmet = self.second_helmet1.copy()
                        color_helmet.fill(self.race_order[i].helmet_color, special_flags=pygame.BLEND_MULT)
                        
                        surf = pygame.Surface(color_suit.get_size(), pygame.SRCALPHA)
                        surf.blit(color_suit, (0,0))
                        surf.blit(self.second_suit2, (0,0))
                        surf.blit(color_helmet, (0,0))
                        surf.blit(self.second_helmet2, (0,0))
                        
                        self.display.blit(surf, (150,190))
                        self.display.blit(name_txt, (235 - name_txt.get_width()/2,160))
                        
                    if i == 2:
                        color_suit = self.third_suit1.copy()
                        color_suit.fill(self.race_order[i].color, special_flags=pygame.BLEND_MULT)
                        
                        color_helmet = self.third_helmet1.copy()
                        color_helmet.fill(self.race_order[i].helmet_color, special_flags=pygame.BLEND_MULT)
                        
                        surf = pygame.Surface(color_suit.get_size(), pygame.SRCALPHA)
                        surf.blit(color_suit, (0,0))
                        surf.blit(self.third_suit2, (0,0))
                        surf.blit(color_helmet, (0,0))
                        surf.blit(self.third_helmet2, (0,0))
                        
                        self.display.blit(surf, (self.display_w - surf.get_width() - 150,190))
                        self.display.blit(name_txt, (self.display_w - 235 - name_txt.get_width()/2,160))
                    

            
    
    def check_lap_record(self):
        for player in self.race_order:
            if player.fastes_lap < self.track_record[1]:
                self.track_record = [player.name, player.fastes_lap]
                
                data = {"start": self.track_data['start'], "start_line": self.track_data['start_line'], "checks": self.track_data['checks'], 
                        'laps':self.track_data['laps'], 'lap_record': self.track_record}
                
                with open(join('..','tracks',f'track_{self.track_num}','data.json'), "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                    
                self.display_track_record = True
                self.move_down_record = True
    
    def update(self, dt):
        """Main per-frame update. Sends local state to server, receives all players, updates/draws only active players."""
        # ensure race start handling (lights/timer etc.)
        self.start_race()
        
        self.input()

        # camera relative offset (follow local player)
        # ensure player has a rect
        if hasattr(self.player, 'rect'):
            self.offset = self.player.rect.center
        else:
            self.offset = (0, 0)

        camera_x = self.offset[0] - self.display_w // 2
        camera_y = self.offset[1] - self.display_h // 2
        
        self.debug(camera_x, camera_y)

        if not self.podium:
            # draw track (centered by camera)
            try:
                self.display.blit(self.ground, (-camera_x, -camera_y))
            except Exception:
                # fallback: fill background
                self.display.fill((30, 30, 30))

        # send local player state and receive full players list from server
        players_list = None
        try:
            players_list = self.n.send(self.player)
        except Exception:
            players_list = None

        if players_list and isinstance(players_list, list):
            for state in players_list:
                if not isinstance(state, dict):
                    continue
                pid = state.get('id')
                if pid is None:
                    continue

                # skip the local player's remote entry (we keep authoritative local object)
                if pid == self.player.id:
                    # optionally reconcile a few server-side authoritative fields:
                    # e.g. self.player.current_lap = state.get('current_lap', self.player.current_lap)
                    continue

                # if player is active and doesn't yet have a remote Player object, create it
                if state.get('active') and pid not in self.remote_players:
                    if pid not in self.remote_players and pid != self.player.id:
                        p = Player(pid)
                        p.create(self.track_data, self.sound, self.track_num)
                        p.color = state.get('color')
                        p.recolor_player()
                        # ensure defaults (so ready exists)
                        p.active = bool(state.get('active', False))
                        p.ready = bool(state.get('ready', False))
                        self.remote_players[pid] = p

                # if we have an object for this pid, update its state
                if pid in self.remote_players:
                    p = self.remote_players[pid]
                    # Prefer a dedicated setter if your Player class provides it:
                    if hasattr(p, 'set_state'):
                        try:
                            p.set_state(state)
                        except Exception:
                            # fallback to manual assignment
                            p.pos = state.get('pos', getattr(p, 'pos', p.pos))
                            p.angle = state.get('angle', getattr(p, 'angle', getattr(p, 'og_angle', 0)))
                            p.active = state.get('active', True)
                            p.last_checkpoint = state.get('last checkpoint', getattr(p, 'last_checkpoint', 0))
                            p.current_lap = state.get('current_lap', getattr(p, 'current_lap', 0))
                    else:
                        p.pos = state.get('pos', getattr(p, 'pos', p.pos))
                        p.angle = state.get('angle', getattr(p, 'angle', getattr(p, 'og_angle', 0)))
                        p.active = state.get('active', True)
                        p.last_checkpoint = state.get('last checkpoint', getattr(p, 'last_checkpoint', 0))
                        p.current_lap = state.get('current_lap', getattr(p, 'current_lap', 0))

        # Rebuild racers list from active players (local always included)
        active_racers = [self.player]
        for p in self.remote_players.values():
            if getattr(p, 'active', False):
                active_racers.append(p)
        self.racers = active_racers

        # Update and draw remote players (only active ones)
        for pid, p in list(self.remote_players.items()):
            if not getattr(p, 'active', False):
                continue
            # remote_update should draw the car at its position relative to camera
            if hasattr(p, 'remote_update'):
                try:
                    # many remote_update implementations expect (dt, camera_x, camera_y)
                    p.remote_update(dt, camera_x, camera_y)
                except TypeError:
                    # fallback if remote_update takes different args
                    try:
                        p.remote_update(dt)
                    except Exception:
                        pass
                    # if even that fails, continue silently
            else:
                # If no remote_update, try calling update with a flag or draw manually
                if hasattr(p, 'update'):
                    try:
                        p.update(dt, camera_x, camera_y, self.track, self.race_order, self.track_record)
                    except Exception:
                        try:
                            p.update(dt)
                        except Exception:
                            pass

        # Update local player (physics, input, collisions)
        # Assumes your Player.update signature matches this call
        if hasattr(self.player, 'update'):
            try:
                self.player.update(dt, camera_x, camera_y, self.track_mask, self.race_order, self.track_record, self.suit_color, self.helmet_color)
            except TypeError as t:
                # fallback if your Player.update has a different signature
                print(t)
                try:
                    self.player.update(dt)
                except Exception as e:
                    print(e)

        # update race order (sort by lap then checkpoint)
        def sort_key(player):
            if not self.qualifying:
                lap = int(getattr(player, 'current_lap', 0))
                cp = int(getattr(player, 'last_checkpoint', 0))
                dist = float(getattr(player, 'check_distance', 0))  # smaller = ahead

                # Use -dist so that being further ahead (smaller distance) comes first in reverse=True
                return (lap, cp, -dist)
            else:
                lap_time = int(getattr(player, 'fastes_lap', 0))
                return (-lap_time)
        
        self.race_order = sorted(self.racers, key=sort_key, reverse=True)
        
        self.check_lap_record()
        
        self.stop_Quali()
        self.ui(dt)
        self.minimap_logic(camera_x,camera_y)
        self.race_end()
        
    def minimap_logic(self, camera_x, camera_y):
            self.display.blit(self.minimap, (self.display_w - self.minimap.get_width()*1.1, 40))
            minimap_screen_pos = (self.display_w - self.minimap.get_width()*1.1, 40)

            # Convert world position -> minimap position
            mini_x = self.player.rect.centerx / self.mini_x_off
            mini_y = self.player.rect.centery / self.mini_y_off

            # Add screen offset (where minimap is drawn)
            mini_pos = (minimap_screen_pos[0] + mini_x, minimap_screen_pos[1] + mini_y)

            # Draw player dot
            pygame.draw.circle(self.display, 'black', mini_pos, 3)
            pygame.draw.circle(self.display, self.player.color, mini_pos, 2)
        
    def ui(self, dt):
        back_rect = pygame.Surface((150, 600), pygame.SRCALPHA)
        pygame.draw.rect( back_rect, (0, 0, 0, 220), (0, 0, 170, 800), border_radius=20, border_top_right_radius=0, border_bottom_right_radius=0 )
        
        back_rect.blit(self.lb_image, (10, 10))
        
        order_txt = []
        for i, player in enumerate(self.race_order):
            race_name = player.name
            if len(race_name) > 3: race_name = race_name[:3]
            order_txt.append(make_txt(f'{i+1}   {race_name}', self.font_14, (255, 255, 255)))
            
        for i, txt in enumerate(order_txt):
           back_rect.blit(txt, (20, 50 + (i+1)*20))
                
        if not self.qualifying:
            cur_lap_txt = make_txt(f'{self.player.current_lap}', self.font_17, (255, 255, 255))
            back_rect.blit(cur_lap_txt, (170/2 - cur_lap_txt.get_width()/2, 41))
            
            
            back_rect.blit(self.race_txt, (82, 11))
            
            back_rect.blit(self.lap_txt, (170/2 - cur_lap_txt.get_width()/2 - self.lap_txt.get_width()*1.2, 41))
            back_rect.blit(self.total_lap_txt, (170/2 - cur_lap_txt.get_width()/2 + cur_lap_txt.get_width() + 2, 41))
                
            for i, player in enumerate(self.race_order):
                if player.fastes_lap < self.tack_fastest_lap:
                    self.tack_fastest_lap = player.fastes_lap
                    self.fastest_y_pos = 85 + (i+1)*20
            
            if self.tack_fastest_lap < 99999:
                pass
                #self.display.blit(self.fastest_l_image, (38 + back_rect.get_width(), self.fastest_y_pos))
                    
            if (pygame.time.get_ticks() - self.update_time_player)/1000 >= 1:
                self.time_between_surf = self.get_time_between_players()
        
            for i, surf in enumerate(self.time_between_surf):
                if surf:
                    back_rect.blit(surf, (75, 50 + (i+1)*20))
                    
            for i, racer in enumerate(self.race_order):
                if racer.race_completed:
                    self.display.blit(self.done_image, (38 + back_rect.get_width(), 85 + (i+1)*20))
                    
        else:
            back_rect.blit(self.Q1_txt, (100, 11))
            time_surf = []
            for i, player in enumerate(self.race_order):
                if player.fastes_lap < 999999:
                    if i == 0:
                        self.quali_fastes_lap = player.fastes_lap
                        time_surf.append(make_txt(f'{(self.quali_fastes_lap/1000):.3f}s', self.font_14, 'white'))
                    else:
                        time_surf.append(make_txt(f'+ {((player.fastes_lap - self.quali_fastes_lap)/1000):.3f}s', self.font_14, 'white'))
                else:
                    time_surf.append(make_txt(f'NO TIME', self.font_14, 'white'))
                        
            for i, surf in enumerate(time_surf):
                back_rect.blit(surf, (back_rect.width - surf.get_width() - 10, 50 + (i+1)*20))
                
            if self.qualifying_time:
                time = (301 - (pygame.time.get_ticks() - self.qualifying_time)/1000)
                if time > 60:
                    time_txt = make_txt(f'{int(time // 60)}:{int(time % 60)}', self.font_18_b, 'white')
                else:
                    if int(time) % 2 == 0:
                        time_txt = make_txt(f'{int(time % 60)}', self.font_18_b, 'white')
                    else:
                        time_txt = make_txt(f'{int(time % 60)}', self.font_18_b, 'red')
                back_rect.blit(time_txt, (back_rect.width/2 - time_txt.get_width()/2, 41))
        
        self.display.blit(back_rect, (40, 40))
        
        # track record
        
        if self.display_track_record:
            if self.move_down_record and self.track_record_y <= 20:
                self.track_record_y += 2
                self.time_record_display = pygame.time.get_ticks()
            
            if (pygame.time.get_ticks() - self.time_record_display)/1000 > 3:
                self.move_down_record = False
                self.track_record_y -= 2
                
            if not self.move_down_record and self.track_record_y <= -60:
                self.display_track_record = False
            
            
            record_name_txt = make_txt(f'{self.track_record[0]}', self.font_16_b, 'white')
            black_rect = pygame.FRect(400,self.track_record_y,200, self.track_record_img.get_height())
            time_txt = make_txt(f'{(self.track_record[1]/1000):.3f}s',self.font_25,'white')
            purple_rect = pygame.FRect(black_rect.right,self.track_record_y, time_txt.get_width() + record_name_txt.get_width() + 50,self.track_record_img.get_height())
            
            bar_width = black_rect.width + purple_rect.width + self.track_record_img.get_width()
            
            black_rect.left = self.display.get_width()//2 - (bar_width - black_rect.width - self.track_record_img.get_width())
            purple_rect.left = black_rect.right
            
            pygame.draw.rect(self.display, 'black',black_rect)
            pygame.draw.rect(self.display, (129,68,146),purple_rect)
            
            self.display.blit(self.track_record_img, (black_rect.left - self.track_record_img.get_width(),self.track_record_y))
            self.display.blit(self.record_txt, (black_rect.centerx - self.record_txt.get_width()//2, black_rect.centery - self.record_txt.get_height()//2))
            self.display.blit(record_name_txt, (purple_rect.left + 10, purple_rect.centery - record_name_txt.get_height()//2))
            self.display.blit(time_txt, (purple_rect.right - time_txt.get_width() - 20, 
                                         purple_rect.centery - time_txt.get_height()//2))
            
    def get_time_between_players(self):
        txt_surf = []
        num_checks = len(self.track_data['checks'])

        def get_check_times(player):
            # handle possible typos in your codebase ('ceck_times' vs 'check_times')
            return getattr(player, 'check_times', None) or getattr(player, 'ceck_times', None)

        def avg_segment_time():
            # If you have a track-wide average time per segment, use it.
            # Fallback: estimate 1 second (1000 ms) per segment — adjust to your game.
            return self.track_data.get('avg_segment_time', 1000)

        def progress_fraction(player):
            # Estimate fraction between checkpoints.
            # If both values exist and are finite, use time since prev / total segment time.
            # We assume: time_to_prev_point = time since last checkpoint,
            #           time_to_nxt_point = time remaining to next checkpoint.
            t_prev = getattr(player, 'time_to_prev_point', math.inf)
            t_next = getattr(player, 'time_to_nxt_point', math.inf)
            if t_prev is None or t_next is None:
                return 0.0
            if t_prev == math.inf or t_next == math.inf:
                return 0.0
            denom = t_prev + t_next
            if denom == 0:
                return 0.0
            return float(t_prev) / denom  # between 0 (just passed) and 1 (just before next)

        def continuous_position(player):
            # position in "checkpoint units" (can be fractional)
            # pos = completed laps * num_checks + checkpoint_index + progress
            lap = getattr(player, 'current_lap', 0)
            cp = getattr(player, 'last_checkpoint', 0)
            prog = progress_fraction(player)
            return lap * num_checks + cp + prog

        def estimate_time_gap_from_segments(nxt_player, player):
            """
            Try to compute an *exact* time gap by summing nxt_player's recorded segment times
            from player to nxt_player. If nxt_player doesn't have per-segment data, fall back
            to average_segment_time * distance_in_segments.
            Returned value is in milliseconds.
            """
            nxt_times = get_check_times(nxt_player)
            # distance in pure segment-units (not laps)
            pos_nxt = continuous_position(nxt_player)
            pos_player = continuous_position(player)
            dist = pos_nxt - pos_player
            if dist <= 0:
                return 0.0

            # If nxt_player has per-segment times in a 2D structure like times[lap_idx][segment_idx],
            # try to use the latest lap array (there may be a 'check_times_reset' index in your code).
            # We'll try to find a 1D array for the current lap:
            if nxt_times:
                # attempt to fetch the most-recent lap times array
                lap_index = getattr(nxt_player, 'check_times_reset', None) or getattr(nxt_player, 'ceck_times_reset', None)
                try:
                    if lap_index is not None:
                        lap_times = nxt_times[lap_index]
                    else:
                        # if nxt_times already 1D, use it
                        lap_times = nxt_times[0] if isinstance(nxt_times[0], (list, tuple)) else nxt_times
                except Exception:
                    # fall back: use first 1D array if possible
                    if isinstance(nxt_times[0], (list, tuple)):
                        lap_times = nxt_times[0]
                    else:
                        lap_times = None

                if lap_times and len(lap_times) >= num_checks:
                    # we'll sum across segments from player's checkpoint to nxt's checkpoint,
                    # wrapping across the lap boundary as needed. This uses nxt_player's recorded
                    # seg-times as an approximation of the time it takes to traverse each segment.
                    total_ms = 0.0

                    # start from the player's next segment index (player.last_checkpoint)
                    start_index = int(getattr(player, 'last_checkpoint', 0))
                    # end index is nxt_player.last_checkpoint (we'll not include that segment index itself
                    # when using range semantics consistent with your original code).
                    end_index = int(getattr(nxt_player, 'last_checkpoint', 0))

                    # if both are on same lap (pos_nxt and pos_player differ < num_checks)
                    # then just sum from start_index to end_index-1
                    # otherwise sum from start_index..num_checks-1 and 0..end_index-1
                    if (pos_nxt // num_checks) == (pos_player // num_checks):
                        # same lap
                        for point in range(start_index, end_index):
                            total_ms += lap_times[point]
                    else:
                        # wrap-around: from start_index to end of lap
                        for point in range(start_index, num_checks):
                            total_ms += lap_times[point]
                        # then from 0 to end_index-1
                        for point in range(0, end_index):
                            total_ms += lap_times[point]

                    # add partial segments:
                    # player still needs time_to_nxt_point to reach its next checkpoint
                    t_player_to_next = getattr(player, 'time_to_nxt_point', math.inf)
                    if t_player_to_next != math.inf:
                        total_ms += float(t_player_to_next)
                    # nxt_player may be partway through a segment; add nxt_player.time_to_prev_point to align
                    t_nxt_prev = getattr(nxt_player, 'time_to_prev_point', math.inf)
                    if t_nxt_prev != math.inf:
                        total_ms += float(t_nxt_prev)

                    return total_ms

            # fallback: estimate using average segment time
            return dist * avg_segment_time()

        # main loop
        for i, player in enumerate(self.race_order):
            if i == 0:
                txt_surf.append(make_txt('Interval', self.font_13_i, (255,255,255)))
                continue

            nxt_player = self.race_order[i-1]  # the one ahead
            pos_nxt = continuous_position(nxt_player)
            pos_player = continuous_position(player)
            diff = pos_nxt - pos_player

            # If leader is at least one full lap ahead -> show lap count
            if diff >= num_checks:
                laps_ahead = int(diff // num_checks)
                txt_surf.append(make_txt(f'+{laps_ahead} lap' + ('s' if laps_ahead > 1 else ''), self.font_13_i, (255,255,255)))
            else:
                # compute estimated time gap (ms)
                time_ms = estimate_time_gap_from_segments(nxt_player, player)
                txt_surf.append(make_txt(f'+{time_ms/1000:.3f}s', self.font_13_i, (255,255,255)))

        self.update_time_player = pygame.time.get_ticks()
        return txt_surf
       
    def stop_Quali(self):
        if self.qualifying:
            if (301 - (pygame.time.get_ticks() - self.qualifying_time)/1000) <= 0: #301
                for i, player in enumerate(self.race_order):
                    player.ready = False
                    player.can_move = False
                    self.players_can_move = True
                    player.og_pos = self.track_data['start'][i][0]
                    player.current_lap = 1
                self.player.reset_player()
                self.qualifying = False
                self.player.quali = False
                self.start = True
             
    def start_race(self):
        if self.start:
            # connected players (local + all remote slots we know about)
            connected = [self.player] + list(self.remote_players.values())

            # require all connected players to be ready to allow movement
            all_ready = len(connected) > 0 and all(getattr(p, 'ready', False) for p in connected)

            self.players_can_move = all_ready

            # set timers/flags on each connected player
            if not self.qualifying:
                for player in connected:
                    if not getattr(player, 'start_start_timer', False):
                        player.start_time = pygame.time.get_ticks()
                    player.start_start_timer = self.players_can_move

            # flip start when players_can_move becomes True (i.e., all connected ready)
            if not self.qualifying:
                self.start = not self.players_can_move
            else:
                if self.players_can_move:
                    self.start = False
                    for player in connected:
                        player.can_move = self.players_can_move
            
            if self.start:
                self.qualifying_time = pygame.time.get_ticks()

    def get_tack_pos(self):
        """Return current race order (list of player ids in position order)."""
        return self.race_order
    
    def debug(self, camera_x, camera_y):
        if self.debug_track:
            if pygame.mouse.get_just_pressed()[0]:
                print(f'({int(pygame.mouse.get_pos()[0] + camera_x)},{int(pygame.mouse.get_pos()[1] + camera_y)}),')
                if self.create_track:
                    self.track_pos += f'(({int(pygame.mouse.get_pos()[0] + camera_x)},{int(pygame.mouse.get_pos()[1] + camera_y)}),'
                else:
                    self.track_pos += f'({int(pygame.mouse.get_pos()[0] + camera_x)},{int(pygame.mouse.get_pos()[1] + camera_y)})),'
                self.create_track = not self.create_track
