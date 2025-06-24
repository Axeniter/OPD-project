import pygame
import os
import random
import math

# глобальные переменные
WIDTH = 1000
HEIGHT = 600
FPS = 60
WORLD_WIDTH = 5000
WORLD_HEIGHT = 5000

# цвета
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)

# инициализация
pygame.init()
pygame.mixer.init()
pygame.display.set_caption("Уличные разборки")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# шрифты
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
large_font = pygame.font.Font(None, 72)

# загрузка ассетов
def load_frames(sheet, frame_width, frame_height, frame_count, row, scale_factor):
    frames = []
    for i in range(frame_count):
        frame = sheet.subsurface(
            i * frame_width, row * frame_height, 
            frame_width, frame_height
        )
        frame = pygame.transform.scale(
            frame, 
            (frame_width * scale_factor, frame_height * scale_factor)
        )
        frames.append(frame)
    return frames

game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, 'sprites')
sound_folder = os.path.join(game_folder, 'sounds')

pygame.mixer.music.load(os.path.join(sound_folder, 'music.mp3'))
pygame.mixer.music.set_volume(0.3)
levelup = pygame.mixer.Sound(os.path.join(sound_folder, 'levelup.mp3'))
player_hit = pygame.mixer.Sound(os.path.join(sound_folder, 'player_hit.mp3'))
enemy_hit1 = pygame.mixer.Sound(os.path.join(sound_folder, 'enemy_hit1.mp3'))
enemy_hit2 = pygame.mixer.Sound(os.path.join(sound_folder, 'enemy_hit2.mp3'))
enemy_hit3 = pygame.mixer.Sound(os.path.join(sound_folder, 'enemy_hit3.mp3'))
enemy_hit4 = pygame.mixer.Sound(os.path.join(sound_folder, 'enemy_hit4.mp3'))

player_sprite = pygame.image.load(os.path.join(img_folder, 'hero_game.png')).convert_alpha()
enemy1_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_1.png')).convert_alpha()
enemy2_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_2.png')).convert_alpha()
enemy3_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_3.png')).convert_alpha()
enemy4_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_4.png')).convert_alpha()
enemy5_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_5.png')).convert_alpha()
ability_sheet = pygame.image.load(os.path.join(img_folder, 'abilities.png'))
projectile_sheet = pygame.image.load(os.path.join(img_folder, 'projectiles.png'))
background_texture = pygame.image.load(os.path.join(img_folder, 'texture2.jpg')).convert()
background_texture = pygame.transform.scale(background_texture, (100, 100))

player_walk = load_frames(player_sprite, 20, 20, 4, 1, 2.5)
player_idle = load_frames(player_sprite, 20, 20, 4, 0, 2.5)
enemy1 = load_frames(enemy1_sprite, 20, 20, 4, 0, 2.5)
enemy2 = load_frames(enemy2_sprite, 20, 20, 4, 0, 2.5)
enemy3 = load_frames(enemy3_sprite, 20, 20, 4, 0, 2.5)
enemy4 = load_frames(enemy4_sprite, 20, 20, 4, 0, 2.5)
enemy5 = load_frames(enemy5_sprite, 20, 20, 4, 0, 2.5)

ability_sprites = load_frames(ability_sheet, 32, 32, 15, 0, 1)
projectile_sprites = load_frames(projectile_sheet, 32, 32, 6, 0, 2)

# отрисовка мира
world_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
for x in range(0, WORLD_WIDTH, background_texture.get_width()):
    for y in range(0, WORLD_HEIGHT, background_texture.get_height()):
        world_surface.blit(background_texture, (x, y))

# гейм менеджер
class Camera:
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
    
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)
    
    def update(self, target):
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)
        
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - WIDTH), x)
        y = max(-(self.height - HEIGHT), y)
        
        self.camera = pygame.Rect(x, y, self.width, self.height)

class Timer:
    def __init__(self):
        self.time = 0.0
        self.last_update_time = 0
        self.paused = False
        self.pause_start_time = 0
        self.paused_duration = 0.0
        
    def start(self):
        self.time = 0.0
        self.last_update_time = pygame.time.get_ticks()
        self.paused = False
        self.paused_duration = 0.0
        
    def update(self):
        if not self.paused:
            current_time = pygame.time.get_ticks()
            elapsed = (current_time - self.last_update_time) / 1000.0
            self.time += elapsed
            self.last_update_time = current_time
            
    def pause(self):
        if not self.paused:
            self.paused = True
            self.pause_start_time = pygame.time.get_ticks()
            
    def resume(self):
        if self.paused:
            self.paused = False
            pause_end_time = pygame.time.get_ticks()
            elapsed_pause = (pause_end_time - self.pause_start_time) / 1000.0
            self.paused_duration += elapsed_pause
            self.last_update_time = pause_end_time
            
    def reset(self):
        self.start()

