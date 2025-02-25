import os
import pygame

pygame.init()
pygame.font.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
HAMSTER_SIZE = 50
MAX_LEVEL = 5
PUZZLES_PER_LEVEL = 10

SAVE_FILE = os.path.join(BASE_DIR, 'save_game.json')

COLORS = {
    'sky_blue': (135, 206, 235),
    'grass_green': (34, 139, 34),
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'pink': (255, 182, 193),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'blue': (0, 0, 255),
    'lightgray': (200, 200, 200)
}

PUZZLE_BUTTON_RECT = pygame.Rect(SCREEN_WIDTH // 2 - 75, SCREEN_HEIGHT // 2 - 25, 150, 50)
