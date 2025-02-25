#!/usr/bin/env python3
"""
Dwarf Hamsters Wedding Adventure
A two-player cooperative puzzle game where two dwarf hamsters (the bride and groom) prepare for their wedding.
This merged version incorporates improvements from both reviewed versions – including enhanced web‐mode support,
more consistent event handling (with Esc to return to the main menu per original guidelines), helper functions to
consolidate drawing routines, and safe state resets on transitions.
Intended Deployment Environments:
  - Desktop: Standard pygame window.
  - Web: Adapted initialization and main loop (via a run_web_loop) for browser-based environments (e.g., using Pyodide).

Controls:
  Bride (Player 1): Arrow keys for movement, Enter to confirm/select.
  Groom   (Player 2): WASD for movement, Space to interact/confirm.
Other:
  Use the S key to save progress.
  Press Esc to return to Main Menu (from tutorial or puzzles).

Game States:
  MAIN_MENU, TUTORIAL, LEVEL1 (Outfit Puzzle), LEVEL2 (Ring Puzzle),
  LEVEL3 (Cooperative Door Puzzle) and WEDDING.
"""

import pygame
import sys
import json
import os

# Initialize pygame and fonts.
pygame.init()
pygame.font.init()

# Global configuration
SCREEN_WIDTH  = 800
SCREEN_HEIGHT = 600
FPS = 60
WEB_MODE = False  # Set to True in a web environment (e.g., via Pyodide)

# Colors
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE  = (0, 0, 139)
GREEN      = (0, 200, 0)
LIGHTGREEN = (144, 238, 144)
RED        = (200, 0, 0)
YELLOW     = (255, 255, 0)
GRAY       = (200, 200, 200)
PINK       = (255, 182, 193)
DARKGRAY   = (50, 50, 50)

# Save file
SAVE_FILE = "savegame.json"

# Fonts
FONT     = pygame.font.SysFont("arial", 24)
BIG_FONT = pygame.font.SysFont("arial", 36)

# Helper functions for drawing
def draw_text(surface, text, font_obj, color, pos):
    lines = text.split("\n")
    for i, line in enumerate(lines):
        text_obj = font_obj.render(line, True, color)
        rect = text_obj.get_rect(center=(pos[0], pos[1] + i * font_obj.get_height()))
        surface.blit(text_obj, rect)

def draw_button(surface, rect, text, font_obj, text_color, button_color):
    pygame.draw.rect(surface, button_color, rect)
    draw_text(surface, text, font_obj, text_color, rect.center)

