import os
import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, ASSETS_DIR

class GameVisuals:
    @staticmethod
    def draw_background(surface):
        surface.fill(COLORS['sky_blue'])
        pygame.draw.rect(surface, COLORS['grass_green'], (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))

    @staticmethod
    def draw_puzzle_button(surface, rect, text='Puzzle'):
        pygame.draw.rect(surface, COLORS['green'], rect)
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(text, True, COLORS['white'])
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    @staticmethod
    def draw_level_complete(surface, level_text):
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render(level_text, True, COLORS['black'])
        rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text_surface, rect)
        instructions = pygame.font.SysFont(None, 36).render("Press SPACE to continue.", True, COLORS['black'])
        instr_rect = instructions.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        surface.blit(instructions, instr_rect)

    @staticmethod
    def draw_game_over(surface):
        font = pygame.font.SysFont(None, 48)
        game_over_surface = font.render("Game Over! Press R to Restart or Q to Quit.", True, COLORS['red'])
        rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(game_over_surface, rect)

    @staticmethod
    def draw_final_wedding_scene(surface):
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