class Spawner:
    def __init__(self, timer, camera, player, group, items):
        self.timer = timer
        self.camera = camera
        self.player = player
        self.group = group
        self.items = items
        self.next_spawn = 0
        self.spawn_distance = 50
        self.side = 0
        self.next_perimeter_spawn = 60
    
    def spawn(self):
        type = random.randint(1,5)
        health = random.randint(1,2) + self.timer.time // 25
        damage = 1 + self.timer.time // 60
        speed = 0.75 + random.uniform(-0.25, 0.25)
        exp = random.randint(1, 3) + self.timer.time // 30

        count = 1 + random.randint(0, int(self.timer.time // 25)%15)

        cam_left = -self.camera.camera.x
        cam_top = -self.camera.camera.y
        cam_right = cam_left + WIDTH
        cam_bottom = cam_top + HEIGHT
        if self.side == 0:
            x = random.randint(cam_left, cam_right)
            y = cam_top - self.spawn_distance
        elif self.side == 1:
            x = cam_right + self.spawn_distance
            y = random.randint(cam_top, cam_bottom)
        elif self.side == 2:
            x = random.randint(cam_left, cam_right)
            y = cam_bottom + self.spawn_distance
        else:
            x = cam_left - self.spawn_distance
            y = random.randint(cam_top, cam_bottom)

        for i in range(count):
            Enemy(type, health, damage, speed, exp, self.player, x, y, self.group, self.items, self.timer)

        self.side = (self.side + 1) % 4

    def update(self):
        if self.timer.time >= self.next_spawn:
            self.next_spawn = self.timer.time + random.randint(1, 1 + int(self.timer.time//60)%2)
            self.spawn()

        if self.timer.time >= self.next_perimeter_spawn:
            self.next_perimeter_spawn = self.timer.time + 60  # Следующий спавн через 60 секунд
            self.spawn_perimeter()

    def spawn_perimeter(self):
        cam_left = -self.camera.camera.x
        cam_top = -self.camera.camera.y
        cam_right = cam_left + WIDTH
        cam_bottom = cam_top + HEIGHT
        
        count = 50
        
        for i in range(count):
            side = i % 4
            
            if side == 0:
                x = random.randint(cam_left, cam_right)
                y = cam_top - self.spawn_distance
            elif side == 1:
                x = cam_right + self.spawn_distance
                y = random.randint(cam_top, cam_bottom)
            elif side == 2:
                x = random.randint(cam_left, cam_right)
                y = cam_bottom + self.spawn_distance
            else:
                x = cam_left - self.spawn_distance
                y = random.randint(cam_top, cam_bottom)
            
            type = random.randint(1,5)
            health = random.randint(1,3) + self.timer.time // 25
            damage = 1 + self.timer.time // 60
            speed = 0.75 + random.uniform(-0.25, 0.25)
            exp = random.randint(1, 3) + self.timer.time // 20
            
            Enemy(type, health, damage, speed, exp, self.player, x, y, self.group, self.items, self.timer)

# ui
def draw_ui(screen, timer, player):
    seconds = int(timer.time // 1) % 60
    minutes = int(timer.time // 60)
    timer_text = f"{minutes:02}:{seconds:02}"
    timer_surface = font.render(timer_text, True, WHITE)
    timer_rect = timer_surface.get_rect(center=(WIDTH // 2, 20))
    screen.blit(timer_surface, timer_rect)
    
    health_text = font.render("Здоровье:", True, WHITE)
    screen.blit(health_text, (20, 20))
    pygame.draw.rect(screen, RED, (20, 60, 200, 20))
    health_width = int(200 * (player.current_health / player.max_health))
    pygame.draw.rect(screen, GREEN, (20, 60, health_width, 20))
    
    level_text = font.render(f"Уровень: {player.level}", True, WHITE)
    level_rect = level_text.get_rect(topright=(WIDTH - 20, 20))
    screen.blit(level_text, level_rect)
    pygame.draw.rect(screen, WHITE, (WIDTH - 220, 60, 200, 10))
    exp_width = int(200 * (player.exp / player.max_exp)) 
    pygame.draw.rect(screen, BLUE, (WIDTH - 220, 60, exp_width, 10))

def draw_upgrade_screen(screen, player):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    title = font.render("Выберите улучшение", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
    
    card_width = 250
    card_height = 300
    margin = 30
    start_x = (WIDTH - (3 * card_width + 2 * margin)) // 2
    
    for i, upgrade in enumerate(player.available_upgrades):
        x = start_x + i * (card_width + margin)
        y = HEIGHT // 2 - card_height // 2
        
        pygame.draw.rect(screen, GRAY, (x, y, card_width, card_height), border_radius=10)
        pygame.draw.rect(screen, LIGHT_GRAY, (x, y, card_width, card_height), 2, border_radius=10)
        
        sprite_rect = upgrade.sprite.get_rect(center=(x + card_width//2, y + 70))
        screen.blit(upgrade.sprite, sprite_rect)
        
        name = font.render(upgrade.name, True, WHITE)
        screen.blit(name, (x + card_width//2 - name.get_width()//2, y + 110))
        
        level = small_font.render(f"Уровень: {upgrade.level} -> {upgrade.level + 1}", True, WHITE)
        screen.blit(level, (x + card_width//2 - level.get_width()//2, y + 140))
        
        desc_lines = []
        words = upgrade.description.split()
        current_line = words[0]
        
        for word in words[1:]:
            test_line = current_line + " " + word
            if small_font.size(test_line)[0] < card_width - 20:
                current_line = test_line
            else:
                desc_lines.append(current_line)
                current_line = word
        desc_lines.append(current_line)
        
        for j, line in enumerate(desc_lines):
            desc = small_font.render(line, True, WHITE)
            screen.blit(desc, (x + card_width//2 - desc.get_width()//2, y + 170 + j * 25))
        
        key = font.render(str(i+1), True, WHITE)
        screen.blit(key, (x + card_width - 30, y + card_height - 30))

def draw_pause_screen(screen):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    pause_text = large_font.render("ПАУЗА", True, WHITE)
    screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2,HEIGHT//2 - pause_text.get_height()//2))

def draw_main_menu(screen):
    screen.fill(BLACK)
    
    title = large_font.render("Уличные разборки", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))
    
    start_text = font.render("Нажмите ПРОБЕЛ чтобы начать", True, WHITE)
    screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2))
    
    controls_text = small_font.render("Управление: WASD - движение, 1-3 - выбор улучшений", True, WHITE)
    screen.blit(controls_text, (WIDTH // 2 - controls_text.get_width() // 2, HEIGHT // 2 + 50))
    
    if not hasattr(draw_main_menu, 'falling_sprites'):
        draw_main_menu.falling_sprites = []
        draw_main_menu.last_spawn_time = pygame.time.get_ticks()
    
    current_time = pygame.time.get_ticks()
    
    if current_time - draw_main_menu.last_spawn_time > 500:
        if len(draw_main_menu.falling_sprites) < 10:
            sprite = random.choice(ability_sprites)
            new_sprite = {
                'sprite': sprite,
                'x': random.randint(0, WIDTH),
                'y': -50,
                'speed': random.uniform(1, 3),
                'angle': 0,
                'rotation_speed': random.uniform(-3, 3),
                'scale': random.uniform(0.5, 1.0)
            }
            draw_main_menu.falling_sprites.append(new_sprite)
        draw_main_menu.last_spawn_time = current_time
    
    for sprite_data in draw_main_menu.falling_sprites[:]:
        sprite_data['y'] += sprite_data['speed']
        sprite_data['angle'] += sprite_data['rotation_speed']
        
        if sprite_data['y'] > HEIGHT + 50:
            draw_main_menu.falling_sprites.remove(sprite_data)
            continue
        
        scaled_width = int(sprite_data['sprite'].get_width() * sprite_data['scale'])
        scaled_height = int(sprite_data['sprite'].get_height() * sprite_data['scale'])
        scaled_sprite = pygame.transform.scale(sprite_data['sprite'], (scaled_width, scaled_height))
        
        rotated_sprite = pygame.transform.rotate(scaled_sprite, sprite_data['angle'])
        
        screen.blit(
            rotated_sprite,
            (
                sprite_data['x'] - rotated_sprite.get_width() // 2,
                sprite_data['y'] - rotated_sprite.get_height() // 2
            )
        )
    
    pygame.display.flip()

def draw_game_over_screen(screen, timer, player):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    game_over = large_font.render("ИГРА ОКОНЧЕНА", True, RED)
    screen.blit(game_over, (WIDTH//2 - game_over.get_width()//2, HEIGHT//2 - 100))
    
    seconds = int(timer.time // 1) % 60
    minutes = int(timer.time // 60)
    time_text = f"Время выживания: {minutes:02}:{seconds:02}"
    time_surface = font.render(time_text, True, WHITE)
    screen.blit(time_surface, (WIDTH//2 - time_surface.get_width()//2, HEIGHT//2))
    
    level_text = font.render(f"Достигнутый уровень: {player.level}", True, WHITE)
    screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 + 50))
    
    restart_text = font.render("Нажмите ПРОБЕЛ чтобы начать заново", True, WHITE)
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 150))
    
    pygame.display.flip()

# сущности
class Enemy(pygame.sprite.Sprite):
    def __init__(self, type, health, damage, speed, exp, player, pos_x, pos_y, group, items, timer):
        pygame.sprite.Sprite.__init__(self, group)
        self.items = items
        self.player = player
        self.health = health
        self.damage = damage
        self.speed = speed
        self.exp = exp
        self.timer = timer

        self.couldown = 1000
        self.curent_couldown = pygame.time.get_ticks()

        if type == 1:
            self.walk_frames = enemy1
        elif type == 2:
            self.walk_frames = enemy2
        elif type == 3:
            self.walk_frames = enemy3
        elif type == 4:
            self.walk_frames = enemy4
        else:
            self.walk_frames = enemy5

        self.facing_right = True
        self.image = self.walk_frames[0]
        
        self.rect = self.image.get_rect().inflate(
            -int(self.image.get_width() / 3),
            -int(self.image.get_height() / 5)
        )
        self.rect.x = pos_x
        self.rect.y = pos_y
        
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        
        self.collision_radius = 25
        self.avoidance_radius = 60
        self.push_force = 0.8
        self.mass = 1.0
        self.velocity = pygame.math.Vector2(0, 0)

        self.attack_cooldown = 1
        self.last_attack_time = 0

        self.normal_image = None
        self.hit_cooldown = 0.3

    def take_damage(self, amount):
        self.health -= amount
        self.last_hit_time = self.timer.time

        if self.normal_image is None:
            self.normal_image = self.image.copy()
        
        colored = self.normal_image.copy()
        colored.fill((255, 0, 0, 128), None, pygame.BLEND_RGBA_MULT)
        self.image = colored

    def update(self):
        self.handle_movement()
        self.handle_animation()
        
        if self.health <= 0:
            chance = random.random()
            if chance < 0.7:
                Exp(self.exp, self.rect.centerx, self.rect.centery, self.player, self.items)
            if chance > 0.985:
                Heal(random.randint(1,5), self.rect.centerx, self.rect.centery, self.player, self.items)
            self.kill()
        
        if self.normal_image and self.timer.time - self.last_hit_time > self.hit_cooldown:
            self.image = self.normal_image
            self.normal_image = None


    def handle_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > 100:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            self.image = self.walk_frames[self.current_frame]
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)

    def handle_movement(self):
        player_dir = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
        if player_dir.length() > 0:
            player_dir = player_dir.normalize()
        
        avoidance = pygame.math.Vector2(0, 0)
        for other in self.groups()[0].sprites():
            if other != self and isinstance(other, Enemy):
                dist = pygame.math.Vector2(other.rect.center).distance_to(self.rect.center)
                if dist < self.avoidance_radius:
                    diff = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(other.rect.center)
                    if diff.length() > 0:
                        avoidance += diff.normalize() * (1 - dist/self.avoidance_radius)
        
        move_force = player_dir * 0.8
        if avoidance.length() > 0:
            avoidance = avoidance.normalize() * 0.1
            move_force += avoidance
        
        self.velocity += move_force * 0.2
        self.velocity *= 0.8
        
        self.handle_collisions()
        
        min_speed = 0.3
        move_vector = player_dir * min_speed + self.velocity * self.speed
        
        self.rect.x += move_vector.x
        self.rect.y += move_vector.y
        
        if abs(move_vector.x) > 0.1:
            self.facing_right = move_vector.x > 0
        
        self.rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))

    def handle_collisions(self):
        if self.rect.colliderect(self.player.rect):
            self.resolve_collision(self.player)
            
            now = self.timer.time
            if now - self.last_attack_time > self.attack_cooldown:
                self.last_attack_time = now
                damage = max(1, self.damage - self.damage * self.player.armor/100)
                self.player.take_damage(damage)
        
        for other in self.groups()[0].sprites():
            if other != self and isinstance(other, Enemy) and self.rect.colliderect(other.rect):
                self.resolve_collision(other)

    def resolve_collision(self, other):
        direction = pygame.math.Vector2(other.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() == 0:
            direction = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        
        direction = direction.normalize()
        
        force = self.push_force
        if isinstance(other, Enemy):
            force = self.push_force * other.mass / (self.mass + other.mass)
        
        self.velocity -= direction * force
        if isinstance(other, Enemy):
            other.velocity += direction * force
            
class Player(pygame.sprite.Sprite):
    def __init__(self, group, timer):
        pygame.sprite.Sprite.__init__(self, group)
        self.timer = timer
        self.animation_speed = 0.2
        self.idle_frames = player_idle
        self.walk_frames = player_walk
        
        self.current_animation = self.idle_frames
        self.current_frame = 0
        self.animation_time = 0
        
        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect().inflate(
            -int(self.image.get_width() / 3),
            -int(self.image.get_height() / 5)
        )
        self.rect.center = (WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

        self.facing_right = True
        self.moving = False
        self.last_update = pygame.time.get_ticks()
        
        self.max_health = 15
        self.current_health = self.max_health
        self.speed = 1.5
        self.level = 1
        self.armor = 0
        self.critical_multiplier = 1.0
        self.critical_chance = 10.0
        self.abilities = [BrassKnuckles(self), AdidasJacket(self), Seeds(self), Bottle(self),
                          Knife(self), BubbleGum(self), Bite(self), Crowbar(self), GoldenKnife(self),
                          Phone(self), AdidasBoots(self), Cigarettes(self), Beer(self)]
        self.exp = 0
        self.max_exp = 15

        self.level_up_ready = False
        self.available_upgrades = []

        self.normal_image = None
        self.hit_cooldown = 0.3

    def take_damage(self, damage):
        self.current_health -= damage
        self.last_hit_time = self.timer.time
        player_hit.play()

        if self.normal_image is None:
            self.normal_image = self.image.copy()
        
        colored = self.normal_image.copy()
        colored.fill((255, 0, 0, 128), None, pygame.BLEND_RGBA_MULT)
        self.image = colored

    def select_random_upgrades(self):
        self.available_upgrades = random.sample(self.abilities, 3)

    def apply_upgrade(self, upgrade_index):
        if 0 <= upgrade_index < len(self.available_upgrades):
            self.available_upgrades[upgrade_index].level_up()
        self.level_up_ready = False
        self.available_upgrades = []
        global paused
        paused = False
        self.timer.resume()

    def level_up(self):
        self.level += 1
        self.exp = self.exp - self.max_exp
        self.max_exp += 15
        self.level_up_ready = True
        self.select_random_upgrades()
        global paused
        paused = True
        self.timer.pause()
        levelup.play()

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.moving = False
        if keys[pygame.K_w] and self.rect.y > 0:
            self.rect.y += -self.speed * 1.5
            self.moving = True
        if keys[pygame.K_s] and self.rect.y < WORLD_HEIGHT - self.rect.height:
            self.rect.y += self.speed
            self.moving = True
        if keys[pygame.K_a] and self.rect.x > 0:
            self.rect.x += -self.speed * 1.5
            self.facing_right = False
            self.moving = True
        if keys[pygame.K_d] and self.rect.x < WORLD_WIDTH - self.rect.width:
            self.rect.x += self.speed
            self.facing_right = True
            self.moving = True
    
    def update(self):
        self.handle_input()
        
        for ab in self.abilities:
            if ab.level != 0: ab.invoke()
        
        if self.moving:
            self.current_animation = self.walk_frames
        else:
            self.current_animation = self.idle_frames  
            
        now = pygame.time.get_ticks()
        if now - self.last_update > 100:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.current_animation)
            self.image = self.current_animation[self.current_frame]
            
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
        
        if self.exp >= self.max_exp:
            self.level_up()

        if self.current_health <= 0:
            self.kill()

# выпадения
class Exp(pygame.sprite.Sprite):
    def __init__(self, exp, pos_x, pos_y, player, group):
        super().__init__(group)
        self.exp = exp
        self.player = player

        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 0, 255), (4, 4), 4)
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

    def update(self):
        if self.rect.colliderect(self.player.rect):
            self.player.exp += self.exp
            self.kill()

class Heal(pygame.sprite.Sprite):
    def __init__(self, heal, pos_x, pos_y, player, group):
        super().__init__(group)
        self.heal = heal
        self.player = player

        self.image = ability_sprites[6]
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

    def update(self):
        if self.player and self.rect.colliderect(self.player.rect):
            if self.player.current_health + self.heal > self.player.max_health:
                self.player.current_health = self.player.max_health
            else:
                self.player.current_health += self.heal
            self.kill()

# способности
def calculate_damage(damage, crit_chance, crit_multiplier):
    if random.random() < crit_chance / 100:
        return damage + damage * crit_multiplier
    return damage

class Projectile(pygame.sprite.Sprite):
    def __init__(self, group, sprite, direction, damage, crit_chance, crit_multiplier, lifetime, pos_x, pos_y, enemies, speed, timer, single, multiplier = 0, sound = enemy_hit1):
        pygame.sprite.Sprite.__init__(self, group)
        self.image = sprite
        self.rect = self.image.get_rect().inflate(
            -int(self.image.get_width() * multiplier),
            -int(self.image.get_height() * multiplier)
        )
        self.rect.centerx = pos_x
        self.rect.centery = pos_y
        self.single = single
        self.sound = sound
        
        self.timer = timer
        self.enemies = enemies

        self.start = timer.time
        self.life = lifetime
        self.speed = speed

        self.damage = damage
        self.crit_chance = crit_chance
        self.crit_multiplier = crit_multiplier
        self.direction = direction
        self.damaged = set()

    def update(self):
        self.move()

        for enemy in self.enemies:
            if isinstance(enemy, Enemy) and self.rect.colliderect(enemy.rect) and (not enemy in self.damaged):
                self.damaged.add(enemy)
                enemy.take_damage(calculate_damage(self.damage, self.crit_chance, self.crit_multiplier))
                self.sound.play()
                if self.single:
                    self.kill()
        
        if (self.timer.time > self.start + self.life):
            self.kill()

    def move(self):
        if self.direction != (0, 0):
            dx, dy = self.direction
            length = (dx ** 2 + dy ** 2) ** 0.5
            if length > 0:
                norm_dx = dx / length
                norm_dy = dy / length
            else:
                norm_dx, norm_dy = 0, 0
        else:
            norm_dx, norm_dy = 0, 0

        self.rect.x += norm_dx * self.speed
        self.rect.y += norm_dy * self.speed

class Ability:
    def __init__(self, player, name, description, sprite):
        self.level = 0
        self.player = player
        self.name = name
        self.description = description
        self.sprite = sprite

    def level_up(self):
        self.level += 1

    def invoke(self):
        pass

class BrassKnuckles(Ability):
    def __init__(self, player):
        super().__init__(player, "Кастет", "Увеличивает шанс критического удара", ability_sprites[0])

    def level_up(self):
        super().level_up()
        self.player.critical_chance += 5

class AdidasJacket(Ability):
    def __init__(self, player):
        super().__init__(player,"Куртка адидас","Увеличивает броню",ability_sprites[1])
        self.const = 25

    def level_up(self):
        super().level_up()
        self.player.armor += self.const / self.level

class Seeds(Ability):
    def __init__(self, player):
        super().__init__(player, "Семечки", "Выстреливает семечками вокруг", ability_sprites[2])
        self.damage = 2
        self.cooldown = 3
        self.last_shot_time = -self.cooldown
        self.projectile_speed = 5
        self.lifetime = 0.6
        self.base_sprite = projectile_sprites[1]
        
    def level_up(self):
        super().level_up()
        self.damage += 3
        if self.level % 2 == 0:
            self.cooldown -= 0.2
            self.cooldown = max(0.5, self.cooldown)
    
    def invoke(self):
        current_time = self.player.timer.time
        
        if current_time - self.last_shot_time >= self.cooldown:
            angles = [0, 60, 120, 180, 240, 300]
            
            for angle in angles:
                angle_rad = math.radians(angle)
                
                direction = (math.sin(angle_rad), -math.cos(angle_rad))
                
                Projectile(
                    group=projectiles,
                    sprite=self.get_rotated_sprite(angle),
                    direction=direction,
                    damage=self.damage,
                    crit_chance=self.player.critical_chance,
                    crit_multiplier=self.player.critical_multiplier,
                    lifetime=self.lifetime,
                    pos_x=self.player.rect.centerx,
                    pos_y=self.player.rect.centery,
                    enemies=entity,
                    speed=self.projectile_speed,
                    timer=self.player.timer,
                    single=True,
                    multiplier= 0.5,
                    sound = enemy_hit2
                )
            
            self.last_shot_time = current_time
    
    def get_rotated_sprite(self, angle):
        rotated_sprite = pygame.transform.rotate(self.base_sprite, angle)
        return rotated_sprite

class Bottle(Ability):
    def __init__(self, player):
        super().__init__(player, "Бутылка", "Увеличивает критический урон", ability_sprites[3])

    def level_up(self):
        super().level_up()
        self.player.critical_multiplier += 0.3

class Knife(Ability):
    def __init__(self, player):
        super().__init__(player, "Нож", "Метает нож в ближайшего врага", ability_sprites[4])
        self.damage = 3
        self.cooldown = 2
        self.last_shot_time = -self.cooldown
        self.projectile_speed = 8
        self.lifetime = 1.5
        self.base_sprite = ability_sprites[4]
        
    def level_up(self):
        super().level_up()
        self.damage += 3
        if self.level % 3 == 0:
            self.cooldown -= 0.3
            self.cooldown = max(0.3, self.cooldown)
    
    def invoke(self):
        current_time = self.player.timer.time
        
        if current_time - self.last_shot_time >= self.cooldown:
            nearest_enemy = self.find_nearest_enemy()
            
            if nearest_enemy:
                dx = nearest_enemy.rect.centerx - self.player.rect.centerx
                dy = nearest_enemy.rect.centery - self.player.rect.centery
                
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > 0:
                    direction = (dx/distance, dy/distance)
                else:
                    direction = (0, 1)
                
                angle = math.degrees(math.atan2(-dy, dx)) + 225
                
                rotated_sprite = pygame.transform.rotate(self.base_sprite, angle)
                
                Projectile(
                    group=projectiles,
                    sprite=rotated_sprite,
                    direction=direction,
                    damage=self.damage,
                    crit_chance=self.player.critical_chance,
                    crit_multiplier=self.player.critical_multiplier,
                    lifetime=self.lifetime,
                    pos_x=self.player.rect.centerx,
                    pos_y=self.player.rect.centery,
                    enemies=entity,
                    speed=self.projectile_speed,
                    timer=self.player.timer,
                    single=True,
                    sound = enemy_hit2
                )
                
                self.last_shot_time = current_time
    
    def find_nearest_enemy(self):
        nearest_enemy = None
        min_distance = float('inf')
        
        for enemy in entity:
            if isinstance(enemy, Enemy):
                dx = enemy.rect.centerx - self.player.rect.centerx
                dy = enemy.rect.centery - self.player.rect.centery
                distance = dx*dx + dy*dy
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = enemy
        
        return nearest_enemy

class BubbleGum(Ability):
    def __init__(self, player):
        super().__init__(player, "Жвачка", "Выплевывает жвачку в случайном направлении", ability_sprites[5])
        self.damage = 2
        self.cooldown = 3
        self.last_shot_time = -self.cooldown
        self.projectile_speed = 5
        self.lifetime = 1.5
        
    def level_up(self):
        super().level_up()
        self.damage += 2
        if self.level % 2 == 0:
            self.cooldown -= 0.5
            self.cooldown = max(1.0, self.cooldown)
    
    def invoke(self):
        current_time = self.player.timer.time
        
        if current_time - self.last_shot_time >= self.cooldown:
            angle = random.uniform(0, 2 * math.pi)
            direction = (math.cos(angle), math.sin(angle))
            
            sprite_angle = math.degrees(angle) - 90
            rotated_sprite = pygame.transform.rotate(projectile_sprites[2], sprite_angle)
            
            Projectile(
                group=projectiles,
                sprite=rotated_sprite,
                direction=direction,
                damage=self.damage,
                crit_chance=self.player.critical_chance,
                crit_multiplier=self.player.critical_multiplier,
                lifetime=self.lifetime,
                pos_x=self.player.rect.centerx,
                pos_y=self.player.rect.centery,
                enemies=entity,
                speed=self.projectile_speed,
                timer=self.player.timer,
                single=False,
                sound = enemy_hit3
            )
            
            self.last_shot_time = current_time

class BiteProjectile(Projectile):
    def __init__(self, group, player, radius, angle, rotation_speed, damage, crit_chance, crit_multiplier, lifetime, enemies, timer):
        super().__init__(
            group=group,
            sprite=ability_sprites[7],
            direction=(0, 0),
            damage=damage,
            crit_chance=crit_chance,
            crit_multiplier=crit_multiplier,
            lifetime=lifetime,
            pos_x=player.rect.centerx,
            pos_y=player.rect.centery,
            enemies=enemies,
            speed=0,
            timer=timer,
            single=False
        )
        self.player = player
        self.radius = radius
        self.angle = angle
        self.rotation_speed = rotation_speed
        self.self_rotation = 0
        self.self_rotation_speed = 10
        
    def move(self):
        self.angle += self.rotation_speed
        if self.angle >= 360:
            self.angle -= 360
            
        offset_x = self.radius * math.cos(math.radians(self.angle))
        offset_y = self.radius * math.sin(math.radians(self.angle))
        self.rect.centerx = self.player.rect.centerx + offset_x
        self.rect.centery = self.player.rect.centery + offset_y
        
        self.self_rotation += self.self_rotation_speed
        if self.self_rotation >= 360:
            self.self_rotation -= 360
        self.image = pygame.transform.rotate(ability_sprites[7], self.self_rotation)

class Bite(Ability):
    def __init__(self, player):
        super().__init__(player, "Бита", "Крутится вокруг игрока, нанося урон", ability_sprites[7])
        self.damage = 2
        self.cooldown = 3
        self.last_shot_time = -self.cooldown
        self.radius = 120
        self.rotation_speed = 3
        self.lifetime = 2
        self.max_projectiles = 3

        
    def level_up(self):
        super().level_up()
        self.damage += 2
        if self.level % 3 == 0:
            self.max_projectiles += 1
        if self.level % 2 == 0:
            self.rotation_speed += 1
            self.lifetime += 1
    
    def invoke(self):
        current_time = self.player.timer.time
        
        if (current_time - self.last_shot_time >= self.cooldown and 
            len([p for p in projectiles if isinstance(p, BiteProjectile)]) < self.max_projectiles):
            
            start_angle = random.randint(0, 359)
            BiteProjectile(
                group=projectiles,
                player=self.player,
                radius=self.radius,
                angle=start_angle,
                rotation_speed=self.rotation_speed,
                damage=self.damage,
                crit_chance=self.player.critical_chance,
                crit_multiplier=self.player.critical_multiplier,
                lifetime=self.lifetime,
                enemies=entity,
                timer=self.player.timer
            )
            
            self.last_shot_time = current_time

class Crowbar(Ability):
    def __init__(self, player):
        super().__init__(player, "Лом", "Атакует горизонтально", ability_sprites[9])
        self.damage = 2
        self.projectiles = 1
        self.cooldown = 1.5
        self.current_cooldown = 0
        self.last_shot_time = 0
        self.shot_delay = 0.2
        self.shots_fired = 0
        self.projectile_sprite = pygame.transform.scale(
            projectile_sprites[0],
            (projectile_sprites[0].get_width(),
            int(projectile_sprites[0].get_height() * 1.3)
        ))
        self.level = 1

    def level_up(self):
        super().level_up()
        self.damage += 2
        if self.level % 3 == 0:
            self.projectiles += 1
    
    def invoke(self):
        current_time = self.player.timer.time
        if current_time - self.last_shot_time >= self.cooldown:
            if self.shots_fired == 0 or (current_time - self.current_cooldown >= self.shot_delay):
                self.fire_projectile()
                self.current_cooldown = current_time
                self.shots_fired += 1
                
                if self.shots_fired >= self.projectiles:
                    self.last_shot_time = current_time
                    self.shots_fired = 0

    def fire_projectile(self):
        if self.player.facing_right:
            base_sprite = self.projectile_sprite
        else:
            base_sprite = pygame.transform.flip(self.projectile_sprite, True, False)
        
        if self.shots_fired % 2 == 0:
            direction = (1 if self.player.facing_right else -1, 0)
            sprite = base_sprite
        else:
            direction = (-1 if self.player.facing_right else 1, 0)
            sprite = pygame.transform.flip(base_sprite, True, False)
        
        Projectile(
            group=projectiles,
            sprite=sprite,
            direction=direction,
            damage=self.damage,
            crit_chance=self.player.critical_chance,
            crit_multiplier=self.player.critical_multiplier,
            lifetime=0.3,
            pos_x=self.player.rect.centerx,
            pos_y=self.player.rect.centery,
            enemies=entity,
            speed=10,
            timer=self.player.timer,
            single=False
        )

class LightningEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, group, timer):
        super().__init__(group)
        self.timer = timer
        self.start_time = timer.time
        self.lifetime = 0.3
        
        self.image = pygame.Surface((40, 60), pygame.SRCALPHA)
        pygame.draw.line(self.image, (255, 255, 100), (20, 0), (10, 20), 3)
        pygame.draw.line(self.image, (255, 255, 0), (10, 20), (30, 30), 3)
        pygame.draw.line(self.image, (255, 200, 0), (30, 30), (15, 50), 3)
        pygame.draw.line(self.image, (255, 150, 0), (15, 50), (25, 60), 3)
        
        self.rect = self.image.get_rect(center=(x, y))
    
    def update(self):
        if self.timer.time > self.start_time + self.lifetime:
            self.kill()

class Phone(Ability):
    def __init__(self, player):
        super().__init__(player, "Мобильный", "Бьет током случайных врагов", ability_sprites[10])
        self.damage = 3
        self.cooldown = 5
        self.last_shot_time = -self.cooldown
        self.max_targets = 2
        self.range = 300
        
    def level_up(self):
        super().level_up()
        self.damage += 3
        if self.level % 2 == 0:
            self.max_targets += 1
        if self.level % 3 == 0:
            self.range += 50
    
    def invoke(self):
        current_time = self.player.timer.time
        enemy_hit4.play()
        
        if current_time - self.last_shot_time >= self.cooldown:
            enemies_in_range = []
            for enemy in entity:
                if isinstance(enemy, Enemy):
                    distance = math.sqrt((enemy.rect.centerx - self.player.rect.centerx)**2 + 
                                  (enemy.rect.centery - self.player.rect.centery)**2)
                    if distance <= self.range:
                        enemies_in_range.append(enemy)
            
            targets = random.sample(enemies_in_range, min(self.max_targets, len(enemies_in_range)))
            
            for target in targets:
                target.take_damage(calculate_damage(self.damage, self.player.critical_chance, self.player.critical_multiplier))
                
                LightningEffect(target.rect.centerx, target.rect.centery, projectiles, self.player.timer)
            
            self.last_shot_time = current_time

class GoldenKnifeProjectile(Projectile):
    def __init__(self, group, sprite, direction, damage, crit_chance, crit_multiplier, lifetime, pos_x, pos_y, enemies, speed, timer):
        super().__init__(
            group=group,
            sprite=sprite,
            direction=direction,
            damage=damage,
            crit_chance=crit_chance,
            crit_multiplier=crit_multiplier,
            lifetime=lifetime,
            pos_x=pos_x,
            pos_y=pos_y,
            enemies=enemies,
            speed=speed,
            timer=timer,
            single=False,
            sound = enemy_hit2
        )
        self.bounce_count = 0
        self.max_bounces = 2 + self.damage // 3
    
    def update(self):
        self.move()
        
        for enemy in self.enemies:
            if isinstance(enemy, Enemy) and (enemy not in self.damaged) and self.rect.colliderect(enemy.rect):
                enemy.take_damage(calculate_damage(self.damage, self.crit_chance, self.crit_multiplier))
                self.damaged.add(enemy)
                self.sound.play()
                
                if self.bounce_count < self.max_bounces:
                    self.bounce_count += 1
                    self.find_new_target()
                else:
                    self.kill()
                break
        
        if self.timer.time > self.start + self.life:
            self.kill()
    
    def find_new_target(self):
        possible_target = None
        for i in self.enemies:
            if isinstance(i, Enemy) and i not in self.damaged:
                possible_target = i
                break
        
        if possible_target:  
            dx = possible_target.rect.centerx - self.rect.centerx
            dy = possible_target.rect.centery - self.rect.centery
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0:
                self.direction = (dx/dist, dy/dist)
            
            angle = math.degrees(math.atan2(-self.direction[1], self.direction[0])) + 225
            self.image = pygame.transform.rotate(ability_sprites[11], angle)
            self.rect = self.image.get_rect(center=self.rect.center)


class GoldenKnife(Ability):
    def __init__(self, player):
        super().__init__(player, "Золотой нож", "Метает отскакивающий нож", ability_sprites[11])
        self.damage = 3
        self.cooldown = 4
        self.last_use_time = -self.cooldown
        self.projectile_speed = 8
        self.lifetime = 3
    
    def level_up(self):
        super().level_up()
        self.damage += 2
        if self.level % 2 == 0:
            self.cooldown -= 0.3
    
    def invoke(self):
        current_time = self.player.timer.time
        
        if current_time - self.last_use_time >= self.cooldown:
            nearest_enemy = self.find_nearest_enemy()
            
            if nearest_enemy:
                dx = nearest_enemy.rect.centerx - self.player.rect.centerx
                dy = nearest_enemy.rect.centery - self.player.rect.centery
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist > 0:
                    direction = (dx/dist, dy/dist)
                else:
                    direction = (0, 1)
                
                angle = math.degrees(math.atan2(-direction[1], direction[0])) + 225
                rotated_sprite = pygame.transform.rotate(ability_sprites[11], angle)
                
                GoldenKnifeProjectile(
                    group=projectiles,
                    sprite=rotated_sprite,
                    direction=direction,
                    damage=self.damage,
                    crit_chance=self.player.critical_chance,
                    crit_multiplier=self.player.critical_multiplier,
                    lifetime=self.lifetime,
                    pos_x=self.player.rect.centerx,
                    pos_y=self.player.rect.centery,
                    enemies=entity,
                    speed=self.projectile_speed,
                    timer=self.player.timer
                )
                
                self.last_use_time = current_time
    
    def find_nearest_enemy(self):
        nearest = None
        min_dist = float('inf')
        
        for enemy in entity:
            if isinstance(enemy, Enemy):
                dx = enemy.rect.centerx - self.player.rect.centerx
                dy = enemy.rect.centery - self.player.rect.centery
                dist_sq = dx*dx + dy*dy
                
                if dist_sq < min_dist:
                    min_dist = dist_sq
                    nearest = enemy
        return nearest

class BeerPuddle(pygame.sprite.Sprite):
    def __init__(self, x, y, size, damage, crit_chance, crit_multiplier, timer, enemies, group):
        super().__init__(group)
        self.timer = timer
        self.enemies = enemies
        self.spawn_time = timer.time
        self.lifetime = 5
        self.damage = damage
        self.crit_chance = crit_chance
        self.crit_multiplier = crit_multiplier
        self.last_damage_time = 0
        self.damage_interval = 1
        
        self.base_image = projectile_sprites[5]
        self.image = pygame.transform.scale(
            self.base_image, 
            (int(self.base_image.get_width() * size), 
            int(self.base_image.get_height() * size))
        )
        self.rect = self.image.get_rect(center=(x, y))
        
        self.hitbox = self.rect.inflate(-20, -20)
    
    def update(self):
        current_time = self.timer.time
        
        if current_time > self.spawn_time + self.lifetime:
            self.kill()
            return
        
        if current_time - self.last_damage_time >= self.damage_interval:
            self.last_damage_time = current_time
            self.apply_damage()
    
    def apply_damage(self):
        for enemy in self.enemies:
            if isinstance(enemy, Enemy) and self.hitbox.colliderect(enemy.rect):
                enemy.take_damage(calculate_damage(self.damage, self.crit_chance, self.crit_multiplier))

class Beer(Ability):
    def __init__(self, player):
        super().__init__(player, "Вредное пойло", "Создает области урона", ability_sprites[12])
        self.damage = 2
        self.cooldown = 4
        self.last_use_time = -self.cooldown
        self.max_puddles = 3
    
    def level_up(self):
        super().level_up()
        self.damage += 2
        if self.level % 2 == 0:
            self.max_puddles += 1
        if self.level % 3 == 0:
            self.cooldown -= 0.5
    
    def invoke(self):
        current_time = self.player.timer.time
        
        if (current_time - self.last_use_time >= self.cooldown and 
            len([p for p in projectiles if isinstance(p, BeerPuddle)]) < self.max_puddles):
            
            cam_left = -camera.camera.x
            cam_top = -camera.camera.y
            cam_right = cam_left + WIDTH
            cam_bottom = cam_top + HEIGHT
            
            x = random.randint(cam_left + 100, cam_right - 100)
            y = random.randint(cam_top + 100, cam_bottom - 100)
            
            size = 1.0 + self.level * 0.2
            
            BeerPuddle(
                x=x,
                y=y,
                size=size,
                damage=self.damage,
                crit_chance=self.player.critical_chance,
                crit_multiplier=self.player.critical_multiplier,
                timer=self.player.timer,
                enemies=entity,
                group=projectiles
            )
            
            self.last_use_time = current_time

class AdidasBoots(Ability):
    def __init__(self, player):
        super().__init__(player, "Ботинки адидас", "Увеличивают скорость", ability_sprites[13])

    def level_up(self):
        super().level_up()
        self.player.speed += 0.2

class Cigarettes(Ability):
    def __init__(self, player):
        super().__init__(player, "Сигареты", "Увеличивает максимальное здоровье", ability_sprites[14])

    def level_up(self):
        super().level_up()
        self.player.max_health += 5

def reset_game():
    # Очищаем все группы спрайтов
    entity.empty()
    items.empty()
    projectiles.empty()
    
    # Сбрасываем таймер
    timer.reset()
    
    # Создаем нового игрока
    player = Player(entity, timer)
    
    # Пересоздаем спавнер
    spawner = Spawner(timer, camera, player, entity, items)
    
    return player, spawner

# Игровой цикл
def main():
    global entity, items, projectiles, camera, timer, player, spawner, paused, running
    
    # Инициализация
    entity = pygame.sprite.Group()
    items = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()

    camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
    timer = Timer()
    timer.start()   
    player = Player(entity, timer)
    spawner = Spawner(timer, camera, player, entity, items)
    
    # Состояния игры
    game_state = "menu"  # menu, game, game_over
    running = True
    paused = False
    
    while running:
        clock.tick(FPS)
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                # Обработка паузы и выбора улучшений
                if game_state == "game":
                    if event.key == pygame.K_SPACE and not player.level_up_ready:
                        if paused: 
                            paused = False
                            timer.resume()
                            pygame.mixer.music.unpause()
                        else: 
                            paused = True
                            timer.pause()
                            pygame.mixer.music.pause()
                    
                    if player.level_up_ready and paused:
                        if event.key == pygame.K_1:
                            player.apply_upgrade(0)
                        elif event.key == pygame.K_2:
                            player.apply_upgrade(1)
                        elif event.key == pygame.K_3:
                            player.apply_upgrade(2)
                
                # Обработка меню и рестарта
                elif event.key == pygame.K_SPACE:
                    if game_state == "menu":
                        game_state = "game"
                        timer.start()
                        pygame.mixer.music.play(-1)
                    elif game_state == "game_over":
                        player, spawner = reset_game()
                        game_state = "game"
                        timer.start()
                        pygame.mixer.music.play(-1)
        
        if game_state == "menu":
            draw_main_menu(screen)
        elif game_state == "game":
            timer.update()
            if not paused:
                entity.update()
                items.update()
                projectiles.update()
                camera.update(player)
                spawner.update()

            if player.current_health <= 0:
                game_state = "game_over"
                timer.pause()
                pygame.mixer.music.stop()
            screen.blit(world_surface, (camera.camera.x, camera.camera.y))
            
            for item in items:
                screen.blit(item.image, (item.rect.x + camera.camera.x, item.rect.y + camera.camera.y))
            for sprite in entity:
                screen.blit(sprite.image, (sprite.rect.x + camera.camera.x, sprite.rect.y + camera.camera.y))
            for projectile in projectiles:
                screen.blit(projectile.image, (projectile.rect.x + camera.camera.x, projectile.rect.y + camera.camera.y))

            draw_ui(screen, timer, player)
            
            if player.level_up_ready and paused:
                draw_upgrade_screen(screen, player)
            elif not player.level_up_ready and paused:
                draw_pause_screen(screen)
        elif game_state == "game_over":
            draw_game_over_screen(screen, timer, player)
        
        pygame.display.flip()

if __name__ == "__main__":
    main()
    pygame.quit()