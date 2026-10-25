"""Space Shooter - a simple pygame game (no image or sound files needed).

Install:  pip install pygame
Run:      python space_shooter.py

Controls: Arrow keys / WASD = move, SPACE = shoot (hold to auto-fire),
          R = restart after game over, ESC = quit
"""
import random
import sys

import pygame

WIDTH, HEIGHT, FPS = 800, 600, 60
WHITE, RED, GREEN, YELLOW, CYAN = (240, 240, 240), (230, 70, 70), (80, 220, 120), (250, 220, 70), (80, 200, 250)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)
big_font = pygame.font.SysFont("consolas", 56, bold=True)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((46, 40), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, CYAN, [(23, 0), (46, 40), (23, 30), (0, 40)])
        pygame.draw.polygon(self.image, WHITE, [(23, 8), (31, 30), (15, 30)])
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
        self.speed = 6
        self.last_shot = 0
        self.cooldown = 220  # ms between shots
        self.invincible_until = 0

    def update(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        self.rect.x += dx * self.speed
        self.rect.y += dy * self.speed
        self.rect.clamp_ip(screen.get_rect())
        # Blink while invincible after being hit
        self.image.set_alpha(120 if pygame.time.get_ticks() < self.invincible_until and
                             (pygame.time.get_ticks() // 100) % 2 else 255)

    def shoot(self, bullets, all_sprites):
        now = pygame.time.get_ticks()
        if now - self.last_shot >= self.cooldown:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            bullets.add(bullet)
            all_sprites.add(bullet)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 16))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(midbottom=(x, y))

    def update(self):
        self.rect.y -= 12
        if self.rect.bottom < 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, level):
        super().__init__()
        size = random.randint(30, 50)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, RED, [(0, 0), (size, 0), (size // 2, size)])
        pygame.draw.circle(self.image, WHITE, (size // 2, size // 3), size // 8)
        self.rect = self.image.get_rect(x=random.randint(0, WIDTH - size), y=-size)
        self.speed_y = random.uniform(2, 3.5) + level * 0.4
        self.speed_x = random.uniform(-1.5, 1.5)
        self.health = 1 + size // 45  # bigger enemies take 2 hits

    def update(self):
        self.rect.y += self.speed_y
        self.rect.x += self.speed_x
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.speed_x *= -1
        if self.rect.top > HEIGHT:
            self.kill()


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(random.choice([YELLOW, RED, WHITE]))
        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.math.Vector2(random.uniform(-4, 4), random.uniform(-4, 4))
        self.life = random.randint(15, 30)

    def update(self):
        self.rect.center += self.vel
        self.life -= 1
        if self.life <= 0:
            self.kill()


def draw_text(text, fnt, color, center):
    surf = fnt.render(text, True, color)
    screen.blit(surf, surf.get_rect(center=center))


def new_game():
    state = {
        "all": pygame.sprite.Group(), "enemies": pygame.sprite.Group(), "bullets": pygame.sprite.Group(),
        "score": 0, "lives": 3, "level": 1, "over": False,
    }
    state["player"] = Player()
    state["all"].add(state["player"])
    return state


def main():
    stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)] for _ in range(80)]
    g = new_game()
    SPAWN = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN, 800)

    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == SPAWN and not g["over"]:
                enemy = Enemy(g["level"])
                g["enemies"].add(enemy)
                g["all"].add(enemy)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r and g["over"]:
                g = new_game()

        if not g["over"]:
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                g["player"].shoot(g["bullets"], g["all"])
            g["all"].update()

            # Bullets vs enemies
            for enemy, hits in pygame.sprite.groupcollide(g["enemies"], g["bullets"], False, True).items():
                enemy.health -= len(hits)
                if enemy.health <= 0:
                    g["score"] += 10 * g["level"]
                    for _ in range(18):
                        g["all"].add(Particle(enemy.rect.center))
                    enemy.kill()

            # Enemies vs player
            if pygame.time.get_ticks() >= g["player"].invincible_until:
                if pygame.sprite.spritecollide(g["player"], g["enemies"], True):
                    g["lives"] -= 1
                    g["player"].invincible_until = pygame.time.get_ticks() + 1500
                    for _ in range(30):
                        g["all"].add(Particle(g["player"].rect.center))
                    if g["lives"] <= 0:
                        g["over"] = True
                        g["player"].kill()

            # Level up every 150 points, spawning faster
            new_level = g["score"] // 150 + 1
            if new_level != g["level"]:
                g["level"] = new_level
                pygame.time.set_timer(SPAWN, max(250, 800 - new_level * 70))

        # Drawing
        screen.fill((8, 8, 25))
        for star in stars:
            star[1] = (star[1] + star[2]) % HEIGHT
            pygame.draw.circle(screen, (150, 150, 190), (star[0], star[1]), 1 if star[2] < 3 else 2)
        g["all"].draw(screen)
        screen.blit(font.render(f"Score: {g['score']}", True, WHITE), (12, 10))
        screen.blit(font.render(f"Level: {g['level']}", True, WHITE), (12, 38))
        for i in range(g["lives"]):
            pygame.draw.polygon(screen, GREEN, [(WIDTH - 30 - i * 30, 12), (WIDTH - 15 - i * 30, 36), (WIDTH - 45 - i * 30, 36)])
        if g["over"]:
            draw_text("GAME OVER", big_font, RED, (WIDTH // 2, HEIGHT // 2 - 30))
            draw_text(f"Final score: {g['score']}   |   Press R to restart", font, WHITE, (WIDTH // 2, HEIGHT // 2 + 30))
        pygame.display.flip()


if __name__ == "__main__":
    main()
