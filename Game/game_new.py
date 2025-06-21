import pygame
import os
import random

# глобальные переменные
WIDTH = 1000
HEIGHT = 600
FPS = 60
WORLD_WIDTH = 5000
WORLD_HEIGHT = 5000

WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 50, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)

# инициализация
pygame.init()
pygame.display.set_caption("Уличные разборки")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()

# загрузка ассетов
game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, 'sprites')
player_sprite = pygame.image.load(os.path.join(img_folder, 'hero_game.png')).convert_alpha()
enemy1_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_1.png')).convert_alpha()
enemy2_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_2.png')).convert_alpha()
enemy3_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_3.png')).convert_alpha()
enemy4_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_4.png')).convert_alpha()
enemy5_sprite = pygame.image.load(os.path.join(img_folder, 'enemy_5.png')).convert_alpha()
ability_sheet = pygame.image.load(os.path.join(img_folder, 'abilities.png')).convert_alpha()
projectile_sheet = pygame.image.load(os.path.join(img_folder, 'projectiles.png')).convert_alpha()
background_texture = pygame.image.load(os.path.join(img_folder, 'texture2.jpg')).convert()
background_texture = pygame.transform.scale(background_texture, (100, 100))
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)
large_font = pygame.font.Font(None, 72)

# камера
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

# Таймер
class Timer:
    def __init__(self):
        self.time = 0  # Текущее время в секундах
        self.last_update_time = 0  # Время последнего обновления
        self.paused = False  # Флаг паузы
        self.pause_start_time = 0  # Время начала паузы
        self.paused_duration = 0  # Общее время на паузе
        
    def start(self):
        self.last_update_time = pygame.time.get_ticks()
        
    def update(self):
        if not self.paused:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update_time >= 1000:
                self.time += 1
                self.last_update_time = current_time
                
    def pause(self):
        if not self.paused:
            self.paused = True
            self.pause_start_time = pygame.time.get_ticks()
            
    def resume(self):
        if self.paused:
            self.paused = False
            pause_end_time = pygame.time.get_ticks()
            self.paused_duration += pause_end_time - self.pause_start_time
            self.last_update_time += pause_end_time - self.pause_start_time
            
    def reset(self):
        self.time = 0
        self.last_update_time = pygame.time.get_ticks()
        self.paused_duration = 0
        self.paused = False  

