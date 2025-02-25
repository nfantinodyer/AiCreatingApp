import pygame
import os

# Define colors
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'lightskyblue3': (145, 182, 255),
    'dodgerblue2': (28, 134, 238),
    'lightgray': (200, 200, 200),
    'blue': (0, 0, 255),
    'green': (0, 255, 0),
    'sky_blue': (135, 206, 235),
    'grass_green': (34, 139, 34),
    'pink': (255, 192, 203),
    'red': (255, 0, 0)
}

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PUZZLE_BUTTON_RECT = pygame.Rect(375, 275, 150, 50)
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

class GameVisuals:
    """Class to handle game visual elements."""
    
    @staticmethod
    def draw_background(surface):
        """Draw the game background."""
        surface.fill(COLORS['sky_blue'])  # Sky blue background
        pygame.draw.rect(surface, COLORS['grass_green'], (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))  # Grass

    @staticmethod
    def draw_puzzle_button(surface, rect, text='Puzzle'):
        """Draw the puzzle interaction button."""
        pygame.draw.rect(surface, COLORS['green'], rect)
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(text, True, COLORS['white'])
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)

    @staticmethod
    def draw_level_complete(surface, level_text):
        """Draw level complete message."""
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render(level_text, True, COLORS['black'])
        rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(text_surface, rect)

        instructions = pygame.font.SysFont(None, 36).render("Press SPACE to continue to the next level.", True, COLORS['black'])
        surface.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

    @staticmethod
    def draw_final_wedding_scene(surface):
        """Draw the final wedding scene."""
        surface.fill(COLORS['white'])
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render("Congratulations!", True, COLORS['red'])
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        surface.blit(text_surface, text_rect)

        wedding_image_path = os.path.join(ASSETS_DIR, 'wedding.png')  # Correctly set the path
        if os.path.exists(wedding_image_path):
            try:
                wedding_image = pygame.image.load(wedding_image_path).convert_alpha()
                wedding_image = pygame.transform.scale(wedding_image, (300, 300))
                surface.blit(wedding_image, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 150))
            except pygame.error:
                pygame.draw.circle(surface, COLORS['pink'], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)
        else:
            pygame.draw.circle(surface, COLORS['pink'], (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), 150)

    @staticmethod
    def draw_game_over(surface):
        """Draw the Game Over message on the screen."""
        font = pygame.font.SysFont(None, 48)
        game_over_surface = font.render("Game Over! Press R to Restart or Q to Quit.", True, COLORS['red'])
        rect = game_over_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        surface.blit(game_over_surface, rect)

class UI:
    """
    Handles user interface elements like input prompts and short messages.
    """
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 36)
        self.active = False
        self.input_text = ''
        self.prompt = ''
        self.message = ''
        self.message_timer = 0
        self.input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 50, 300, 40)
        self.color_active = COLORS['lightgray']
        self.show_input = False

    def display_message(self, message, duration=2000):
        """Display a transient message for the specified duration in ms."""
        self.message = message
        self.message_timer = pygame.time.get_ticks() + duration

    def activate_input(self, prompt):
        """Activate text input mode with a prompt."""
        self.active = True
        self.input_text = ''
        self.prompt = prompt
        self.show_input = True

    def get_input_event(self, event):
        """
        Process keyboard events; if the user presses Enter, return the typed text.
        Otherwise, handle backspaces and character inputs.
        """
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                result = self.input_text
                self.active = False
                self.show_input = False
                return result
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif len(self.input_text) < 50 and event.unicode.isprintable():
                self.input_text += event.unicode
        return None

    def draw(self, surface):
        """Draw any active message or input prompt on the screen."""
        current_time = pygame.time.get_ticks()
        if self.message and current_time > self.message_timer:
            self.message = ''

        # Draw message
        if self.message:
            msg_surface = self.font.render(self.message, True, COLORS['black'])
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150))
            surface.blit(msg_surface, msg_rect)

        # Draw input prompt
        if self.show_input:
            prompt_surface = self.font.render(self.prompt, True, COLORS['black'])
            surface.blit(prompt_surface, (self.input_box.x, self.input_box.y - 40))
            txt_surface = self.font.render(self.input_text, True, COLORS['black'])
            width = max(300, txt_surface.get_width() + 10)
            self.input_box.w = width
            pygame.draw.rect(surface, self.color_active, self.input_box, 2)
            surface.blit(txt_surface, (self.input_box.x + 5, self.input_box.y + 5))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Puzzle Game')
    ui = UI()
    clock = pygame.time.Clock()
    running = True
    show_final_message = False
    game_over = False
    level_complete = False
    level = 1

    puzzle_description = f"What is {level} + {level}?"
    ui.activate_input(f"Puzzle Level {level}: {puzzle_description}")

    while running:
        GameVisuals.draw_background(screen)
        if show_final_message:
            GameVisuals.draw_final_wedding_scene(screen)
        elif game_over:
            GameVisuals.draw_game_over(screen)
        elif not level_complete:
            GameVisuals.draw_puzzle_button(screen, PUZZLE_BUTTON_RECT, "Interact")
        ui.draw(screen)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if show_final_message:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                    running = False
            elif game_over:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        level = 1
                        ui.activate_input(f"Puzzle Level {level}: What is {level} + {level}?")
                        game_over = False
                    elif event.key == pygame.K_q:
                        running = False
            elif not level_complete:
                user_input = ui.get_input_event(event)
                if user_input is not None:
                    try:
                        expected_answer = level + level
                        if int(user_input.strip()) == expected_answer:
                            GameVisuals.draw_background(screen)
                            GameVisuals.draw_level_complete(screen, f"Level {level} Complete!")
                            ui.display_message("Correct! You've completed the level.", duration=2000)
                            level_complete = True
                            pygame.display.flip()
                            pygame.time.wait(2000)
                            level += 1
                            if level > 5:
                                show_final_message = True
                            else:
                                ui.activate_input(f"Puzzle Level {level}: What is {level} + {level}?")
                                level_complete = False
                        else:
                            GameVisuals.draw_background(screen)
                            ui.display_message(f"Incorrect. The correct answer was {expected_answer}.", duration=2000)
                            ui.activate_input(f"Puzzle Level {level}: What is {level} + {level}?")
                    except ValueError:
                        ui.display_message("Please enter a valid number.", duration=2000)
            elif level_complete:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    level_complete = False

        clock.tick(30)

    pygame.quit()

if __name__ == '__main__':
    main()
