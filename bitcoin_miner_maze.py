#!/usr/bin/env python3
"""
Bitcoin Miner - Maze Collection Game
Collect all coins, then touch the wallet to win!
Ghost catches you or you hit a wall = back to start.
"""

import pygame
import random
import os
import sys

pygame.init()
pygame.mixer.init()

# =============================================================================
# SCREEN SETUP
# =============================================================================
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Bitcoin Miner - Collect & Deposit!")
clock = pygame.time.Clock()

# =============================================================================
# ASSET LOADING (searches multiple paths)
# =============================================================================

def find_asset_dir():
    possible_paths = [
        "/mnt/agents/upload",
        os.path.expanduser("~/bitcoin_miner_assets"),
        os.path.expanduser("~/.bitcoin_miner"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
        os.path.dirname(os.path.abspath(__file__)),
        ".",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            for f in ["miner.png", "bitcoin.png", "ghost.png", "background.jpg"]:
                if os.path.exists(os.path.join(path, f)):
                    print(f"Assets found in: {path}")
                    return path
    return None

ASSET_DIR = find_asset_dir()

def load_image(filename, scale=None):
    if ASSET_DIR:
        path = os.path.join(ASSET_DIR, filename)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                if scale:
                    img = pygame.transform.scale(img, scale)
                return img
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    placeholder = pygame.Surface(scale if scale else (50, 50), pygame.SRCALPHA)
    colors = {
        "miner": (255, 165, 0),
        "bitcoin": (255, 215, 0),
        "dollar": (0, 255, 100),
        "ghost": (0, 200, 200),
        "background": (30, 30, 60),
        "wallet": (139, 69, 19),
    }
    color = (255, 0, 255)
    for key, c in colors.items():
        if key in filename.lower():
            color = c
            break
    placeholder.fill(color)
    pygame.draw.rect(placeholder, (255, 255, 255), placeholder.get_rect(), 2)
    return placeholder

def load_sound(filename):
    if ASSET_DIR:
        path = os.path.join(ASSET_DIR, filename)
        if os.path.exists(path):
            try:
                return pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Error loading sound {filename}: {e}")
    return None

# Load assets
background_img = load_image("background.jpg", (SCREEN_WIDTH, SCREEN_HEIGHT))
miner_img = load_image("miner.png", (40, 40))
bitcoin_img = load_image("bitcoin.png", (28, 28))
dollar_img = load_image("dollar.png", (28, 28))
ghost_img = load_image("ghost.png", (40, 40))

coin_sound = load_sound("coin_drop.mp3")
win_sound = load_sound("win.wav")
lose_sound = load_sound("lose.wav")

try:
    if ASSET_DIR and os.path.exists(os.path.join(ASSET_DIR, "cave.mp3")):
        pygame.mixer.music.load(os.path.join(ASSET_DIR, "cave.mp3"))
except:
    pass

# =============================================================================
# FONTS
# =============================================================================
font_large = pygame.font.Font(None, 64)
font_medium = pygame.font.Font(None, 36)
font_small = pygame.font.Font(None, 28)

# =============================================================================
# GAME CLASSES
# =============================================================================

class Player(pygame.sprite.Sprite):
    def __init__(self, start_pos):
        super().__init__()
        self.image = miner_img
        self.rect = self.image.get_rect(center=start_pos)
        self.start_pos = start_pos
        self.speed = 4
        self.coins_held = 0
        self.invincible = False
        self.invincible_timer = 0

    def respawn(self):
        self.rect.center = self.start_pos
        self.invincible = True
        self.invincible_timer = 60  # 1 second invincibility
        if lose_sound:
            lose_sound.play()

    def update(self, keys, walls):
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed

        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Try X movement
        old_x = self.rect.x
        self.rect.x += dx
        if self.check_wall_collision(walls):
            self.rect.x = old_x
            if not self.invincible:
                self.respawn()
                return

        # Try Y movement
        old_y = self.rect.y
        self.rect.y += dy
        if self.check_wall_collision(walls):
            self.rect.y = old_y
            if not self.invincible:
                self.respawn()
                return

        # Keep on screen
        self.rect.clamp_ip(screen.get_rect())

        # Invincibility countdown
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def check_wall_collision(self, walls):
        for wall in walls:
            if self.rect.colliderect(wall):
                return True
        return False

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, walls):
        super().__init__()
        self.image = ghost_img
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 2.5
        self.walls = walls
        self.wobble = random.uniform(0, 6.28)

    def update(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = (dx**2 + dy**2) ** 0.5

        if dist > 0:
            dx = (dx / dist) * self.speed
            dy = (dy / dist) * self.speed

        self.wobble += 0.08
        dx += random.uniform(-0.5, 0.5)
        dy += random.uniform(-0.5, 0.5)

        new_rect = self.rect.copy()
        new_rect.x += dx
        if not self.check_wall_collision(new_rect):
            self.rect.x += dx

        new_rect = self.rect.copy()
        new_rect.y += dy
        if not self.check_wall_collision(new_rect):
            self.rect.y += dy

        self.rect.clamp_ip(screen.get_rect())

    def check_wall_collision(self, rect):
        for wall in self.walls:
            if rect.colliderect(wall):
                return True
        return False

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y, coin_type="bitcoin"):
        super().__init__()
        self.coin_type = coin_type
        self.image = bitcoin_img if coin_type == "bitcoin" else dollar_img
        self.rect = self.image.get_rect(center=(x, y))
        self.float_offset = random.uniform(0, 6.28)
        self.base_y = y

    def update(self):
        self.float_offset += 0.06
        self.rect.y = self.base_y + int(6 * __import__("math").sin(self.float_offset))

class Wallet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((60, 60), pygame.SRCALPHA)
        # Draw wallet icon
        pygame.draw.rect(self.image, (139, 69, 19), (5, 15, 50, 40), border_radius=5)
        pygame.draw.rect(self.image, (160, 82, 45), (5, 15, 50, 40), border_radius=5)
        pygame.draw.rect(self.image, (100, 50, 20), (5, 15, 50, 40), 2, border_radius=5)
        # B symbol
        font = pygame.font.Font(None, 36)
        b_text = font.render("B", True, (255, 215, 0))
        b_rect = b_text.get_rect(center=(30, 35))
        self.image.blit(b_text, b_rect)
        self.rect = self.image.get_rect(center=(x, y))
        self.pulse = 0

    def update(self):
        self.pulse += 0.1

    def draw_glow(self, surface):
        glow_size = 80 + int(10 * __import__("math").sin(self.pulse))
        glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 215, 0, 50), (glow_size//2, glow_size//2), glow_size//2)
        glow_rect = glow.get_rect(center=self.rect.center)
        surface.blit(glow, glow_rect)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.life = 30
        self.color = color
        self.size = random.randint(3, 6)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size = max(1, self.size - 0.1)

    def draw(self, surface):
        alpha = int(255 * (self.life / 30))
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

# =============================================================================
# WALL GENERATION
# =============================================================================

def generate_walls():
    """Generate maze-like walls."""
    walls = []
    wall_thickness = 20

    # Border walls
    walls.append(pygame.Rect(0, 0, SCREEN_WIDTH, wall_thickness))  # Top
    walls.append(pygame.Rect(0, SCREEN_HEIGHT - wall_thickness, SCREEN_WIDTH, wall_thickness))  # Bottom
    walls.append(pygame.Rect(0, 0, wall_thickness, SCREEN_HEIGHT))  # Left
    walls.append(pygame.Rect(SCREEN_WIDTH - wall_thickness, 0, wall_thickness, SCREEN_HEIGHT))  # Right

    # Inner walls - create a simple maze layout
    inner_walls = [
        # Horizontal walls
        (200, 150, 300, wall_thickness),
        (600, 250, 250, wall_thickness),
        (150, 400, 350, wall_thickness),
        (650, 500, 200, wall_thickness),
        (100, 600, 250, wall_thickness),
        (500, 350, 200, wall_thickness),
        (800, 100, 150, wall_thickness),

        # Vertical walls
        (300, 150, wall_thickness, 200),
        (500, 50, wall_thickness, 200),
        (700, 250, wall_thickness, 200),
        (200, 400, wall_thickness, 200),
        (450, 350, wall_thickness, 250),
        (800, 400, wall_thickness, 200),
        (100, 200, wall_thickness, 200),
        (900, 500, wall_thickness, 200),
    ]

    for x, y, w, h in inner_walls:
        walls.append(pygame.Rect(x, y, w, h))

    return walls

def spawn_coins(walls, count=10):
    """Spawn coins in valid positions (not inside walls)."""
    coins = []
    margin = 60
    attempts = 0

    while len(coins) < count and attempts < 200:
        x = random.randint(margin, SCREEN_WIDTH - margin)
        y = random.randint(margin, SCREEN_HEIGHT - margin)
        test_rect = pygame.Rect(x - 15, y - 15, 30, 30)

        valid = True
        for wall in walls:
            if test_rect.colliderect(wall):
                valid = False
                break

        if valid:
            coin_type = random.choice(["bitcoin", "dollar"])
            coins.append(Coin(x, y, coin_type))
        attempts += 1

    return coins

def find_valid_position(walls, margin=80):
    """Find a position not inside any wall."""
    attempts = 0
    while attempts < 200:
        x = random.randint(margin, SCREEN_WIDTH - margin)
        y = random.randint(margin, SCREEN_HEIGHT - margin)
        test_rect = pygame.Rect(x - 25, y - 25, 50, 50)

        valid = True
        for wall in walls:
            if test_rect.colliderect(wall):
                valid = False
                break

        if valid:
            return (x, y)
        attempts += 1
    return (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

# =============================================================================
# DRAWING HELPERS
# =============================================================================

def draw_text(surface, text, font, color, x, y, center=True):
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
    return text_rect

def draw_walls(surface, walls):
    for wall in walls:
        pygame.draw.rect(surface, (80, 60, 40), wall)
        pygame.draw.rect(surface, (120, 90, 60), wall, 2)

# =============================================================================
# SCREENS
# =============================================================================

def show_title_screen():
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    waiting = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

        screen.blit(background_img, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        screen.blit(overlay, (0, 0))

        draw_text(screen, "BITCOIN MINER", font_large, (255, 215, 0), SCREEN_WIDTH//2, 200)
        draw_text(screen, "Collect all coins, then deposit in the wallet!", font_medium, (255, 255, 255), SCREEN_WIDTH//2, 290)
        draw_text(screen, "Arrow Keys or WASD to move", font_small, (200, 200, 200), SCREEN_WIDTH//2, 360)
        draw_text(screen, "Avoid the ghost and walls!", font_small, (255, 100, 100), SCREEN_WIDTH//2, 390)
        draw_text(screen, "Press SPACE or CLICK to start", font_medium, (0, 255, 150), SCREEN_WIDTH//2, 470)

        pygame.display.flip()
        clock.tick(FPS)

def show_win_screen(score):
    if win_sound:
        win_sound.play()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return True
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                return True

        screen.blit(background_img, (0, 0))

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        screen.blit(overlay, (0, 0))

        draw_text(screen, "YOU WIN!", font_large, (0, 255, 100), SCREEN_WIDTH//2, 250)
        draw_text(screen, f"Final Score: {score}", font_medium, (255, 215, 0), SCREEN_WIDTH//2, 330)
        draw_text(screen, "All coins deposited!", font_medium, (255, 255, 255), SCREEN_WIDTH//2, 370)
        draw_text(screen, "Press SPACE to play again", font_medium, (0, 255, 150), SCREEN_WIDTH//2, 450)
        draw_text(screen, "Press ESC to quit", font_small, (150, 150, 150), SCREEN_WIDTH//2, 500)

        pygame.display.flip()
        clock.tick(FPS)

# =============================================================================
# MAIN GAME
# =============================================================================

def main_game():
    walls = generate_walls()

    # Find valid start position
    start_pos = find_valid_position(walls)
    player = Player(start_pos)

    # Spawn coins
    coins = spawn_coins(walls, 10)

    # Spawn ghost
    ghost_pos = find_valid_position(walls)
    while abs(ghost_pos[0] - start_pos[0]) < 200 and abs(ghost_pos[1] - start_pos[1]) < 200:
        ghost_pos = find_valid_position(walls)
    ghost = Ghost(ghost_pos[0], ghost_pos[1], walls)

    # Wallet position
    wallet_pos = find_valid_position(walls)
    wallet = Wallet(wallet_pos[0], wallet_pos[1])

    particles = []
    score = 0
    game_won = False

    # Start music
    try:
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(0.3)
    except:
        pass

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    return False

        keys = pygame.key.get_pressed()
        player.update(keys, walls)
        ghost.update(player)
        wallet.update()

        # Update coins
        for coin in coins:
            coin.update()

        # Check coin collection
        for coin in coins[:]:
            if player.rect.colliderect(coin.rect):
                coins.remove(coin)
                player.coins_held += 1
                score += 100

                # Spawn particles
                for _ in range(8):
                    color = (255, 215, 0) if coin.coin_type == "bitcoin" else (0, 255, 100)
                    particles.append(Particle(coin.rect.centerx, coin.rect.centery, color))

                if coin_sound:
                    coin_sound.play()

        # Check ghost collision
        if not player.invincible and player.rect.colliderect(ghost.rect):
            player.respawn()
            score = max(0, score - 50)

        # Check wallet interaction
        if len(coins) == 0 and player.rect.colliderect(wallet.rect):
            score += player.coins_held * 200
            player.coins_held = 0
            game_won = True

        # Update particles
        for p in particles[:]:
            p.update()
            if p.life <= 0:
                particles.remove(p)

        # DRAWING
        screen.blit(background_img, (0, 0))

        draw_walls(screen, walls)

        # Draw wallet with glow if all coins collected
        if len(coins) == 0:
            wallet.draw_glow(screen)
        wallet.update()
        screen.blit(wallet.image, wallet.rect)

        for coin in coins:
            screen.blit(coin.image, coin.rect)

        screen.blit(ghost.image, ghost.rect)

        # Draw player (flash if invincible)
        if not player.invincible or (player.invincible_timer // 5) % 2 == 0:
            screen.blit(player.image, player.rect)

        for p in particles:
            p.draw(screen)

        # HUD
        draw_text(screen, f"Coins Held: {player.coins_held}", font_small, (255, 215, 0), 20, 20, center=False)
        draw_text(screen, f"Remaining: {len(coins)}", font_small, (255, 255, 255), 20, 50, center=False)
        draw_text(screen, f"Score: {score}", font_small, (0, 255, 150), 20, 80, center=False)

        if len(coins) == 0:
            draw_text(screen, "DEPOSIT IN WALLET!", font_medium, (255, 215, 0), SCREEN_WIDTH//2, 100)

        if game_won:
            return show_win_screen(score)

        pygame.display.flip()
        clock.tick(FPS)

    return False

def main():
    print("=" * 50)
    print("  BITCOIN MINER - MAZE COLLECTION")
    print("=" * 50)
    print("Goal: Collect all coins, then touch the wallet to win!")
    print("Avoid walls and the ghost (they send you back to start)")
    print("=" * 50)

    if not ASSET_DIR:
        print("WARNING: Asset directory not found!")
        print("Place images in same folder as script or ~/bitcoin_miner_assets/")

    show_title_screen()

    playing = True
    while playing:
        playing = main_game()

    pygame.quit()
    print("Thanks for playing!")

if __name__ == "__main__":
    main()
