import pygame
import os
import sys

# Constants
ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BACKGROUND_COLOR = (255, 255, 255)  # White
COLORS = {
    'HAMSTER': (150, 75, 0),  # Brown
    'white': (255, 255, 255),
    'black': (0, 0, 0)
}
HAMSTER_COLOR = COLORS['HAMSTER']
HAMSTER_SIZE = 50
CONTROLS = {
    'left': pygame.K_LEFT,
    'right': pygame.K_RIGHT,
    'up': pygame.K_UP,
    'down': pygame.K_DOWN
}

def load_image(image_name, size=HAMSTER_SIZE, fallback_color=COLORS['white']):
    """
    Load an image from the assets directory or create a fallback shape.
    """
    if image_name:
        image_path = os.path.join(ASSETS_DIR, image_name)
        if os.path.exists(image_path):
            try:
                image = pygame.image.load(image_path).convert_alpha()
                image = pygame.transform.scale(image, (size, size))
                return image
            except pygame.error as e:
                print(f"Error loading image {image_name}: {e}")
    # Fallback circle
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surface, fallback_color, (size // 2, size // 2), size // 2)
    return surface

class Hamster(pygame.sprite.Sprite):
    """
    Represents a hamster character controlled by a player.
    """
    def __init__(self, x, y, color, controls, image_name=None):
        super().__init__()
        self.controls = controls
        self.velocity = 5
        self.image = load_image(image_name, size=HAMSTER_SIZE, fallback_color=color)
        self.rect = self.image.get_rect(center=(x, y))

    def handle_keys(self):
        """Update position based on pressed keys."""
        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]:
            self.rect.x -= self.velocity
        if keys[self.controls['right']]:
            self.rect.x += self.velocity
        if keys[self.controls['up']]:
            self.rect.y -= self.velocity
        if keys[self.controls['down']]:
            self.rect.y += self.velocity
        # Clamping to screen
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def update(self):
        """Update the hamster state each frame."""
        self.handle_keys()

    def draw(self, surface):
        """Draw the hamster to the screen."""
        surface.blit(self.image, self.rect.topleft)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamster Game")
    clock = pygame.time.Clock()

    hamster = Hamster(
        x=SCREEN_WIDTH // 2,
        y=SCREEN_HEIGHT // 2,
        color=HAMSTER_COLOR,
        controls=CONTROLS,
        image_name='hamster.png'
    )
    all_sprites = pygame.sprite.Group()
    all_sprites.add(hamster)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        all_sprites.update()

        screen.fill(BACKGROUND_COLOR)
        all_sprites.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
