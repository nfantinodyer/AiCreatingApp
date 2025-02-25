import pygame
import os
from config import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, PUZZLE_BUTTON_RECT, ASSETS_DIR

class GameVisuals:
    """
    Class to handle primary game visual elements throughout the adventure.
    """

    @staticmethod
    def draw_background(surface):
        """Draw the game background (sky and grass)."""
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
    def draw_level_complete(surface, level_text):
        """Draw level complete message with instruction to continue."""
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
        """Draw the final wedding scene with text and optional wedding image."""
        surface.fill(COLORS['white'])
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render("Final Wedding Ceremony!", True, COLORS['blue'])
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        surface.blit(text_surface, text_rect)

        wedding_image_path = os.path.join(ASSETS_DIR, 'wedding.png')
        if os.path.exists(wedding_image_path):
            try:
                wedding_image = pygame.image.load(wedding_image_path).convert_alpha()
                wedding_image = pygame.transform.scale(wedding_image, (300, 300))
                surface.blit(wedding_image, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
            except pygame.error as e:
                print(f"Error loading wedding image: {e}. Using fallback circle.")
                pygame.draw.circle(surface, COLORS['pink'], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)
        else:
            pygame.draw.circle(surface, COLORS['pink'], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)

    @staticmethod
    def draw_game_over(surface):
        """Draw the Game Over message."""
        font = pygame.font.SysFont(None, 48)
        game_over_surface = font.render("Game Over! Press R to Restart or Q to Quit.", True, COLORS['red'])
        rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(game_over_surface, rect)

    @staticmethod
    def draw_level_complete_message(surface, message):
        """
        Draw a more general 'level completed' text with instructions.
        This can be an alternative to draw_level_complete if custom text is needed.
        """
        font = pygame.font.SysFont(None, 48)
        text = font.render(message, True, COLORS['black'])
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text, rect)
        instructions = pygame.font.SysFont(None, 36).render(
            "Press SPACE to continue to the next level.", True, COLORS['black']
        )
        surface.blit(
            instructions,
            (SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT // 2 + 50)
        )
