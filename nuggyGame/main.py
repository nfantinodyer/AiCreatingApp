import pygame
import sys
import json
import os
import random

# Global constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
MAX_LEVEL = 5
PUZZLES_PER_LEVEL = 10

COLORS = {
    'white': (255, 255, 255),
    'black': (0, 0, 0),
    'pink': (255, 182, 193),
    'blue': (0, 0, 255),
    'green': (0, 255, 0),
    'red': (255, 0, 0),
    'lightgray': (200, 200, 200),
}

PUZZLE_BUTTON_RECT = (SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT//2 - 25, 150, 50)
SAVE_FILE = 'save_game.json'

class Puzzle:
    def __init__(self, description, solution):
        self.description = description
        self.solution = solution
        self.solved = False

    def check_solution(self, answer):
        return answer.strip().lower() == self.solution.lower()

def create_puzzles(level=1, puzzles_per_level=10):
    sample_puzzles = [
        Puzzle("What is the color of the sky on a clear day?", "blue"),
        Puzzle("What do you call a baby cat?", "kitten"),
        Puzzle("What is 2 + 2?", "4"),
        Puzzle("What is the opposite of cold?", "hot"),
        Puzzle("What do bees produce?", "honey"),
        Puzzle("What is the capital of France?", "paris"),
        Puzzle("What is the largest planet in our solar system?", "jupiter"),
        Puzzle("What language do they speak in Spain?", "spanish"),
        Puzzle("What is H2O commonly known as?", "water"),
        Puzzle("What tool do you use to drive a nail?", "hammer"),
        Puzzle("What is the tallest mountain in the world?", "everest"),
        Puzzle("What gas do plants absorb?", "carbon dioxide"),
        Puzzle("What is the freezing point of water in Celsius?", "0"),
        Puzzle("What is the currency of Japan?", "yen"),
        Puzzle("What planet is known as the Red Planet?", "mars"),
        Puzzle("What is the hardest natural substance?", "diamond"),
        Puzzle("What device do you use to look at stars?", "telescope"),
        Puzzle("What is the largest ocean on Earth?", "pacific"),
        Puzzle("What is the process by which plants make food?", "photosynthesis"),
        Puzzle("What is the main language spoken in Brazil?", "portuguese"),
    ]
    random.shuffle(sample_puzzles)
    return sample_puzzles[:puzzles_per_level]

def retrieve_random_puzzle(puzzles):
    unsolved = [p for p in puzzles if not p.solved]
    if unsolved:
        return random.choice(unsolved)
    return None

def save_game_state(data):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except IOError:
        pass

def load_game_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None

def show_tutorial():
    return ("Welcome to Dwarf Hamster Wedding Adventure!\n\n"
            "Player 1 (Bride):\n"
            "  Move: W, A, S, D\n"
            "  Interact: SPACE\n\n"
            "Player 2 (Groom):\n"
            "  Move: Arrow keys\n"
            "  Interact: ENTER\n\n"
            "Work together to solve puzzles and prepare for the wedding!\n")

class UI:
    def __init__(self):
        self.active = False
        self.input_text = ''
        self.prompt = ''
        self.message = ''
        self.message_timer = 0
        self.message_render = None
        self.message_rect = None
        self.font = pygame.font.SysFont(None, 36)

    def activate_input(self, prompt):
        self.active = True
        self.input_text = ''
        self.prompt = prompt

    def get_input_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                self.active = False
                return self.input_text
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            else:
                self.input_text += event.unicode
        return None

    def display_message(self, message, duration=2000):
        self.message = message
        self.message_timer = pygame.time.get_ticks() + duration
        self.message_render = self.font.render(self.message, True, COLORS['black'])
        self.message_rect = self.message_render.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))

    def draw(self, screen):
        if self.active:
            lines = self.prompt.split('\n')
            for i, line in enumerate(lines):
                prompt_surface = self.font.render(line, True, COLORS['black'])
                screen.blit(prompt_surface, (SCREEN_WIDTH//2 - prompt_surface.get_width()//2, SCREEN_HEIGHT//2 - 50 + i * 30))
            input_surface = self.font.render(self.input_text, True, COLORS['black'])
            screen.blit(input_surface, (SCREEN_WIDTH//2 - input_surface.get_width()//2, SCREEN_HEIGHT//2 + 50))
        if self.message_timer > pygame.time.get_ticks():
            screen.blit(self.message_render, self.message_rect)
        else:
            self.message = ''
            self.message_timer = 0

class GameVisuals:
    @staticmethod
    def draw_background(screen):
        screen.fill(COLORS['lightgray'])

    @staticmethod
    def draw_puzzle_button(screen, rect):
        pygame.draw.rect(screen, COLORS['green'], rect)
        font = pygame.font.SysFont(None, 36)
        text = font.render("Puzzle", True, COLORS['white'])
        text_rect = text.get_rect(center=(rect[0] + rect[2]//2, rect[1] + rect[3]//2))
        screen.blit(text, text_rect)

    @staticmethod
    def draw_final_wedding_scene(screen):
        screen.fill(COLORS['white'])
        font = pygame.font.SysFont(None, 48)
        text = font.render("Final Wedding Ceremony!", True, COLORS['blue'])
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
        screen.blit(text, text_rect)

        text2 = font.render("Thank you for playing!", True, COLORS['black'])
        text_rect2 = text2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10))
        screen.blit(text2, text_rect2)

    @staticmethod
    def draw_level_complete(screen, level_text):
        font = pygame.font.SysFont(None, 48)
        text = font.render(level_text, True, COLORS['blue'])
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(text, text_rect)

    @staticmethod
    def draw_game_over(screen):
        font = pygame.font.SysFont(None, 48)
        text = font.render("Game Over!", True, COLORS['red'])
        text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(text, text_rect)

class Hamster(pygame.sprite.Sprite):
    def __init__(self, x, y, color, controls, image_name=None):
        super().__init__()
        self.rect = pygame.Rect(x, y, 50, 50)
        self.color = color
        self.controls = controls
        self.image_name = image_name
        self.image_path = self.image_name
        if self.image_path and os.path.exists(self.image_path):
            self.image = pygame.image.load(self.image_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (50, 50))
        else:
            self.image = None
        self.velocity = 5
        self.font = pygame.font.SysFont(None, 24)

    def handle_keys(self):
        keys = pygame.key.get_pressed()
        if keys[self.controls['left']]:
            self.rect.x -= self.velocity
        if keys[self.controls['right']]:
            self.rect.x += self.velocity
        if keys[self.controls['up']]:
            self.rect.y -= self.velocity
        if keys[self.controls['down']]:
            self.rect.y += self.velocity

    def update(self):
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.ellipse(surface, self.color, self.rect)
            eye_radius = 3
            eye_y = self.rect.y + 15
            eye_x_offset = 10
            pygame.draw.circle(surface, COLORS['black'], (self.rect.x + eye_x_offset, eye_y), eye_radius)
            pygame.draw.circle(surface, COLORS['black'], (self.rect.x + self.rect.width - eye_x_offset, eye_y), eye_radius)
            mouth_start = (self.rect.x + 15, self.rect.y + 30)
            mouth_end = (self.rect.x + 35, self.rect.y + 30)
            pygame.draw.line(surface, COLORS['black'], mouth_start, mouth_end, 2)

class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dwarf Hamster Wedding Adventure")
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.game_state = 'playing'
        self.current_level = 1
        self.puzzles = create_puzzles(level=self.current_level, puzzles_per_level=PUZZLES_PER_LEVEL)
        self.final_scene = False

        # Load a saved game state if present
        saved = load_game_state()
        if saved:
            self.current_level = saved.get('current_level', 1)
            self.game_state = saved.get('game_state', 'playing')
            puzzles_data = saved.get('puzzles', [])
            self.puzzles = []
            for p in puzzles_data:
                puzzle = Puzzle(p['description'], p['solution'])
                puzzle.solved = p.get('solved', False)
                self.puzzles.append(puzzle)

        self.puzzle_button_rect = pygame.Rect(*PUZZLE_BUTTON_RECT)

        bride_controls = {
            'left': pygame.K_a,
            'right': pygame.K_d,
            'up': pygame.K_w,
            'down': pygame.K_s,
            'interact': pygame.K_SPACE
        }
        groom_controls = {
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'interact': pygame.K_RETURN
        }
        # Initial positions for bride and groom
        bride_x = SCREEN_WIDTH // 4
        bride_y = SCREEN_HEIGHT - 150
        groom_x = 3 * SCREEN_WIDTH // 4
        groom_y = SCREEN_HEIGHT - 150

        self.bride = Hamster(bride_x, bride_y, COLORS['pink'], bride_controls, image_name='bride.png')
        self.groom = Hamster(groom_x, groom_y, COLORS['black'], groom_controls, image_name='groom.png')

    def save_state(self):
        data = {
            'current_level': self.current_level,
            'game_state': self.game_state,
            'puzzles': [
                {'description': p.description, 'solution': p.solution, 'solved': p.solved}
                for p in self.puzzles
            ]
        }
        save_game_state(data)

    def reset_game(self):
        """Reset the game to its initial state."""
        self.current_level = 1
        self.puzzles = create_puzzles(level=self.current_level, puzzles_per_level=PUZZLES_PER_LEVEL)
        self.bride.rect.center = (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150)
        self.groom.rect.center = (3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150)
        self.game_state = 'playing'
        self.final_scene = False
        self.save_state()

    def advance_level(self):
        """Move to the next level or go to final wedding if MAX_LEVEL is reached."""
        self.current_level += 1
        if self.current_level > MAX_LEVEL:
            self.game_state = 'final_wedding'
            self.final_scene = True
        else:
            self.puzzles = create_puzzles(level=self.current_level, puzzles_per_level=PUZZLES_PER_LEVEL)
            self.bride.rect.center = (SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150)
            self.groom.rect.center = (3 * SCREEN_WIDTH // 4, SCREEN_HEIGHT - 150)
            self.game_state = 'playing'
        self.save_state()

    def process_puzzle_answer(self, answer):
        """Check user answer against a random unsolved puzzle."""
        current_puzzle = retrieve_random_puzzle(self.puzzles)
        if current_puzzle:
            if current_puzzle.check_solution(answer):
                current_puzzle.solved = True
                self.ui.display_message("Correct! Puzzle solved.", duration=2000)
                if all(p.solved for p in self.puzzles):
                    if self.current_level >= MAX_LEVEL:
                        self.game_state = 'final_wedding'
                        self.final_scene = True
                    else:
                        self.game_state = 'level_complete'
                    self.save_state()
            else:
                self.ui.display_message("Incorrect! Try again.", duration=2000)

    def attempt_puzzle(self):
        """Prompt user to solve a random unsolved puzzle if available."""
        current_puzzle = retrieve_random_puzzle(self.puzzles)
        if current_puzzle:
            self.ui.activate_input(current_puzzle.description)
        else:
            self.ui.display_message("All puzzles solved for this level!", duration=2000)
            if all(p.solved for p in self.puzzles):
                if self.current_level >= MAX_LEVEL:
                    self.game_state = 'final_wedding'
                    self.final_scene = True
                else:
                    self.game_state = 'level_complete'
                self.save_state()

    def resolve_collision(self):
        """
        Simple collision resolution to prevent hamsters from overlapping.
        Moves them apart if they collide.
        """
        if self.bride.rect.colliderect(self.groom.rect):
            overlap_x = (self.bride.rect.x + self.bride.rect.width) - self.groom.rect.x
            overlap_y = (self.bride.rect.y + self.bride.rect.height) - self.groom.rect.y
            # Move them slightly apart
            if abs(overlap_x) < abs(overlap_y):
                if self.bride.rect.centerx < self.groom.rect.centerx:
                    self.bride.rect.x -= overlap_x // 2
                    self.groom.rect.x += overlap_x // 2
                else:
                    self.bride.rect.x += overlap_x // 2
                    self.groom.rect.x -= overlap_x // 2
            else:
                if self.bride.rect.centery < self.groom.rect.centery:
                    self.bride.rect.y -= overlap_y // 2
                    self.groom.rect.y += overlap_y // 2
                else:
                    self.bride.rect.y += overlap_y // 2
                    self.groom.rect.y -= overlap_y // 2

    def run(self):
        """Main game loop."""
        # Show tutorial at the start
        tutorial_text = show_tutorial()
        self.ui.display_message(tutorial_text, duration=10000)
        pygame.display.flip()
        pygame.time.wait(10000)

        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_state()
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if self.game_state == 'game_over':
                        if event.key == pygame.K_r:
                            self.reset_game()
                        elif event.key == pygame.K_q:
                            self.save_state()
                            running = False

                    elif self.game_state == 'level_complete':
                        if event.key == pygame.K_SPACE:
                            self.advance_level()

                    elif self.game_state == 'final_wedding':
                        if event.key == pygame.K_q:
                            running = False

                # Check if UI returned an input from the puzzle prompt
                user_input = self.ui.get_input_event(event)
                if user_input is not None and self.game_state == 'playing':
                    self.process_puzzle_answer(user_input)

            # Check puzzle interaction
            if self.game_state == 'playing':
                keys = pygame.key.get_pressed()
                bride_interact = self.bride.rect.colliderect(self.puzzle_button_rect) and keys[self.bride.controls['interact']]
                groom_interact = self.groom.rect.colliderect(self.puzzle_button_rect) and keys[self.groom.controls['interact']]
                if bride_interact or groom_interact:
                    self.attempt_puzzle()

                self.bride.handle_keys()
                self.groom.handle_keys()
                self.bride.update()
                self.groom.update()
                self.resolve_collision()

                # Draw the normal game scene
                GameVisuals.draw_background(self.screen)
                GameVisuals.draw_puzzle_button(self.screen, self.puzzle_button_rect)
                self.bride.draw(self.screen)
                self.groom.draw(self.screen)

            elif self.game_state == 'level_complete':
                GameVisuals.draw_background(self.screen)
                GameVisuals.draw_level_complete(self.screen, f"Level {self.current_level} Complete!")

            elif self.game_state == 'final_wedding':
                GameVisuals.draw_final_wedding_scene(self.screen)

            elif self.game_state == 'game_over':
                GameVisuals.draw_game_over(self.screen)

            self.ui.draw(self.screen)
            pygame.display.flip()

        pygame.quit()
        sys.exit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()
