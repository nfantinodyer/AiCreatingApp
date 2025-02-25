import pygame
import os

# Initialize Pygame
pygame.init()
pygame.font.init()

# Global constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
HAMSTER_SIZE = 50  # Constant for hamster size
PUZZLE_BUTTON_RECT = pygame.Rect(375, 275, 150, 50)  # Consistent puzzle button position
COLORS = {
    'sky_blue': (135, 206, 235),  # Sky blue
    'grass_green': (34, 139, 34),  # Grass color
    'green': (0, 255, 0),  # Green for puzzle button
    'gold': (255, 215, 0),  # Gold color for button
    'black': (0, 0, 0),  # Black text
    'red': (255, 0, 0),  # Red color for text
    'pink': (255, 182, 193),  # Softer pink for bride hamster
    'white': (255, 255, 255),  # White color
    'light_gray': (200, 200, 200),  # Light gray for background
    'blue': (0, 0, 255),  # Blue for button
}

ASSETS_DIR = os.path.join(os.path.dirname(__file__), 'assets')


def load_image(image_path, size=HAMSTER_SIZE, fallback_color=COLORS['white']):
    """
    Load an image from the assets directory, or create a fallback shape if not found.
    """
    if image_path:
        full_path = os.path.join(ASSETS_DIR, image_path)
        if os.path.exists(full_path):
            try:
                image = pygame.image.load(full_path).convert_alpha()
                image = pygame.transform.scale(image, (size, size))
                return image
            except pygame.error as e:
                print(f"Error loading image at {full_path}: {e}. Using fallback circle.")
    # Fallback: draw a colored circle on a transparent surface
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surface, fallback_color, (size // 2, size // 2), size // 2)
    return surface


class Hamster:
    """
    A simpler hamster class (not sprite-based) for demonstration in art_style module.
    """
    def __init__(self, x, y, color, image_path=None):
        self.color = color
        self.rect = pygame.Rect(x - HAMSTER_SIZE // 2, y - HAMSTER_SIZE // 2, HAMSTER_SIZE, HAMSTER_SIZE)
        self.image = load_image(image_path, size=HAMSTER_SIZE, fallback_color=self.color)

    def draw(self, surface):
        """Draw the hamster on the specified surface."""
        surface.blit(self.image, self.rect.topleft)


class GameVisuals:
    """
    Class to manage game drawing and scene transitions (art style showcase).
    """
    @staticmethod
    def draw_background(surface):
        """Fill the background with sky blue and draw grass at the bottom."""
        surface.fill(COLORS['sky_blue'])
        pygame.draw.rect(surface, COLORS['grass_green'], (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))

    @staticmethod
    def draw_puzzle_button(surface, rect=PUZZLE_BUTTON_RECT, text='Puzzle'):
        """Draw a puzzle interaction button."""
        pygame.draw.rect(surface, COLORS['green'], rect)
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(text, True, COLORS['white'])
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    @staticmethod
    def draw_hamster_wedding(surface):
        """Draw a title text for the hamster wedding scene."""
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render("Hamster Wedding!", True, COLORS['red'])
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(text_surface, text_rect)

    @staticmethod
    def draw_game_over(surface):
        """Draw the Game Over message on the screen."""
        font = pygame.font.SysFont(None, 48)
        game_over_surface = font.render("Game Over! Press R to Restart or Q to Quit.", True, COLORS['red'])
        rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(game_over_surface, rect)

    @staticmethod
    def draw_level_complete(surface, level_text):
        """Draw level complete message."""
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render(level_text, True, COLORS['black'])
        rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text_surface, rect)
        instructions = pygame.font.SysFont(None, 36).render(
            "Press SPACE to continue to the next level.", True, COLORS['black']
        )
        surface.blit(
            instructions,
            (SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT // 2 + 50)
        )

    @staticmethod
    def draw_final_wedding_scene(surface):
        """Draw the final wedding scene."""
        surface.fill(COLORS['white'])
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render("Congratulations!", True, COLORS['red'])
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        surface.blit(text_surface, text_rect)

        wedding_image_path = os.path.join(ASSETS_DIR, 'wedding.png')
        if os.path.exists(wedding_image_path):
            try:
                wedding_image = pygame.image.load(wedding_image_path).convert_alpha()
                wedding_image = pygame.transform.scale(wedding_image, (300, 300))
                surface.blit(wedding_image, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 150))
            except pygame.error as e:
                print(f"Error loading wedding image: {e}. Using fallback circle.")
                pygame.draw.circle(surface, COLORS['pink'], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)
        else:
            pygame.draw.circle(surface, COLORS['pink'], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Dwarf Hamster Wedding Adventure')

    # Create hamsters
    bride_hamster = Hamster(400, 300, COLORS['pink'], image_path='bride.png')
    groom_hamster = Hamster(450, 300, COLORS['black'], image_path='groom.png')

    clock = pygame.time.Clock()
    running = True
    game_over = False
    level_complete = False
    level = 1
    final_scene = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        # Restart the game
                        game_over = False
                        level = 1
                        level_complete = False
                        bride_hamster = Hamster(400, 300, COLORS['pink'], image_path='bride.png')
                        groom_hamster = Hamster(450, 300, COLORS['black'], image_path='groom.png')
                        global HAMSTER_SIZE
                        HAMSTER_SIZE = 50
                    elif event.key == pygame.K_q:
                        running = False
                elif final_scene:
                    if event.key == pygame.K_q:
                        running = False
                elif level_complete:
                    if event.key == pygame.K_SPACE:
                        # Proceed to next level
                        level += 1
                        level_complete = False
                        HAMSTER_SIZE += 10
                        bride_hamster = Hamster(400, 300, COLORS['pink'], image_path='bride.png')
                        groom_hamster = Hamster(450, 300, COLORS['black'], image_path='groom.png')

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and not game_over and not level_complete and not final_scene:
                    if PUZZLE_BUTTON_RECT.collidepoint(event.pos):
                        # Example: Complete level when puzzle button is clicked
                        level_complete = True

        if not game_over and not level_complete and not final_scene:
            GameVisuals.draw_background(screen)
            bride_hamster.draw(screen)
            groom_hamster.draw(screen)
            GameVisuals.draw_puzzle_button(screen, PUZZLE_BUTTON_RECT)
            GameVisuals.draw_hamster_wedding(screen)
        elif level_complete:
            GameVisuals.draw_background(screen)
            GameVisuals.draw_level_complete(screen, f"Level {level} Complete!")
        elif final_scene:
            GameVisuals.draw_final_wedding_scene(screen)
        else:
            GameVisuals.draw_background(screen)
            GameVisuals.draw_game_over(screen)

        pygame.display.flip()
        clock.tick(60)

        # Example condition to trigger final scene after level 3
        if level > 3 and not final_scene and not game_over:
            final_scene = True

    pygame.quit()


if __name__ == "__main__":
    main()
