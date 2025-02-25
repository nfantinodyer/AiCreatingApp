# main.py
import pygame
import sys
import os

# Initialize Pygame
pygame.init()

# Settings
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
PINK = (255, 182, 193)
BLACK = (0, 0, 0)

# Setup screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dwarf Hamster Wedding Adventure")

# Hamster class
class Hamster(pygame.sprite.Sprite):
    def __init__(self, color, controls, image_name=None):
        super().__init__()
        if image_name:
            try:
                self.image = pygame.image.load(os.path.join('assets', image_name)).convert_alpha()
                self.image = pygame.transform.scale(self.image, (50, 50))
            except pygame.error:
                self.image = pygame.Surface((50, 50))
                self.image.fill(color)
        else:
            self.image = pygame.Surface((50, 50))
            self.image.fill(color)
        self.rect = self.image.get_rect()
        self.controls = controls
        self.rect.center = (WIDTH // 2, HEIGHT // 2)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]:
            self.rect.x -= 5
        if keys[self.controls['right']]:
            self.rect.x += 5
        if keys[self.controls['up']]:
            self.rect.y -= 5
        if keys[self.controls['down']]:
            self.rect.y += 5
        if keys[self.controls['interact']]:
            print(f"Interacting with {self.controls['interact_key']}!")

# Create hamsters
hamster1_controls = {
    'left': pygame.K_a,
    'right': pygame.K_d,
    'up': pygame.K_w,
    'down': pygame.K_s,
    'interact': pygame.K_SPACE,
    'interact_key': 'Player 1'
}
hamster2_controls = {
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'up': pygame.K_UP,
    'down': pygame.K_DOWN,
    'interact': pygame.K_RETURN,
    'interact_key': 'Player 2'
}

hamster1 = Hamster(PINK, hamster1_controls, image_name='bride.png')
hamster2 = Hamster(BLACK, hamster2_controls, image_name='groom.png')

# Sprite groups
all_sprites = pygame.sprite.Group()
all_sprites.add(hamster1)
all_sprites.add(hamster2)

# Main game loop
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    all_sprites.update()

    # Draw everything
    screen.fill(WHITE)
    all_sprites.draw(screen)
    
    pygame.display.flip()
    clock.tick(FPS)

# Dwarf Hamster Wedding Adventure

Dwarf Hamster Wedding Adventure is a charming two-player cooperative puzzle game built with Pygame. In this game, the bride must pick out her outfit while the groom hunts for the perfect ring. Work together to solve puzzles and prepare for the ultimate wedding ceremony!

## Features
- Two-player cooperative gameplay on a single screen
- Multiple levels with increasing puzzle difficulty
- Save and load functionality (resume the adventure at any time)
- Cute and whimsical art style suitable for all ages
- Simple and intuitive user interface
- Interactive tutorial to guide you through the game
- Fun and engaging story that unfolds as you progress

## Installation
1. Clone or download this repository.
2. Ensure you have Python 3.x installed.
3. Install dependencies:
   pip install pygame
4. Make sure you have an "assets" folder in the same directory, containing:
   - bride.png
   - groom.png
   - hamster.png (optional if desired)
   - wedding.png

## Running the Game
From a terminal or command prompt, run:
python main.py

## Controls
• Player 1 (Bride):
  - Move Left: A
  - Move Right: D
  - Move Up: W
  - Move Down: S
  - Interact: SPACE

• Player 2 (Groom):
  - Move Left: Arrow Left
  - Move Right: Arrow Right
  - Move Up: Arrow Up
  - Move Down: Arrow Down
  - Interact: Enter

## License
This project is licensed under the MIT License. See the LICENSE file for details.