def draw_overlay(surface, heading, option_text, instruction):
    # Draws a translucent overlay with a heading, current option, and instructions.
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((255, 255, 255, 200))
    surface.blit(overlay, (0, 0))
    draw_text(surface, heading, BIG_FONT, DARK_BLUE, (SCREEN_WIDTH // 2, 120))
    draw_text(surface, f"<  {option_text}  >", BIG_FONT, BLACK, (SCREEN_WIDTH // 2, 220))
    draw_text(surface, instruction, FONT, DARKGRAY, (SCREEN_WIDTH // 2, 320))

# Player class – each hamster is represented as a rectangle.
class Player:
    def __init__(self, x, y, color, controls):
        # 'controls' is a dict with keys: up, down, left, right, interact.
        self.rect = pygame.Rect(x, y, 40, 40)
        self.color = color
        self.speed = 4
        self.controls = controls
        self.selected_option = 0  # Used during selection overlays

    def move(self, keys_pressed):
        if keys_pressed[self.controls["up"]]:
            self.rect.y -= self.speed
        if keys_pressed[self.controls["down"]]:
            self.rect.y += self.speed
        if keys_pressed[self.controls["left"]]:
            self.rect.x -= self.speed
        if keys_pressed[self.controls["right"]]:
            self.rect.x += self.speed
        # Keep within screen boundaries.
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

# Main Game class handles game logic and state transitions.
class Game:
    def __init__(self):
        # Adjust display for web-based mode if needed.
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dwarf Hamsters Wedding Adventure")
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "MAIN_MENU"
        
        # Create players with individual controls.
        self.players = {
            "bride": Player(100, SCREEN_HEIGHT // 2, PINK, {
                "up": pygame.K_UP,
                "down": pygame.K_DOWN,
                "left": pygame.K_LEFT,
                "right": pygame.K_RIGHT,
                "interact": pygame.K_RETURN
            }),
            "groom": Player(SCREEN_WIDTH - 140, SCREEN_HEIGHT // 2, LIGHT_BLUE, {
                "up": pygame.K_w,
                "down": pygame.K_s,
                "left": pygame.K_a,
                "right": pygame.K_d,
                "interact": pygame.K_SPACE
            })
        }
        
        # Main menu options.
        self.menu_options = ["Start Game", "Tutorial", "Exit"]
        self.menu_selected = 0
        
        # Tutorial text (with instructions as per guidelines – press Esc to return).
        self.tutorial_text = (
            "Welcome to Dwarf Hamsters Wedding Adventure!\n\n"
            "Bride (Player 1): Use Arrow keys to move and Enter to interact/select.\n"
            "Groom (Player 2): Use WASD to move and Space to interact/confirm.\n\n"
            "Complete cooperative puzzles to help the couple get ready for their big day.\n"
            "Communication is key!\n\n"
            "Press Esc to return to Main Menu."
        )
        
        # Puzzle option lists.
        self.outfit_options = ["Red Dress", "Blue Gown", "Green Frock"]
        self.ring_options   = ["Gold Ring", "Silver Ring", "Enchanted Ring"]
        self.bride_choice = None
        self.groom_choice = None
        
        # Level completion flags.
        self.level_flags = {
            "level1_done": False,
            "level2_done": False,
            "level3_done": False
        }
        
        # Level3 (Cooperative Door Puzzle) variables.
        self.door_open = False
        self.door_rect = pygame.Rect(SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 120, 100, 20)
        
        # Level1 (Outfit Puzzle) variables.
        self.wardrobe_rect = pygame.Rect(50, 50, 80, 120)
        self.unlock_button_rect = pygame.Rect(SCREEN_WIDTH - 130, 50, 60, 40)
        self.wardrobe_unlocked = False
        self.in_outfit_menu = False
        
        # Level2 (Ring Puzzle) variables.
        self.ring_shop_rect = pygame.Rect(SCREEN_WIDTH - 140, SCREEN_HEIGHT - 180, 80, 120)
        self.ring_button_rect = pygame.Rect(20, SCREEN_HEIGHT - 80, 60, 40)
        self.ring_shop_unlocked = False
        self.in_ring_menu = False
        
        self.load_game()
    
    def reset_state_variables(self):
        # Reset state-specific flags to prevent carry‐over effects.
        for player in self.players.values():
            player.selected_option = 0
        self.in_outfit_menu = False
        self.in_ring_menu = False
        self.wardrobe_unlocked = False
        self.ring_shop_unlocked = False

    def reposition_players(self, level):
        # Place players appropriately for each level.
        if level == "LEVEL1":
            self.players["bride"].rect.topleft = (100, SCREEN_HEIGHT // 2)
            self.players["groom"].rect.topleft = (SCREEN_WIDTH - 140, SCREEN_HEIGHT // 2)
        elif level == "LEVEL2":
            self.players["bride"].rect.topleft = (20, SCREEN_HEIGHT - 120)
            self.players["groom"].rect.topleft = (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 220)
        elif level == "LEVEL3":
            self.players["bride"].rect.topleft = (self.door_rect.x - 150, self.door_rect.y + 50)
            self.players["groom"].rect.topleft = (self.door_rect.x + self.door_rect.width + 70, self.door_rect.y + 50)
        elif level == "WEDDING":
            self.players["bride"].rect.topleft = (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2)
            self.players["groom"].rect.topleft = (SCREEN_WIDTH // 2 + 40, SCREEN_HEIGHT // 2)

    def save_game(self):
        data = {
            "state": self.state,
            "level_flags": self.level_flags,
            "bride_choice": self.bride_choice,
            "groom_choice": self.groom_choice
        }
        try:
            with open(SAVE_FILE, "w") as f:
                json.dump(data, f)
            print("Game saved.")
        except Exception as e:
            print("Error saving game:", e)

    def load_game(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r") as f:
                    data = json.load(f)
                self.state = data.get("state", "MAIN_MENU")
                self.level_flags = data.get("level_flags", self.level_flags)
                self.bride_choice = data.get("bride_choice")
                self.groom_choice = data.get("groom_choice")
                print("Game loaded.")
            except Exception as e:
                print("Failed to load save file:", e)

    def handle_return_to_menu(self, key):
        # Global handling: Pressing Esc returns to Main Menu.
        if key == pygame.K_ESCAPE and self.state not in ["MAIN_MENU", "WEDDING"]:
            self.state = "MAIN_MENU"
            self.reset_state_variables()

    def handle_events(self):
        keys_pressed = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    self.save_game()
                self.handle_return_to_menu(event.key)
                self.handle_state_specific_events(event)
        return keys_pressed

    def handle_state_specific_events(self, event):
        if self.state == "MAIN_MENU":
            self.handle_main_menu_events(event)
        elif self.state == "TUTORIAL":
            self.handle_tutorial_events(event)
        elif self.state == "LEVEL1":
            self.handle_level1_events(event)
        elif self.state == "LEVEL2":
            self.handle_level2_events(event)
        elif self.state == "LEVEL3":
            self.handle_level3_events(event)
        elif self.state == "WEDDING":
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.running = False

    def handle_main_menu_events(self, event):
        if event.key == pygame.K_UP:
            self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
        elif event.key == pygame.K_DOWN:
            self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
        elif event.key == pygame.K_RETURN:
            selected = self.menu_options[self.menu_selected]
            if selected == "Start Game":
                self.reset_state_variables()
                self.state = "LEVEL1"
                self.level_flags = {"level1_done": False, "level2_done": False, "level3_done": False}
                self.reposition_players("LEVEL1")
            elif selected == "Tutorial":
                self.state = "TUTORIAL"
            elif selected == "Exit":
                self.running = False

    def handle_tutorial_events(self, event):
        # Per original guidelines, pressing Esc (or via global handler) returns to Main Menu.
        if event.type == pygame.KEYDOWN:
            self.state = "MAIN_MENU"
            self.reset_state_variables()

    def handle_level1_events(self, event):
        groom = self.players["groom"]
        bride = self.players["bride"]
        if not self.in_outfit_menu:
            # Groom unlocks the wardrobe if colliding with the unlock button.
            if groom.rect.colliderect(self.unlock_button_rect) and event.key == groom.controls["interact"]:
                self.wardrobe_unlocked = True
            # Bride opens the outfit selection if near the wardrobe and unlocked.
            if self.wardrobe_unlocked and bride.rect.colliderect(self.wardrobe_rect) and event.key == bride.controls["interact"]:
                self.in_outfit_menu = True
        else:
            # Outfit selection overlay controls.
            if event.key == bride.controls["left"]:
                bride.selected_option = (bride.selected_option - 1) % len(self.outfit_options)
            elif event.key == bride.controls["right"]:
                bride.selected_option = (bride.selected_option + 1) % len(self.outfit_options)
            elif event.key == bride.controls["interact"]:
                self.bride_choice = self.outfit_options[bride.selected_option]
                self.level_flags["level1_done"] = True
                self.in_outfit_menu = False
                self.reset_state_variables()
                self.reposition_players("LEVEL2")
                self.state = "LEVEL2"

    def handle_level2_events(self, event):
        bride = self.players["bride"]
        groom = self.players["groom"]
        if not self.in_ring_menu:
            # Bride unlocks the ring shop.
            if bride.rect.colliderect(self.ring_button_rect) and event.key == bride.controls["interact"]:
                self.ring_shop_unlocked = True
            # Groom activates ring selection when near the shop.
            if self.ring_shop_unlocked and groom.rect.colliderect(self.ring_shop_rect) and event.key == groom.controls["interact"]:
                self.in_ring_menu = True
        else:
            # Ring selection overlay controls.
            if event.key == groom.controls["left"]:
                groom.selected_option = (groom.selected_option - 1) % len(self.ring_options)
            elif event.key == groom.controls["right"]:
                groom.selected_option = (groom.selected_option + 1) % len(self.ring_options)
            elif event.key == groom.controls["interact"]:
                self.groom_choice = self.ring_options[groom.selected_option]
                self.level_flags["level2_done"] = True
                self.in_ring_menu = False
                self.reset_state_variables()
                self.reposition_players("LEVEL3")
                self.state = "LEVEL3"

    def handle_level3_events(self, event):
        # Level 3 events are based on player movement; no additional key events are needed.
        pass

    def update(self, keys_pressed):
        # Allow player movement if not in a selection overlay.
        if self.state in ["LEVEL1", "LEVEL2", "LEVEL3", "WEDDING"]:
            if not (self.in_outfit_menu or self.in_ring_menu):
                self.players["bride"].move(keys_pressed)
                self.players["groom"].move(keys_pressed)
        if self.state == "LEVEL3":
            self.update_level3()

    def update_level3(self):
        # Update the cooperative door puzzle.
        plate_left  = pygame.Rect(self.door_rect.x - 100, self.door_rect.y, 80, 20)
        plate_right = pygame.Rect(self.door_rect.x + self.door_rect.width + 20, self.door_rect.y, 80, 20)
        bride_on_plate = plate_left.colliderect(self.players["bride"].rect)
        groom_on_plate = plate_right.colliderect(self.players["groom"].rect)
        if bride_on_plate and groom_on_plate:
            self.door_open = True
            self.level_flags["level3_done"] = True
            # Transition to wedding if either player steps into the door area.
            if self.players["bride"].rect.colliderect(self.door_rect) or self.players["groom"].rect.colliderect(self.door_rect):
                self.reset_state_variables()
                self.reposition_players("WEDDING")
                self.state = "WEDDING"
        else:
            self.door_open = False

    def draw(self):
        if self.state == "WEDDING":
            self.draw_wedding()
        else:
            if self.state == "TUTORIAL":
                self.screen.fill(LIGHTGREEN)
            else:
                self.screen.fill(LIGHT_BLUE)
            if self.state == "MAIN_MENU":
                self.draw_main_menu()
            elif self.state == "TUTORIAL":
                self.draw_tutorial()
            elif self.state == "LEVEL1":
                self.draw_level1()
            elif self.state == "LEVEL2":
                self.draw_level2()
            elif self.state == "LEVEL3":
                self.draw_level3()
        pygame.display.flip()

    def draw_main_menu(self):
        draw_text(self.screen, "Dwarf Hamsters Wedding Adventure", BIG_FONT, DARK_BLUE, (SCREEN_WIDTH // 2, 100))
        for i, option in enumerate(self.menu_options):
            color = RED if i == self.menu_selected else BLACK
            draw_text(self.screen, option, FONT, color, (SCREEN_WIDTH // 2, 250 + i * 40))
        hint = FONT.render("Press 'S' to Save at any time.", True, BLACK)
        self.screen.blit(hint, (10, SCREEN_HEIGHT - 30))

    def draw_tutorial(self):
        draw_text(self.screen, self.tutorial_text, FONT, BLACK, (SCREEN_WIDTH // 2, 150))

    def draw_level1(self):
        instructions = FONT.render("Level 1: Cooperatively unlock the wardrobe & Bride choose outfit.", True, BLACK)
        self.screen.blit(instructions, (50, 20))
        if self.wardrobe_unlocked:
            pygame.draw.rect(self.screen, GREEN, self.wardrobe_rect)
            draw_text(self.screen, "Wardrobe\n(Unlocked)", FONT, BLACK, self.wardrobe_rect.center)
        else:
            pygame.draw.rect(self.screen, GRAY, self.wardrobe_rect)
            draw_text(self.screen, "Wardrobe\n(Locked)", FONT, BLACK, self.wardrobe_rect.center)
        draw_button(self.screen, self.unlock_button_rect, "Unlock", FONT, BLACK, YELLOW)
        if self.in_outfit_menu:
            current_option = self.outfit_options[self.players["bride"].selected_option]
            draw_overlay(self.screen, "Choose your outfit:", current_option, "Use LEFT/RIGHT to cycle, Enter to confirm.")
        self.players["bride"].draw(self.screen)
        self.players["groom"].draw(self.screen)

    def draw_level2(self):
        instructions = FONT.render("Level 2: Cooperatively unlock the ring shop & Groom choose ring.", True, BLACK)
        self.screen.blit(instructions, (50, 20))
        if self.ring_shop_unlocked:
            pygame.draw.rect(self.screen, GREEN, self.ring_shop_rect)
            draw_text(self.screen, "Ring Shop\n(Unlocked)", FONT, BLACK, self.ring_shop_rect.center)
        else:
            pygame.draw.rect(self.screen, GRAY, self.ring_shop_rect)
            draw_text(self.screen, "Ring Shop\n(Locked)", FONT, BLACK, self.ring_shop_rect.center)
        draw_button(self.screen, self.ring_button_rect, "Unlock", FONT, BLACK, YELLOW)
        if self.in_ring_menu:
            current_option = self.ring_options[self.players["groom"].selected_option]
            draw_overlay(self.screen, "Choose your ring:", current_option, "Use LEFT/RIGHT to cycle, Space to confirm.")
        self.players["bride"].draw(self.screen)
        self.players["groom"].draw(self.screen)

    def draw_level3(self):
        instructions = FONT.render("Level 3: Both players, stand on your pressure plates to open the door.", True, BLACK)
        self.screen.blit(instructions, (50, 20))
        plate_left  = pygame.Rect(self.door_rect.x - 100, self.door_rect.y, 80, 20)
        plate_right = pygame.Rect(self.door_rect.x + self.door_rect.width + 20, self.door_rect.y, 80, 20)
        pygame.draw.rect(self.screen, GRAY, plate_left)
        pygame.draw.rect(self.screen, GRAY, plate_right)
        draw_text(self.screen, "Bride", FONT, BLACK, plate_left.center)
        draw_text(self.screen, "Groom", FONT, BLACK, plate_right.center)
        door_color = GREEN if self.door_open else RED
        pygame.draw.rect(self.screen, door_color, self.door_rect)
        draw_text(self.screen, "Door", FONT, BLACK, self.door_rect.center)
        if self.door_open:
            prompt = FONT.render("Door open! Step in to proceed.", True, BLACK)
            self.screen.blit(prompt, (self.door_rect.x, self.door_rect.y - 30))
        self.players["bride"].draw(self.screen)
        self.players["groom"].draw(self.screen)

    def draw_wedding(self):
        self.screen.fill(WHITE)
        title = BIG_FONT.render("Wedding Ceremony", True, DARK_BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))
        summary = FONT.render(f"Bride chose: {self.bride_choice} | Groom chose: {self.groom_choice}", True, BLACK)
        self.screen.blit(summary, (SCREEN_WIDTH // 2 - summary.get_width() // 2, 150))
        couple_txt = BIG_FONT.render("They are now married!", True, GREEN)
        self.screen.blit(couple_txt, (SCREEN_WIDTH // 2 - couple_txt.get_width() // 2, 250))
        prompt = FONT.render("Press Enter or Space to exit.", True, RED)
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 350))
        self.players["bride"].draw(self.screen)
        self.players["groom"].draw(self.screen)

    def run(self):
        if WEB_MODE:
            self.run_web_loop()
        else:
            while self.running:
                self.clock.tick(FPS)
                keys_pressed = self.handle_events()
                self.update(keys_pressed)
                self.draw()
            pygame.quit()
            sys.exit()

    def run_web(self):
        # Single frame update for web-based scheduling.
        for event in pygame.event.get():
            pass
        self.clock.tick(FPS)
        keys_pressed = self.handle_events()
        self.update(keys_pressed)
        self.draw()
        # Schedule next frame using a timer event.
        pygame.time.set_timer(pygame.USEREVENT, int(1000 / FPS))

    def run_web_loop(self):
        # Non-blocking loop compatible with web schedulers (e.g., requestAnimationFrame).
        self.run_web()
        if self.running:
            pygame.time.set_timer(pygame.USEREVENT, int(1000 / FPS))
        else:
            pygame.quit()

if __name__ == "__main__":
    # Detect web environment (e.g., Pyodide) via attempting to import js.
    try:
        import js
        WEB_MODE = True
    except ImportError:
        WEB_MODE = False
    game = Game()
    game.run()