# UI   
def draw_ui():
    # Таймер
    seconds = (timer.time) % 60
    minutes = (timer.time // 60)
    timer_text = f"{minutes:02}:{seconds:02}"
    timer_surface = font.render(timer_text, True, WHITE)
    timer_rect = timer_surface.get_rect(center=(WIDTH // 2, 20))
    screen.blit(timer_surface, timer_rect)
    
    # Здоровье
    health_text = font.render("Здоровье:", True, WHITE)
    screen.blit(health_text, (20, 20))
    pygame.draw.rect(screen, RED, (20, 60, 200, 20))
    health_width = int(200 * (player.current_health / player.max_health))
    pygame.draw.rect(screen, GREEN, (20, 60, health_width, 20))
    
    # Уровень
    level_text = font.render(f"Уровень: {player.level}", True, WHITE)
    level_rect = level_text.get_rect(topright=(WIDTH - 20, 20))
    screen.blit(level_text, level_rect)
    pygame.draw.rect(screen, WHITE, (WIDTH - 220, 60, 200, 10))
    exp_width = int(200 * (player.exp / player.max_exp)) 
    pygame.draw.rect(screen, BLUE, (WIDTH - 220, 60, exp_width, 10))

def draw_upgrade_screen():
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

def draw_pause_screen():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    pause_text = large_font.render("ПАУЗА", True, WHITE)
    screen.blit(pause_text, (WIDTH//2 - pause_text.get_width()//2, HEIGHT//2 - pause_text.get_height()//2))

# создание мира
world_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
for x in range(0, WORLD_WIDTH, background_texture.get_width()):
    for y in range(0, WORLD_HEIGHT, background_texture.get_height()):
        world_surface.blit(background_texture, (x, y))

# функция загрузки анимации
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

# игрок
class Player(pygame.sprite.Sprite):
    def __init__(self, group):
        pygame.sprite.Sprite.__init__(self, group)
        
        # Параметры спрайта
        self.animation_speed = 0.2
        self.idle_frames = load_frames(player_sprite, 20, 20, 4, 0, 2.5)
        self.walk_frames = load_frames(player_sprite, 20, 20, 4, 1, 2.5)
        
        self.current_animation = self.idle_frames
        self.current_frame = 0
        self.animation_time = 0
        
        self.image = self.idle_frames[0]
        self.rect = self.image.get_rect().inflate(
            -int(self.image.get_width() / 3),
            -int(self.image.get_height() / 5)
        )
        self.rect.center = (WORLD_WIDTH // 2, WORLD_HEIGHT // 2)

        self.direction = pygame.math.Vector2(0, 0)
        self.facing_right = True
        self.moving = False
        self.last_update = pygame.time.get_ticks()
        
        # Игровые параметры
        self.max_health = 20
        self.current_health = self.max_health
        self.speed = 2
        self.level = 1
        self.armor = 0
        self.critical_multiplier = 1.0
        self.critical_chance = 10.0
        self.abilities = [BrassKnuckles(self), AdidasJacket(self), Seeds(self), Bottle(self),
                          Knife(self), BubbleGum(self), Bite(self), Paper(self), Crowbar(self),
                          Phone(self), GoldenKnife(self), Beer(self), AdidasBoots(self), Cigarettes(self)]
        self.exp = 0
        self.max_exp = 20

        self.level_up_ready = False
        self.available_upgrades = []

    def select_random_upgrades(self):
        self.available_upgrades = random.sample(self.abilities, 3)

    def apply_upgrade(self, upgrade_index):
        if 0 <= upgrade_index < len(self.available_upgrades):
            self.available_upgrades[upgrade_index].level_up()
        self.level_up_ready = False
        self.available_upgrades = []
        global paused
        paused = False
        timer.resume()

    def level_up(self):
        self.level += 1
        self.exp = self.exp - self.max_exp
        self.max_exp += self.max_exp
        self.level_up_ready = True
        self.select_random_upgrades()
        global paused
        paused = True
        timer.pause()


    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        self.direction.x, self.direction.y = 0, 0
        self.moving = False
        
        if keys[pygame.K_a]:
            self.direction.x = -1
            self.facing_right = False
            self.moving = True
        if keys[pygame.K_d]:
            self.direction.x = 1
            self.facing_right = True
            self.moving = True
        if keys[pygame.K_w]:
            self.direction.y = -1
            self.moving = True
        if keys[pygame.K_s]:
            self.direction.y = 1
            self.moving = True
            
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()

    def update(self):
        self.handle_input()
        
        self.rect.x += self.direction.x * self.speed
        self.rect.y += self.direction.y * self.speed
        
        self.rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        
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

# способности игрока
ability_sprites = load_frames(ability_sheet, 32, 32, 15, 0, 1)
projectile_sprites = load_frames(projectile_sheet, 32, 32, 2, 0, 2)

def calculate_damage(damage, crit_chance, crit_multiplier):
    if random.random() < crit_chance / 100:
        return damage + damage * crit_multiplier
    return damage

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
        self.const = 15

    def level_up(self):
        super().level_up()
        self.player.armor += self.const / self.level

class Seeds(Ability):
    def __init__(self, player):
        super().__init__(player,"Семечки","Выстреливает семечками вокруг",ability_sprites[2])

        self.damage = 1
        self.couldown = 2
        self.radius = 100

    def level_up(self):
        super().level_up()
        self.damage += 1

class Bottle(Ability):
    def __init__(self, player):
        super().__init__(player, "Бутылка", "Увеличивает критический урон", ability_sprites[3])

    def level_up(self):
        super().level_up()
        self.player.critical_multiplier += 0.1

class Knife(Ability):
    def __init__(self, player):
        super().__init__(player,"Нож","Метает нож в ближайшего врага",ability_sprites[4])

class BubbleGum(Ability):
    def __init__(self, player):
        super().__init__(player,"Жвачка","Выплевывает жвачку, наносящую урон",ability_sprites[5])

class Bite(Ability):
    def __init__(self, player):
        super().__init__(player,"Бита","Наносит урон вокруг",ability_sprites[7])

class Paper(Ability):
    def __init__(self, player):
        super().__init__(player,"Важный документ","Дает временный барьер от урона",ability_sprites[8])

class Crowbar(Ability):
    def __init__(self, player):
        super().__init__(player,"Лом","Атакует врага в направлении взгляда",ability_sprites[9])
        self.level = 1

        self.damage = 3
        self.projectiles = 1
        self.couldown = 1500
        self.curent_couldown = pygame.time.get_ticks()

        self.attack_width = 200
        self.attack_height = 100

    def level_up(self):
        super().level_up()
        self.damage += 2
        if (self.level % 3):
            self.projectiles += 1
    
    def invoke(self):
        if pygame.time.get_ticks() > self.curent_couldown:
            self.curent_cooldown = pygame.time.get_ticks() + self.couldown

class Phone(Ability):
    def __init__(self, player):
        super().__init__(player,"Мобильный","Наносит урон вокруг",ability_sprites[10])

class GoldenKnife(Ability):
    def __init__(self, player):
        super().__init__(player,"Золотой нож","Метает отскакивающий ножь",ability_sprites[11])

class Beer(Ability):
    def __init__(self, player):
        super().__init__(player,"Пенное","Создает область урона",ability_sprites[12])

class AdidasBoots(Ability):
    def __init__(self, player):
        super().__init__(player, "Ботинки адидас", "Увеличивают скорость", ability_sprites[13])

    def level_up(self):
        super().level_up()
        self.player.speed += 1

class Cigarettes(Ability):
    def __init__(self, player):
        super().__init__(player, "Сигареты", "Увеличивает максимальное здоровье", ability_sprites[14])

    def level_up(self):
        super().level_up()
        self.player.max_health += 5

# Выпадение    
class Exp(pygame.sprite.Sprite):
    def __init__(self, exp, pos_x, pos_y, player, group):
        super().__init__(group)
        self.exp = exp
        self.player = player

        self.image = pygame.Surface((8, 8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 0, 255), (4, 4), 4)
        self.rect = self.image.get_rect(center=(pos_x, pos_y))

    def update(self):
        if self.player and self.rect.colliderect(self.player.rect):
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


# враги
class Enemy(pygame.sprite.Sprite):
    def __init__(self, type, health, damage, speed, exp, player, pos_x, pos_y, group):
        pygame.sprite.Sprite.__init__(self, group)
        
        self.player = player
        self.health = health
        self.damage = damage
        self.speed = speed
        self.exp = exp

        self.couldown = 1000
        self.curent_couldown = pygame.time.get_ticks()

        if type == 1:
            self.walk_frames = load_frames(enemy1_sprite, 20, 20, 4, 0, 2.5)
        elif type == 2:
            self.walk_frames = load_frames(enemy2_sprite, 20, 20, 4, 0, 2.5)
        elif type == 3:
            self.walk_frames = load_frames(enemy3_sprite, 20, 20, 4, 0, 2.5)
        elif type == 4:
            self.walk_frames = load_frames(enemy4_sprite, 20, 20, 4, 0, 2.5)
        else:
            self.walk_frames = load_frames(enemy5_sprite, 20, 20, 4, 0, 2.5)

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

    def update(self):
        self.move_to_player()

        now = pygame.time.get_ticks()
        if now - self.last_update > 100:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.walk_frames)
            self.image = self.walk_frames[self.current_frame]
            if not self.facing_right:
                self.image = pygame.transform.flip(self.image, True, False)
        
        if self.health < 0:
            self.kill()

    def move_to_player(self):
        direction = pygame.math.Vector2(self.player.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() > 0:
            direction = direction.normalize()
        
        self.facing_right = direction.x > 0
        
        self.rect.x += direction.x * self.speed
        self.handle_collisions('x')
        
        self.rect.y += direction.y * self.speed
        self.handle_collisions('y')

    def handle_collisions(self, axis):
        for other in self.groups()[0].sprites():
            if other != self and self.rect.colliderect(other.rect):
                if other == self.player and (pygame.time.get_ticks() > self.curent_couldown):
                    self.curent_couldown = pygame.time.get_ticks() + self.couldown
                    self.damage_player = False
                    self.player.current_health -= (self.damage - self.damage * self.player.armor/100) 
                if axis == 'x':
                    if self.rect.centerx > other.rect.centerx:
                        self.rect.left = other.rect.right
                    else:
                        self.rect.right = other.rect.left
                elif axis == 'y':
                    if self.rect.centery > other.rect.centery:
                        self.rect.top = other.rect.bottom
                    else:
                        self.rect.bottom = other.rect.top

# спавнер
class Spawner:
    def __init__(self):
        self.next_spawn = 0
        self.spawn_distance = 300

    
    def spawn(self):
        type = random.randint(1,5)
        health = random.randint(1,5) + timer.time // 60
        damage = 1 + timer.time // 60
        speed = 1.0 + random.uniform(-0.25, 0.25)
        exp = random.randint(1, 3) + timer.time // 60

        count = 1 + random.randint(0, (timer.time // 25)%15)

        side = random.randint(0, 3)
        cam_left = -camera.camera.x
        cam_top = -camera.camera.y
        cam_right = cam_left + WIDTH
        cam_bottom = cam_top + HEIGHT
        if side == 0:  # Верх
            x = random.randint(cam_left, cam_right)
            y = cam_top - self.spawn_distance
        elif side == 1:  # Право
            x = cam_right + self.spawn_distance
            y = random.randint(cam_top, cam_bottom)
        elif side == 2:  # Низ
            x = random.randint(cam_left, cam_right)
            y = cam_bottom + self.spawn_distance
        else:  # Лево
            x = cam_left - self.spawn_distance
            y = random.randint(cam_top, cam_bottom)

        for i in range(count):
            Enemy(type, health, damage, speed, exp, player, x, y, entity)

    def update(self):
        if timer.time >= self.next_spawn:
            self.next_spawn = timer.time + random.randint(1, 1 + (timer.time//60)%2)
            self.spawn()

    
# создание спрайтов
entity = pygame.sprite.Group()
items = pygame.sprite.Group()
player = Player(entity)
expi = Exp(20, player.rect.centerx+500, player.rect.centery, player, items)
heali = Heal(5, player.rect.centerx+500, player.rect.centery-100, player, items)

# Создаем камеру и таймер
camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
timer = Timer()
timer.start()   
spawner = Spawner()

# Игровой цикл
running = True
paused = False
while running:
    clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not player.level_up_ready:
                if (paused): 
                    paused = False
                    timer.resume()
                else: 
                    paused = True
                    timer.pause()
            
            if player.level_up_ready and paused:
                if event.key == pygame.K_1:
                    player.apply_upgrade(0)
                elif event.key == pygame.K_2:
                    player.apply_upgrade(1)
                elif event.key == pygame.K_3:
                    player.apply_upgrade(2)
    
    timer.update()
    if(not paused):
        entity.update()
        items.update()
        camera.update(player)
        spawner.update()
        
    screen.blit(world_surface, (camera.camera.x, camera.camera.y))
        
    for item in items:
        screen.blit(item.image, (item.rect.x + camera.camera.x, item.rect.y + camera.camera.y))
    for sprite in entity:
        screen.blit(sprite.image, (sprite.rect.x + camera.camera.x, sprite.rect.y + camera.camera.y))

    draw_ui()
    if (player.level_up_ready and paused):
            draw_upgrade_screen()
    if (not player.level_up_ready and paused):
        draw_pause_screen()
    pygame.display.flip()

pygame.quit()