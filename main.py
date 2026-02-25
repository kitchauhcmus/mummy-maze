import pygame
import os
import sys
import re
import json
import graphics
import characters
import ascii_game
import maze_generator  

# --- IMPORT DATABASE ---
try:
    from database import UserManager
except ImportError:
    print("WARNING: Running without database.py file. Data won't save correctly.")


    class UserManager:
        def register(self, n, c): return True, "Registration Mock"

        def login(self, n, c): return True, {"max_level": 1, "difficulty": 1, "score": 0}

        def get_level(self, n): return 1

        def get_difficulty(self, n): return 1

        def get_score(self, n): return 0

        def reset_level(self, n): pass

        def update_progress(self, n, l): pass

        def add_score(self, n, p): pass

        def update_difficulty(self, n, d): pass

        def get_leaderboard(self): return []

# --- ĐỊNH NGHĨA PATH ---
project_path = os.path.dirname(os.path.abspath(__file__))
map_path = os.path.join(project_path, "map")
maze_path = os.path.join(map_path, "maze")
object_path = os.path.join(map_path, "agents")
image_path = os.path.join(project_path, "image")
save_file_path = os.path.join(project_path, "savegame.json")

# --- MUSIC & SOUND PATH ---
music_path = os.path.join(project_path, "music")
sound_path = os.path.join(project_path, "sound")

# Màu sắc & Window
COLOR_BG = (20, 20, 30);
COLOR_TEXT = (255, 255, 255);
COLOR_HOVER = (255, 215, 0)
COLOR_LOCKED = (100, 100, 100);
COLOR_RED = (200, 50, 50)
COLOR_BUTTON = (100, 200, 100);
COLOR_BUTTON_HOVER = (150, 250, 150)
COLOR_UNDO = (255, 165, 0);
COLOR_RESET = (255, 69, 0)
WINDOW_WIDTH, WINDOW_HEIGHT = 494, 480

# --- GLOBAL VARIABLES ---
game_sounds = {}
current_music_file = None


# =============================================================================
# CÁC HÀM HỖ TRỢ
# =============================================================================

def check_folders():
    if not os.path.exists(music_path): os.makedirs(music_path)
    if not os.path.exists(sound_path): os.makedirs(sound_path)


def load_game_sounds():
    check_folders()
    sounds = {}
    files = {"move": "move.wav", "danger": "danger.wav", "win": "win.wav", "lose": "lose.wav"}
    for key, filename in files.items():
        full_path = os.path.join(sound_path, filename)
        if os.path.exists(full_path):
            try:
                sounds[key] = pygame.mixer.Sound(full_path)
                sounds[key].set_volume(0.6)
            except:
                sounds[key] = None
        else:
            sounds[key] = None
    return sounds


def play_sfx(sound_key):
    if sound_key in game_sounds and game_sounds[sound_key]:
        game_sounds[sound_key].play()


def get_music_files_with_thresholds():
    check_folders()
    files = []
    try:
        for f in os.listdir(music_path):
            if f.lower().endswith(('.mp3', '.wav', '.ogg')):
                files.append(f)
    except:
        pass
    files.sort()
    music_data = []
    signature_track = "Dentaneosuchus Hunt.mp3"
    threshold_step = 200
    current_threshold = 200
    if signature_track in files:
        music_data.append((signature_track, 0))
        files.remove(signature_track)
    for f in files:
        music_data.append((f, current_threshold))
        current_threshold += threshold_step
    return music_data


def play_bg_music(filename):
    global current_music_file
    if filename == current_music_file and pygame.mixer.music.get_busy(): return
    full_path = os.path.join(music_path, filename)
    if os.path.exists(full_path):
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.play(-1)
            pygame.mixer.music.set_volume(0.5)
            current_music_file = filename
        except:
            pass


def stop_bg_music():
    pygame.mixer.music.stop()
    global current_music_file
    current_music_file = None


def init_startup_music():
    check_folders()
    signature_track = "Dentaneosuchus Hunt.mp3"
    full_path = os.path.join(music_path, signature_track)
    if os.path.exists(full_path):
        play_bg_music(signature_track)
    else:
        try:
            files = [f for f in os.listdir(music_path) if f.endswith(('.mp3', '.wav'))]
            if files: play_bg_music(files[0])
        except:
            pass


# --- HÀM LỌC LEVEL THEO YÊU CẦU  ---
def get_sorted_levels(difficulty=1):
    """
    difficulty = 1 (Easy): Lấy map DỄ (không có chữ 'hard' trong tên).
    difficulty = 2 (Medium) hoặc 3 (Hard): Lấy map KHÓ (có chữ 'hard' trong tên).
    """
    try:
        all_files = [f for f in os.listdir(maze_path) if f.endswith('.txt')]
    except FileNotFoundError:
        return []

    filtered_files = []

    # Lọc file dựa trên độ khó
    for f in all_files:
        is_hard_map = "hard" in f.lower()

        if difficulty == 1:  # Chế độ Easy -> Lấy map gốc
            if not is_hard_map: filtered_files.append(f)

        else:  # Chế độ Medium (2) hoặc Hard (3) -> Lấy map khó
            if is_hard_map: filtered_files.append(f)

    def sort_key(filename):
        numbers = re.findall(r'\d+', filename)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        elif len(numbers) == 1:
            return int(numbers[0]), 0
        return 999, 999

    filtered_files.sort(key=sort_key)
    return filtered_files


def save_game_process(layout_file, explorer, mw, mr, sw, sr, gate, current_idx, difficulty):
    data = {
        "layout": layout_file,
        "level_idx": current_idx,
        "difficulty": difficulty,  # Lưu thêm độ khó
        "explorer": (explorer.get_x(), explorer.get_y()),
        "gate_closed": gate.get("isClosed", True),
        "mw": [(c.get_x(), c.get_y()) for c in mw],
        "mr": [(c.get_x(), c.get_y()) for c in mr],
        "sw": [(c.get_x(), c.get_y()) for c in sw],
        "sr": [(c.get_x(), c.get_y()) for c in sr]
    }
    try:
        with open(save_file_path, "w") as f:
            json.dump(data, f)
        return True
    except:
        return False


def load_game_data():
    if not os.path.exists(save_file_path): return None
    try:
        with open(save_file_path, "r") as f:
            return json.load(f)
    except:
        return None


def clear_save_file():
    if os.path.exists(save_file_path):
        try:
            os.remove(save_file_path)
        except:
            pass


class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = (100, 100, 100);
        self.color_active = (0, 255, 0)
        self.color = self.color_inactive;
        self.text = text
        self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, (0, 255, 0))
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = not self.active if self.rect.collidepoint(event.pos) else False
            self.color = self.color_active if self.active else self.color_inactive
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, (0, 255, 0))

    def update(self):
        self.rect.w = max(200, self.txt_surface.get_width() + 10)

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 0, 0), self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


class GameState:
    def __init__(self, file_name):
        self.screen_size_x = 494
        self.screen_size_y = 480
        self.maze_rect = 360
        self.coordinate_screen_x = 67
        self.coordinate_screen_y = 80
        self.get_input_maze(file_name)
        self.get_input_object(file_name)
        if self.gate_position:
            self.gate = {"gate_position": self.gate_position, "isClosed": True, "cellIndex": 0}
        else:
            self.gate = {"gate_position": (-100, -100), "isClosed": False, "cellIndex": 0}
        self.explorer_direction = "RIGHT" if self.explorer_position[1] // 2 <= self.maze_size // 2 else "LEFT"
        self.mummy_white_direction = ["DOWN"] * len(self.mummy_white_position)
        self.mummy_red_direction = ["DOWN"] * len(self.mummy_red_position)
        self.scorpion_white_direction = ["DOWN"] * len(self.scorpion_white_position)
        self.scorpion_red_direction = ["DOWN"] * len(self.scorpion_red_position)

    def get_input_maze(self, name):
        self.maze = []
        self.stair_position = ()
        self.key_position = ()
        self.gate_position = ()
        self.trap_position = []
        # Tự động tìm đường dẫn
        full_maze_path = os.path.join(maze_path, name)
        if not os.path.exists(full_maze_path):
            print(f"Error: Maze file not found: {full_maze_path}")
            # Tạo map rỗng để không crash
            self.maze = ["%" * 13] * 13
        else:
            with open(full_maze_path, "r") as file:
                for line in file: self.maze.append([c for c in line if c != '\n'])

        self.maze_size = len(self.maze) // 2
        self.cell_rect = self.maze_rect // self.maze_size
        for i in range(len(self.maze)):
            for j in range(len(self.maze[i])):
                if self.maze[i][j] == 'S': self.stair_position = (i, j)
                if self.maze[i][j] == 'T': self.trap_position.append((i, j))
                if self.maze[i][j] == 'K': self.key_position = (i, j)
                if self.maze[i][j] == 'G': self.gate_position = (i, j)

    def get_input_object(self, name):
        self.mummy_white_position = []
        self.mummy_red_position = []
        self.scorpion_white_position = []
        self.scorpion_red_position = []
        self.explorer_position = [2, 2]  # Default fallback

        full_obj_path = os.path.join(object_path, name)
        if os.path.exists(full_obj_path):
            with open(full_obj_path, "r") as file:
                for line in file:
                    x = line.split()
                    if not x: continue
                    if x[0] == 'E':
                        self.explorer_position = [int(x[1]), int(x[2])]
                    elif x[0] == 'MW':
                        self.mummy_white_position.append([int(x[1]), int(x[2])])
                    elif x[0] == 'MR':
                        self.mummy_red_position.append([int(x[1]), int(x[2])])
                    elif x[0] == 'SW':
                        self.scorpion_white_position.append([int(x[1]), int(x[2])])
                    elif x[0] == 'SR':
                        self.scorpion_red_position.append([int(x[1]), int(x[2])])
        else:
            print(f"Warning: Agents file not found for {name}")

    def show_information(self):
        print("Maze Loaded!")


def load_image_path(size):
    def jp(f): return os.path.join(image_path, f)

    return jp("backdrop.png"), jp(f"floor{size}.jpg"), jp(f"walls{size}.png"), jp(f"key{size}.png"), \
        jp(f"gate{size}.png"), jp(f"trap{size}.png"), jp(f"stairs{size}.png"), jp(f"explorer{size}.png"), \
        jp(f"mummy_white{size}.png"), jp(f"redmummy{size}.png"), jp(f"white_scorpion{size}.png"), jp(
        f"red_scorpion{size}.png")


def Cal_coordinates(game, position_x, position_y):
    coordinate_x = game.coordinate_screen_x + game.cell_rect * (position_y // 2)
    coordinate_y = game.coordinate_screen_y + game.cell_rect * (position_x // 2)
    if game.maze[position_x - 1][position_y] == "%" or game.maze[position_x - 1][position_y] == "G": coordinate_y += 3
    return [coordinate_x, coordinate_y]


def character_same_place_with_key(character, key_position, gate, render, screen, game, backdrop, floor, stair,
                                  stair_position, trap, trap_position, key, gate_sheet, wall, explorer, mummy_white,
                                  mummy_red, scorpion_white, scorpion_red):
    if key_position and character.get_x() == key_position[0] and character.get_y() == key_position[1]:
        gate["isClosed"] = not gate["isClosed"]
        if render:
            graphics.gate_animation(screen, game, backdrop, floor, stair, stair_position, trap, trap_position,
                                    key, key_position, gate_sheet, gate, wall, explorer, mummy_white, mummy_red,
                                    scorpion_white, scorpion_red)
        gate["cellIndex"] = 0 if gate["isClosed"] else -1
    return gate


def update_list_character(list_char, list_sheet):
    i = 0
    while i < len(list_char):
        j = 0
        while j < len(list_char):
            if j != i and list_char[i].check_same_position(list_char[j]):
                del list_char[j], list_sheet[j]
            j += 1
        i += 1
    return list_char, list_sheet


def update_lists_character(list_strong, list_weak, list_sheet_weak):
    for i in range(len(list_strong)):
        j = 0
        while j < len(list_weak):
            if list_strong[i].check_same_position(list_weak[j]):
                del list_weak[j], list_sheet_weak[j]
            j += 1
    return list_weak, list_sheet_weak


def check_explorer_is_killed(explorer, mw, mr, sw, sr, trap_pos_list):
    if trap_pos_list:
        for t in trap_pos_list:
            if explorer.get_x() == t[0] and explorer.get_y() == t[1]: return True
    for char_list in [mw, mr, sw, sr]:
        if char_list:
            for char in char_list:
                if explorer.get_x() == char.get_x() and explorer.get_y() == char.get_y(): return True
    return False


def update_enemy_position(window, render, game, backdrop, floor, stair, trap, key, gate, wall, explorer,
                          explorer_char, mw_char, mr_char, sw_char, sr_char, list_mw, list_mr, list_sw, list_sr):
    game.gate = character_same_place_with_key(explorer_char, game.key_position, game.gate, render, window, game,
                                              backdrop, floor, stair, game.stair_position, trap, game.trap_position,
                                              key, gate, wall, explorer, list_mw, list_mr, list_sw, list_sr)

    if check_explorer_is_killed(explorer_char, mw_char, mr_char, sw_char, sr_char, game.trap_position):
        if render: pygame.time.delay(500)
        return "LOSE"

    def move_and_update(char_list, move_func):
        past_pos, new_pos = [], []
        for i in range(len(char_list)):
            past_pos.append([char_list[i].get_x(), char_list[i].get_y()])
            char_list[i] = move_func(char_list[i], game.maze, game.gate, explorer_char)
            new_pos.append([char_list[i].get_x(), char_list[i].get_y()])
        return past_pos, new_pos

    # --- LƯỢT 1 ---
    mw_past, mw_new = move_and_update(mw_char, lambda c, m, g, e: c.white_move(m, g, e))
    for i in range(len(mw_char)): game.gate = character_same_place_with_key(mw_char[i], game.key_position, game.gate,
                                                                            render, window, game, backdrop, floor,
                                                                            stair, game.stair_position, trap,
                                                                            game.trap_position, key, gate, wall,
                                                                            explorer, list_mw, list_mr, list_sw,
                                                                            list_sr)
    mr_past, mr_new = move_and_update(mr_char, lambda c, m, g, e: c.red_move(m, g, e))
    for i in range(len(mr_char)): game.gate = character_same_place_with_key(mr_char[i], game.key_position, game.gate,
                                                                            render, window, game, backdrop, floor,
                                                                            stair, game.stair_position, trap,
                                                                            game.trap_position, key, gate, wall,
                                                                            explorer, list_mw, list_mr, list_sw,
                                                                            list_sr)
    sw_past, sw_new = move_and_update(sw_char, lambda c, m, g, e: c.white_move(m, g, e))
    for i in range(len(sw_char)): game.gate = character_same_place_with_key(sw_char[i], game.key_position, game.gate,
                                                                            render, window, game, backdrop, floor,
                                                                            stair, game.stair_position, trap,
                                                                            game.trap_position, key, gate, wall,
                                                                            explorer, list_mw, list_mr, list_sw,
                                                                            list_sr)
    sr_past, sr_new = move_and_update(sr_char, lambda c, m, g, e: c.red_move(m, g, e))
    for i in range(len(sr_char)): game.gate = character_same_place_with_key(sr_char[i], game.key_position, game.gate,
                                                                            render, window, game, backdrop, floor,
                                                                            stair, game.stair_position, trap,
                                                                            game.trap_position, key, gate, wall,
                                                                            explorer, list_mw, list_mr, list_sw,
                                                                            list_sr)

    if render:
        graphics.enemy_move_animation(mw_past, mw_new, mr_past, mr_new, sw_past, sw_new, sr_past, sr_new, window,
                                      game, backdrop, floor, stair, game.stair_position, trap, game.trap_position,
                                      key, game.key_position, gate, game.gate, wall, explorer, list_mw, list_mr,
                                      list_sw, list_sr)

    if check_explorer_is_killed(explorer_char, mw_char, mr_char, sw_char, sr_char, game.trap_position):
        if render: pygame.time.delay(500)
        return "LOSE"

    mw_char, list_mw = update_list_character(mw_char, list_mw)
    mr_char, list_mr = update_list_character(mr_char, list_mr)
    if mr_char: mr_char, list_mr = update_lists_character(mw_char, mr_char, list_mr)
    if sw_char: sw_char, list_sw = update_lists_character(mw_char, sw_char, list_sw)
    if sr_char: sr_char, list_sr = update_lists_character(mw_char, sr_char, list_sr)
    if sw_char: sw_char, list_sw = update_lists_character(mr_char, sw_char, list_sw)
    if sr_char: sr_char, list_sr = update_lists_character(mr_char, sr_char, list_sr)
    if sr_char: sr_char, list_sr = update_lists_character(sw_char, sr_char, list_sr)

    sw_past, sr_past = sw_new.copy(), sr_new.copy()

    # --- LƯỢT 2 ---
    mw_past, mw_new = move_and_update(mw_char, lambda c, m, g, e: c.white_move(m, g, e))
    for i in range(len(mw_char)): game.gate = character_same_place_with_key(mw_char[i], game.key_position, game.gate,
                                                                            render, window, game, backdrop, floor,
                                                                            stair, game.stair_position, trap,
                                                                            game.trap_position, key, gate, wall,
                                                                            explorer, list_mw, list_mr, list_sw,
                                                                            list_sr)
    mr_past, mr_new = move_and_update(mr_char, lambda c, m, g, e: c.red_move(m, g, e))
    for i in range(len(mr_char)): game.gate = character_same_place_with_key(mr_char[i], game.key_position, game.gate,
                                                                            render, window, game, backdrop, floor,
                                                                            stair, game.stair_position, trap,
                                                                            game.trap_position, key, gate, wall,
                                                                            explorer, list_mw, list_mr, list_sw,
                                                                            list_sr)

    if render:
        graphics.enemy_move_animation(mw_past, mw_new, mr_past, mr_new, sw_past, sw_new, sr_past, sr_new, window,
                                      game, backdrop, floor, stair, game.stair_position, trap, game.trap_position,
                                      key, game.key_position, gate, game.gate, wall, explorer, list_mw, list_mr,
                                      list_sw, list_sr)

    if check_explorer_is_killed(explorer_char, mw_char, mr_char, sw_char, sr_char, game.trap_position):
        if render: pygame.time.delay(500)
        return "LOSE"

    mw_char, list_mw = update_list_character(mw_char, list_mw)
    mr_char, list_mr = update_list_character(mr_char, list_mr)
    if mr_char: mr_char, list_mr = update_lists_character(mw_char, mr_char, list_mr)
    if sw_char: sw_char, list_sw = update_lists_character(mw_char, sw_char, list_sw)
    if sr_char: sr_char, list_sr = update_lists_character(mw_char, sr_char, list_sr)
    if sw_char: sw_char, list_sw = update_lists_character(mr_char, sw_char, list_sw)
    if sr_char: sr_char, list_sr = update_lists_character(mr_char, sr_char, list_sr)
    if sr_char: sr_char, list_sr = update_lists_character(sw_char, sr_char, list_sr)

    x, y = explorer_char.get_x(), explorer_char.get_y()
    if game.maze[x - 1][y] == "S" or game.maze[x + 1][y] == "S" or game.maze[x][y - 1] == "S" or game.maze[x][
        y + 1] == "S":
        print("=== YOU WIN ===")
        return "WIN"
    return "PLAYING"


def draw_text(window, text, size, x, y, color=COLOR_TEXT, center=True):
    font = pygame.font.Font(None, size)
    surface = font.render(text, True, color)
    if center:
        rect = surface.get_rect(center=(x, y))
    else:
        rect = surface.get_rect(topleft=(x, y))
    window.blit(surface, rect)
    return rect


def draw_button(window, text, x, y, w, h, mx, my, action=None, base_color=COLOR_BUTTON):
    btn_rect = pygame.Rect(x, y, w, h)
    hover_color = (min(base_color[0] + 30, 255), min(base_color[1] + 30, 255), min(base_color[2] + 30, 255))
    color = hover_color if btn_rect.collidepoint((mx, my)) else base_color
    pygame.draw.rect(window, color, btn_rect, border_radius=5)
    draw_text(window, text, 20, x + w // 2, y + h // 2, (0, 0, 0))
    if pygame.mouse.get_pressed()[0] and btn_rect.collidepoint((mx, my)): return action
    return None


def draw_auth_popup(window, input_boxes, mode, message=""):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180));
    window.blit(overlay, (0, 0))
    popup_w, popup_h = 420, 380;
    popup_x = (WINDOW_WIDTH - popup_w) // 2;
    popup_y = (WINDOW_HEIGHT - popup_h) // 2
    pygame.draw.rect(window, (220, 200, 120), (popup_x - 5, popup_y - 5, popup_w + 10, popup_h + 10), border_radius=10)
    pygame.draw.rect(window, (80, 60, 40), (popup_x, popup_y, popup_w, popup_h), border_radius=5)
    title = "LOGIN SYSTEM" if mode == "LOGIN" else "REGISTER NEW USER"
    draw_text(window, title, 32, WINDOW_WIDTH // 2, popup_y + 35, (255, 215, 0))
    draw_text(window, "Username:", 24, popup_x + 40, popup_y + 85, (220, 220, 220), center=False)
    input_boxes[0].rect.x = popup_x + 40;
    input_boxes[0].rect.y = popup_y + 115;
    input_boxes[0].rect.w = popup_w - 80
    draw_text(window, "Password:", 24, popup_x + 40, popup_y + 175, (220, 220, 220), center=False)
    input_boxes[1].rect.x = popup_x + 40;
    input_boxes[1].rect.y = popup_y + 205;
    input_boxes[1].rect.w = popup_w - 80
    for box in input_boxes: box.draw(window)
    if message:
        color = (0, 255, 0) if "Success" in message else (255, 80, 80)
        draw_text(window, message, 20, WINDOW_WIDTH // 2, popup_y + 260, color)
    mx, my = pygame.mouse.get_pos();
    action = None;
    button_y = popup_y + 300
    if draw_button(window, "CLOSE", popup_x + 40, button_y, 100, 40, mx, my, "CLOSE"): action = "CLOSE"
    btn_text = "LOGIN" if mode == "LOGIN" else "REGISTER"
    if draw_button(window, btn_text, popup_x + popup_w - 140, button_y, 100, 40, mx, my, "SUBMIT"): action = "SUBMIT"
    toggle_text = "No account? Register" if mode == "LOGIN" else "Have account? Login"
    toggle_rect = draw_text(window, toggle_text, 18, WINDOW_WIDTH // 2, popup_y + 355, (100, 200, 255))
    if pygame.mouse.get_pressed()[0] and toggle_rect.collidepoint((mx, my)):
        pygame.time.delay(200);
        action = "TOGGLE_MODE"
    return action


def draw_save_confirm_popup(window):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    window.blit(overlay, (0, 0))
    popup_w, popup_h = 400, 250
    popup_x = (WINDOW_WIDTH - popup_w) // 2
    popup_y = (WINDOW_HEIGHT - popup_h) // 2
    pygame.draw.rect(window, (50, 50, 50), (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(window, (255, 215, 0), (popup_x, popup_y, popup_w, popup_h), 3, border_radius=10)
    draw_text(window, "DO YOU WANT TO SAVE?", 30, WINDOW_WIDTH // 2, popup_y + 50, (255, 215, 0))

    pygame.display.update()
    pygame.time.delay(200)
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()
        if draw_button(window, "YES (Save & Quit)", popup_x + 50, popup_y + 100, 300, 40, mx, my, "SAVE",
                       (50, 200, 50)): return "SAVE"
        if draw_button(window, "NO (Just Quit)", popup_x + 50, popup_y + 150, 300, 40, mx, my, "NO_SAVE",
                       (200, 50, 50)): return "NO_SAVE"
        if draw_button(window, "CANCEL", popup_x + 50, popup_y + 200, 300, 40, mx, my, "CANCEL",
                       (100, 100, 100)): return "CANCEL"
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "NO_SAVE"
        pygame.display.update()


def continue_game_popup(window, level):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    window.blit(overlay, (0, 0))
    popup_w, popup_h = 400, 250
    popup_x = (WINDOW_WIDTH - popup_w) // 2
    popup_y = (WINDOW_HEIGHT - popup_h) // 2
    pygame.draw.rect(window, (50, 50, 50), (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(window, (255, 215, 0), (popup_x, popup_y, popup_w, popup_h), 3, border_radius=10)
    draw_text(window, "FOUND SAVED LEVEL!", 30, WINDOW_WIDTH // 2, popup_y + 40, (255, 215, 0))
    draw_text(window, f"You are at Level {level}", 22, WINDOW_WIDTH // 2, popup_y + 80, (255, 255, 255))
    pygame.display.update()
    pygame.time.delay(200)
    while pygame.mouse.get_pressed()[0]: pygame.event.pump()
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()
        if draw_button(window, "CONTINUE", popup_x + 30, popup_y + 150, 150, 50, mx, my, "CONTINUE"): return "CONTINUE"
        new_btn_rect = pygame.Rect(popup_x + 220, popup_y + 150, 150, 50)
        color = (255, 100, 100) if new_btn_rect.collidepoint((mx, my)) else (200, 50, 50)
        pygame.draw.rect(window, color, new_btn_rect, border_radius=5)
        draw_text(window, "NEW GAME", 25, new_btn_rect.centerx, new_btn_rect.centery, (255, 255, 255))
        if pygame.mouse.get_pressed()[0] and new_btn_rect.collidepoint((mx, my)): return "NEW_GAME"
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        pygame.display.update()


def draw_continue_or_new_popup(window, saved_level_num):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200));
    window.blit(overlay, (0, 0))
    popup_w, popup_h = 400, 250;
    popup_x = (WINDOW_WIDTH - popup_w) // 2;
    popup_y = (WINDOW_HEIGHT - popup_h) // 2
    pygame.draw.rect(window, (50, 50, 50), (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(window, (255, 215, 0), (popup_x, popup_y, popup_w, popup_h), 3, border_radius=10)
    draw_text(window, "UNFINISHED GAME FOUND!", 30, WINDOW_WIDTH // 2, popup_y + 40, (255, 215, 0))
    draw_text(window, f"Resume Level {saved_level_num}?", 22, WINDOW_WIDTH // 2, popup_y + 80, (200, 200, 200))
    pygame.display.update()
    pygame.time.delay(300)
    pygame.event.clear()
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        mx, my = pygame.mouse.get_pos()
        clicked_now = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_now = True
        btn_cont_rect = pygame.Rect(popup_x + 50, popup_y + 130, 300, 45)
        btn_new_rect = pygame.Rect(popup_x + 50, popup_y + 185, 300, 45)
        c_cont = (100, 200, 255) if btn_cont_rect.collidepoint((mx, my)) else (50, 150, 255)
        pygame.draw.rect(window, c_cont, btn_cont_rect, border_radius=5)
        draw_text(window, "CONTINUE", 20, btn_cont_rect.centerx, btn_cont_rect.centery, (0, 0, 0))
        c_new = (255, 150, 150) if btn_new_rect.collidepoint((mx, my)) else (255, 100, 100)
        pygame.draw.rect(window, c_new, btn_new_rect, border_radius=5)
        draw_text(window, "NEW GAME", 20, btn_new_rect.centerx, btn_new_rect.centery, (0, 0, 0))
        if clicked_now:
            if btn_cont_rect.collidepoint((mx, my)): return "CONTINUE"
            if btn_new_rect.collidepoint((mx, my)): return "NEW_GAME"
        pygame.display.update()


def difficulty_select_popup(window):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220));
    window.blit(overlay, (0, 0))
    popup_w, popup_h = 400, 300;
    popup_x = (WINDOW_WIDTH - popup_w) // 2;
    popup_y = (WINDOW_HEIGHT - popup_h) // 2
    pygame.draw.rect(window, (30, 30, 40), (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(window, (255, 215, 0), (popup_x, popup_y, popup_w, popup_h), 2, border_radius=10)
    draw_text(window, "SELECT DIFFICULTY", 35, WINDOW_WIDTH // 2, popup_y + 40, (255, 215, 0))
    pygame.display.update()
    pygame.time.delay(200)
    while pygame.mouse.get_pressed()[0]: pygame.event.pump()
    clock = pygame.time.Clock()
    while True:
        clock.tick(60);
        mx, my = pygame.mouse.get_pos()
        if draw_button(window, "EASY (Basic)", popup_x + 50, popup_y + 90, 300, 40, mx, my, "EASY"): return 1
        if draw_button(window, "MEDIUM (Balanced)", popup_x + 50, popup_y + 150, 300, 40, mx, my, "MEDIUM"): return 2
        if draw_button(window, "HARD (Pro - Special Maps)", popup_x + 50, popup_y + 210, 300, 40, mx, my,
                       "HARD"): return 3
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        pygame.display.update()


def show_score_popup(window, score):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200));
    window.blit(overlay, (0, 0))
    popup_w, popup_h = 400, 250;
    popup_x = (WINDOW_WIDTH - popup_w) // 2;
    popup_y = (WINDOW_HEIGHT - popup_h) // 2
    pygame.draw.rect(window, (50, 50, 50), (popup_x, popup_y, popup_w, popup_h), border_radius=10)
    pygame.draw.rect(window, (255, 215, 0), (popup_x, popup_y, popup_w, popup_h), 3, border_radius=10)
    draw_text(window, "LEVEL COMPLETE!", 35, WINDOW_WIDTH // 2, popup_y + 50, (0, 255, 0))
    draw_text(window, f"TOTAL SCORE: {score}", 28, WINDOW_WIDTH // 2, popup_y + 100, (255, 255, 255))
    while True:
        mx, my = pygame.mouse.get_pos()
        if draw_button(window, "CONTINUE", popup_x + 125, popup_y + 160, 150, 50, mx, my, "NEXT"): return
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        pygame.display.update()


def draw_game_buttons(window, mx, my):
    undo_rect = pygame.Rect(WINDOW_WIDTH - 80, 10, 70, 30)
    reset_rect = pygame.Rect(WINDOW_WIDTH - 80, 50, 70, 30)
    c_undo = (255, 200, 0) if undo_rect.collidepoint((mx, my)) else COLOR_UNDO
    c_reset = (255, 100, 100) if reset_rect.collidepoint((mx, my)) else COLOR_RESET
    pygame.draw.rect(window, c_undo, undo_rect, border_radius=5)
    pygame.draw.rect(window, c_reset, reset_rect, border_radius=5)
    font = pygame.font.SysFont("arial", 15, bold=True)
    draw_text(window, "UNDO", 20, undo_rect.centerx, undo_rect.centery, (0, 0, 0))
    draw_text(window, "RESET", 20, reset_rect.centerx, reset_rect.centery, (255, 255, 255))
    return undo_rect, reset_rect


def capture_state(explorer, mw, mr, sw, sr, gate):
    state = {
        "explorer": (explorer.get_x(), explorer.get_y()),
        "gate_closed": gate.get("isClosed", True),
        "mw": [(c.get_x(), c.get_y()) for c in mw],
        "mr": [(c.get_x(), c.get_y()) for c in mr],
        "sw": [(c.get_x(), c.get_y()) for c in sw],
        "sr": [(c.get_x(), c.get_y()) for c in sr]
    }
    return state


def restore_state(state, explorer, mw, mr, sw, sr, gate, game):
    explorer.set_x(state["explorer"][0])
    explorer.set_y(state["explorer"][1])
    gate["isClosed"] = state["gate_closed"]
    gate["cellIndex"] = 0 if gate["isClosed"] else -1

    def restore_pos(char_list, pos_list):
        for i in range(min(len(char_list), len(pos_list))):
            char_list[i].set_x(pos_list[i][0])
            char_list[i].set_y(pos_list[i][1])

    restore_pos(mw, state["mw"])
    restore_pos(mr, state["mr"])
    restore_pos(sw, state["sw"])
    restore_pos(sr, state["sr"])


def rungame(window, layout, agent, render, difficulty=1, loaded_data=None, current_level_idx=0):
    game = GameState(layout)
    if loaded_data:
        game.gate["isClosed"] = loaded_data["gate_closed"]
        game.gate["cellIndex"] = 0 if game.gate["isClosed"] else -1
    else:
        game.show_information()

    paths = load_image_path(game.maze_size)
    backdrop = pygame.image.load(paths[0])
    floor = pygame.image.load(paths[1])
    stair = graphics.stairs_spritesheet(paths[6])
    trap = graphics.trap_spritesheet(paths[5])
    key = graphics.key_spritesheet(paths[3])
    gate = graphics.gate_spritesheet(paths[4])
    wall = graphics.wall_spritesheet(paths[2], game.maze_size)
    explorer_sheet = graphics.character_spritesheet(paths[7])
    mummy_white_sheet = graphics.character_spritesheet(paths[8])
    mummy_red_sheet = graphics.character_spritesheet(paths[9])
    scorpion_white_sheet = graphics.character_spritesheet(paths[10])
    scorpion_red_sheet = graphics.character_spritesheet(paths[11])

    start_ex = loaded_data["explorer"] if loaded_data else game.explorer_position
    explorer_char = characters.Explorer(start_ex[0], start_ex[1])
    explorer = {"sprite_sheet": explorer_sheet,
                "coordinates": Cal_coordinates(game, explorer_char.get_x(), explorer_char.get_y()),
                "direction": game.explorer_direction, "cellIndex": 0}

    def setup_enemies(pos_list, sheet, CharClass, load_pos_list=None):
        chars_logic = []
        chars_gfx = []
        count = len(pos_list)
        use_pos = load_pos_list if (load_pos_list and len(load_pos_list) == count) else pos_list
        for i in range(count):
            p = use_pos[i]
            c_logic = CharClass(p[0], p[1])
            c_logic.set_difficulty(difficulty)
            chars_logic.append(c_logic)
            gfx = {"sprite_sheet": sheet, "coordinates": Cal_coordinates(game, p[0], p[1]), "direction": "DOWN",
                   "cellIndex": 0}
            chars_gfx.append(gfx)
        return chars_logic, chars_gfx

    mw_char, list_mw = setup_enemies(game.mummy_white_position, mummy_white_sheet, characters.mummy_white,
                                     loaded_data["mw"] if loaded_data else None)
    mr_char, list_mr = setup_enemies(game.mummy_red_position, mummy_red_sheet, characters.mummy_red,
                                     loaded_data["mr"] if loaded_data else None)
    sw_char, list_sw = setup_enemies(game.scorpion_white_position, scorpion_white_sheet, characters.scorpion_white,
                                     loaded_data["sw"] if loaded_data else None)
    sr_char, list_sr = setup_enemies(game.scorpion_red_position, scorpion_red_sheet, characters.scorpion_red,
                                     loaded_data["sr"] if loaded_data else None)

    history_stack = []

    if render:
        graphics.draw_screen(window, game.maze, backdrop, floor, game.maze_size, game.cell_rect, stair,
                             game.stair_position, trap, game.trap_position, key, game.key_position, gate, game.gate,
                             wall, explorer, list_mw, list_mr, list_sw, list_sr)
        pygame.display.update()

    game_status = "PLAYING"
    clock = pygame.time.Clock()

    last_danger_sound_time = 0
    DANGER_SOUND_COOLDOWN = 3000

    while game_status == "PLAYING":
        clock.tick(30)
        mx, my = pygame.mouse.get_pos()
        if render:
            graphics.draw_screen(window, game.maze, backdrop, floor, game.maze_size, game.cell_rect, stair,
                                 game.stair_position, trap, game.trap_position, key, game.key_position, gate, game.gate,
                                 wall, explorer, list_mw, list_mr, list_sw, list_sr)
            btn_undo, btn_reset = draw_game_buttons(window, mx, my)
            pygame.display.update()

        current_time = pygame.time.get_ticks()
        ex, ey = explorer_char.get_x(), explorer_char.get_y()
        is_near_danger = False
        all_enemies = mw_char + mr_char + sw_char + sr_char
        for enemy in all_enemies:
            dist = (abs(ex - enemy.get_x()) + abs(ey - enemy.get_y())) // 2
            if dist <= 2: is_near_danger = True; break

        if is_near_danger:
            if current_time - last_danger_sound_time > DANGER_SOUND_COOLDOWN:
                play_sfx("danger")
                last_danger_sound_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                action = draw_save_confirm_popup(window)
                if action == "SAVE":
                    save_game_process(layout, explorer_char, mw_char, mr_char, sw_char, sr_char, game.gate,
                                      current_level_idx, difficulty)
                    return "QUIT_TO_MENU"
                elif action == "NO_SAVE":
                    return "QUIT_TO_MENU"
                elif action == "CANCEL":
                    pass

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_reset.collidepoint((mx, my)): return "RETRY"
                if btn_undo.collidepoint((mx, my)):
                    if history_stack:
                        prev_state = history_stack.pop()
                        restore_state(prev_state, explorer_char, mw_char, mr_char, sw_char, sr_char, game.gate, game)
                        explorer["coordinates"] = Cal_coordinates(game, explorer_char.get_x(), explorer_char.get_y())

                        def refresh_gfx(gfx_list, char_list):
                            for i in range(min(len(gfx_list), len(char_list))):
                                gfx_list[i]["coordinates"] = Cal_coordinates(game, char_list[i].get_x(),
                                                                             char_list[i].get_y())

                        refresh_gfx(list_mw, mw_char);
                        refresh_gfx(list_mr, mr_char)
                        refresh_gfx(list_sw, sw_char);
                        refresh_gfx(list_sr, sr_char)
                        continue

            if agent == "KeyboardAgent":
                move_direction = None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        move_direction = "UP"
                    elif event.key == pygame.K_DOWN:
                        move_direction = "DOWN"
                    elif event.key == pygame.K_LEFT:
                        move_direction = "LEFT"
                    elif event.key == pygame.K_RIGHT:
                        move_direction = "RIGHT"
                    elif event.key == pygame.K_SPACE:
                        move_direction = "WAIT"

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not btn_undo.collidepoint((mx, my)) and not btn_reset.collidepoint((mx, my)):
                        char_x = explorer["coordinates"][0] + game.cell_rect // 2
                        char_y = explorer["coordinates"][1] + game.cell_rect // 2
                        diff_x, diff_y = mx - char_x, my - char_y
                        if abs(diff_x) > abs(diff_y):
                            move_direction = "RIGHT" if diff_x > 0 else "LEFT"
                        else:
                            move_direction = "DOWN" if diff_y > 0 else "UP"

                if move_direction:
                    history_stack.append(capture_state(explorer_char, mw_char, mr_char, sw_char, sr_char, game.gate))
                    ex, ey = explorer_char.get_x(), explorer_char.get_y()
                    nex, ney = ex, ey
                    moved = False
                    if move_direction == "UP" and explorer_char.eligible_character_move(game.maze, game.gate, ex, ey,
                                                                                        ex - 2, ey):
                        nex -= 2
                        explorer["direction"] = "UP"
                        moved = True
                    elif move_direction == "DOWN" and explorer_char.eligible_character_move(game.maze, game.gate, ex,
                                                                                            ey, ex + 2, ey):
                        nex += 2
                        explorer["direction"] = "DOWN"
                        moved = True
                    elif move_direction == "LEFT" and explorer_char.eligible_character_move(game.maze, game.gate, ex,
                                                                                            ey, ex, ey - 2):
                        ney -= 2
                        explorer["direction"] = "LEFT"
                        moved = True
                    elif move_direction == "RIGHT" and explorer_char.eligible_character_move(game.maze, game.gate, ex,
                                                                                             ey, ex, ey + 2):
                        ney += 2
                        explorer["direction"] = "RIGHT"
                        moved = True
                    elif move_direction == "WAIT":
                        moved = True

                    if moved:
                        if move_direction != "WAIT":
                            play_sfx("move")
                        explorer_char.move(nex, ney, render, window, game, backdrop, floor, stair, game.stair_position,
                                           trap, game.trap_position, key, game.key_position, gate, game.gate, wall,
                                           explorer, list_mw, list_mr, list_sw, list_sr)
                        game_status = update_enemy_position(window, render, game, backdrop, floor, stair, trap, key,
                                                            gate, wall, explorer, explorer_char, mw_char, mr_char,
                                                            sw_char, sr_char, list_mw, list_mr, list_sw, list_sr)

        if game_status == "WIN":
            play_sfx("win")
            pygame.time.delay(1000)
            return "NEXT_LEVEL"
        elif game_status == "LOSE":
            play_sfx("lose")
            font = pygame.font.SysFont("arial", 50, bold=True)
            text = font.render("GAME OVER", True, (255, 0, 0))
            rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
            window.blit(text, rect);
            pygame.display.update();
            pygame.time.delay(2000)
            return "RETRY"


# --- HÀM GENERATE MAZE SCREEN ---
def generate_maze_screen(window):
    # Setup Variables
    selected_size = 6  # Default
    input_density = InputBox(WINDOW_WIDTH // 2 + 20, 200, 100, 32, text='50')  # Default 50%
    input_density.active = True  # Focus ngay
    message = ""

    clock = pygame.time.Clock()

    while True:
        window.fill(COLOR_BG)
        draw_text(window, "GENERATE MAZE", 40, WINDOW_WIDTH // 2, 50, (255, 215, 0))
        draw_text(window, "(Escape to Back)", 20, WINDOW_WIDTH // 2, 80, (150, 150, 150))

        mx, my = pygame.mouse.get_pos()

        # --- CHỌN KÍCH THƯỚC MÊ CUNG ---
        draw_text(window, "Select Size:", 25, WINDOW_WIDTH // 2, 130, (255, 255, 255))

        sizes = [6, 8, 10]
        btn_start_x = WINDOW_WIDTH // 2 - 110
        for i, s in enumerate(sizes):
            color = (0, 200, 0) if selected_size == s else (100, 100, 100)
            if draw_button(window, f"{s}x{s}", btn_start_x + i * 80, 150, 60, 30, mx, my, s, color):
                selected_size = s

        # --- NHẬP TỈ LỆ TƯỜNG ---
        draw_text(window, "Wall Density (%):", 25, WINDOW_WIDTH // 2 - 80, 215, (255, 255, 255))
        input_density.update()
        input_density.draw(window)
        draw_text(window, "(0% = Open, 100% = Full Maze)", 18, WINDOW_WIDTH // 2, 250, (180, 180, 180))

        # --- GENERATE BUTTON ---
        gen_btn_color = (255, 69, 0)
        if draw_button(window, "GENERATE & PLAY", WINDOW_WIDTH // 2 - 100, 300, 200, 50, mx, my, "GENERATE",
                       gen_btn_color):
            # KIỂM TRA MẬT ĐỘ TƯỜNG
            try:
                den = int(input_density.text)
                if den < 0: den = 0
                if den > 100: den = 100

                # Show Loading Text
                pygame.draw.rect(window, COLOR_BG, (0, 360, WINDOW_WIDTH, 50))
                draw_text(window, "Generating... Please Wait...", 30, WINDOW_WIDTH // 2, 380, (0, 255, 255))
                pygame.display.update()

                # CALL GENERATOR
                generated_file = maze_generator.create_valid_level(selected_size, den)
                return generated_file  # Trả về tên file để play

            except ValueError:
                message = "Invalid Density! Enter 0-100"

        # Message
        if message:
            draw_text(window, message, 20, WINDOW_WIDTH // 2, 400, (255, 100, 100))

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "BACK"
            input_density.handle_event(event)

        pygame.display.update()
        clock.tick(60)


def practice_menu_screen(window):
    class MenuItem:
        def __init__(self, text, y_pos):
            self.text = text;
            self.base_pos = (WINDOW_WIDTH // 2, y_pos)
            self.font = pygame.font.SysFont("comicsansms", 28, bold=True)
            self.current_scale = 1.0;
            self.target_scale = 1.0;
            self.rect = pygame.Rect(0, 0, 0, 0);
            self.hovered = False

        def update(self, mouse_pos):
            self.hovered = self.rect.collidepoint(mouse_pos)
            if self.hovered:
                self.target_scale = 1.2; color = (255, 215, 0)
            else:
                self.target_scale = 1.0; color = (255, 255, 255)
            self.current_scale += (self.target_scale - self.current_scale) * 0.2
            base_surf = self.font.render(self.text, True, color)
            new_w = int(base_surf.get_width() * self.current_scale);
            new_h = int(base_surf.get_height() * self.current_scale)
            scaled_surf = pygame.transform.smoothscale(base_surf, (new_w, new_h));
            self.rect = scaled_surf.get_rect(center=self.base_pos)
            return scaled_surf, self.rect

    items = [MenuItem("ALL LEVELS", 200), MenuItem("GENERATE MAZE", 280), MenuItem("BACK", 400)]
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        window.fill(COLOR_BG)
        draw_text(window, "PRACTICE MODE", 40, WINDOW_WIDTH // 2, 100, (255, 215, 0))
        mx, my = pygame.mouse.get_pos()
        for item in items:
            surf, rect = item.update((mx, my))
            window.blit(surf, rect)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for item in items:
                    if item.hovered:
                        if item.text == "BACK": return "BACK"
                        if item.text == "ALL LEVELS": return "ALL_LEVELS"
                        if item.text == "GENERATE MAZE": return "GENERATE_MENU"
        pygame.display.update()


def all_level_select_screen(window):
    try:
        available_files = get_sorted_levels(1) + get_sorted_levels(3)  # Get All
    except:
        return None
    pygame.time.delay(200)
    pygame.event.clear()

    run = True
    scroll_y = 0
    while run:
        window.fill(COLOR_BG)
        draw_text(window, "ALL LEVELS", 40, WINDOW_WIDTH // 2, 50, COLOR_HOVER)
        draw_text(window, "(Escape to Back)", 20, WINDOW_WIDTH // 2, 80, (150, 150, 150))
        if not available_files:
            draw_text(window, "No levels found!", 30, WINDOW_WIDTH // 2, 200, (200, 100, 100))
        mx, my = pygame.mouse.get_pos()
        start_y = 120 + scroll_y
        clicked_now = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "BACK"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_now = True
            if event.type == pygame.MOUSEWHEEL:
                scroll_y += event.y * 20
                max_scroll = -(len(available_files) * 40 - 300)
                if scroll_y > 0: scroll_y = 0;
                if max_scroll > 0: max_scroll = 0
                if scroll_y < max_scroll: scroll_y = max_scroll

        for i, filename in enumerate(available_files):
            y_pos = start_y + i * 40
            if 100 < y_pos < 450:
                display_name = filename.replace(".txt", "").replace("map_", "Level ").replace("_", "-")
                color = COLOR_HOVER if 150 < mx < 350 and y_pos - 15 < my < y_pos + 15 else COLOR_TEXT
                btn_rect = draw_text(window, display_name, 30, WINDOW_WIDTH // 2, y_pos, color)
                if clicked_now and btn_rect.collidepoint((mx, my)): return filename
        pygame.display.update()


def music_select_screen(window, db, current_user):
    music_data = get_music_files_with_thresholds()
    user_score = 0
    if current_user:
        user_score = db.get_score(current_user)

    pygame.time.delay(200)
    pygame.event.clear()

    run = True
    scroll_y = 0
    while run:
        window.fill(COLOR_BG)
        draw_text(window, "MUSIC SELECT", 35, WINDOW_WIDTH // 2, 40, COLOR_HOVER)
        draw_text(window, f"Your Score: {user_score}", 25, WINDOW_WIDTH // 2, 70, (0, 255, 255))
        draw_text(window, "(Escape to Back)", 20, WINDOW_WIDTH // 2, 95, (150, 150, 150))

        if not music_data:
            draw_text(window, "No music found!", 25, WINDOW_WIDTH // 2, 200, (200, 100, 100))

        mx, my = pygame.mouse.get_pos()
        clicked_now = False

        stop_btn_rect = pygame.Rect(WINDOW_WIDTH - 100, 10, 80, 40)
        c_stop = (200, 50, 50) if stop_btn_rect.collidepoint((mx, my)) else (150, 50, 50)
        pygame.draw.rect(window, c_stop, stop_btn_rect, border_radius=5)
        draw_text(window, "MUTE", 20, stop_btn_rect.centerx, stop_btn_rect.centery, (255, 255, 255))

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "BACK"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_now = True
            if event.type == pygame.MOUSEWHEEL:
                scroll_y += event.y * 20
                max_scroll = -(len(music_data) * 50 - 300)
                if scroll_y > 0: scroll_y = 0;
                if max_scroll > 0: max_scroll = 0
                if scroll_y < max_scroll: scroll_y = max_scroll

        if clicked_now and stop_btn_rect.collidepoint((mx, my)):
            stop_bg_music()

        start_y = 130 + scroll_y
        for i, (filename, threshold) in enumerate(music_data):
            y_pos = start_y + i * 50
            if 100 < y_pos < 450:
                is_unlocked = user_score >= threshold
                is_playing = (filename == current_music_file)
                if is_unlocked:
                    color = (0, 255, 0) if is_playing else (
                        COLOR_HOVER if 50 < mx < 450 and y_pos - 20 < my < y_pos + 20 else COLOR_TEXT)
                    prefix = ">> " if is_playing else ""
                    display_text = f"{prefix}{filename}"
                else:
                    color = COLOR_LOCKED
                    display_text = f"LOCKED (Need {threshold} pts)"
                btn_rect = draw_text(window, display_text, 26, WINDOW_WIDTH // 2, y_pos, color)
                if is_unlocked and clicked_now and btn_rect.collidepoint((mx, my)):
                    play_bg_music(filename)
        pygame.display.update()


def leaderboard_screen(window, db):
    pygame.time.delay(200)
    pygame.event.clear()
    leaderboard_data = db.get_leaderboard()
    while True:
        window.fill(COLOR_BG)
        draw_text(window, "TOP PLAYERS", 40, WINDOW_WIDTH // 2, 50, (255, 215, 0))
        draw_text(window, "(Escape to Back)", 20, WINDOW_WIDTH // 2, 85, (150, 150, 150))
        pygame.draw.line(window, (255, 255, 255), (50, 110), (WINDOW_WIDTH - 50, 110), 2)
        draw_text(window, "RANK", 25, 80, 130, (200, 200, 200))
        draw_text(window, "PLAYER NAME", 25, WINDOW_WIDTH // 2, 130, (200, 200, 200))
        draw_text(window, "SCORE", 25, WINDOW_WIDTH - 80, 130, (200, 200, 200))
        pygame.draw.line(window, (255, 255, 255), (50, 150), (WINDOW_WIDTH - 50, 150), 2)
        start_y = 170
        if not leaderboard_data:
            draw_text(window, "No data yet!", 30, WINDOW_WIDTH // 2, 250, (150, 150, 150))
        else:
            for i, (name, score) in enumerate(leaderboard_data):
                y_pos = start_y + i * 40
                if i < 7:
                    color = (255, 215, 0) if i == 0 else (192, 192, 192) if i == 1 else (205, 127, 50) if i == 2 else (
                        255, 255, 255)
                    draw_text(window, f"#{i + 1}", 25, 80, y_pos, color)
                    draw_text(window, str(name).upper(), 25, WINDOW_WIDTH // 2, y_pos, color)
                    draw_text(window, str(score), 25, WINDOW_WIDTH - 80, y_pos, color)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "BACK"
        pygame.display.update()


def start_screen(window):
    db = UserManager()
    current_user = None
    user_data = None
    menu_bg_path = os.path.join(image_path, "menu_start.png")
    bg_image = None
    try:
        bg_image = pygame.image.load(menu_bg_path); bg_image = pygame.transform.scale(bg_image,
                                                                                      (WINDOW_WIDTH, WINDOW_HEIGHT))
    except:
        pass
    input_name = InputBox(0, 0, 290, 32);
    input_code = InputBox(0, 0, 290, 32);
    input_boxes = [input_name, input_code]
    is_popup_open = False;
    popup_mode = "LOGIN";
    popup_message = "";
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        if bg_image:
            window.blit(bg_image, (0, 0))
        else:
            window.fill(COLOR_BG)
        mx, my = pygame.mouse.get_pos()
        s = pygame.Surface((WINDOW_WIDTH, 40));
        s.set_alpha(150)
        s.fill((0, 0, 0))
        window.blit(s, (0, 350))
        if current_user:
            draw_text(window, f"WELCOME, {current_user.upper()}!", 30, WINDOW_WIDTH // 2, 370, (0, 255, 0))
            score = user_data.get("score", 0)
            draw_text(window, f"Level: {user_data.get('max_level', 1)} | Score: {score}", 20, WINDOW_WIDTH // 2, 395,
                      (200, 255, 200))
        else:
            draw_text(window, "UNREGISTERED VERSION", 30, WINDOW_WIDTH // 2, 370, (255, 255, 0))
            reg_rect = pygame.Rect(100, 370, 300, 30)
            if reg_rect.collidepoint((mx, my)): draw_text(window, "Click to Login / Register", 18, WINDOW_WIDTH // 2,
                                                          390, (200, 200, 255))
        bar_x, bar_y, bar_w, bar_h = 100, 410, 300, 40;
        play_btn_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
        btn_color = (0, 200, 0) if play_btn_rect.collidepoint((mx, my)) else (0, 100, 0)
        pygame.draw.rect(window, btn_color, play_btn_rect, border_radius=5)
        draw_text(window, "CLICK HERE TO PLAY", 25, WINDOW_WIDTH // 2, bar_y + 20, (255, 255, 255))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if is_popup_open:
                input_name.handle_event(event); input_code.handle_event(event)
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if play_btn_rect.collidepoint((mx, my)):
                        if not current_user:
                            db.register("guest", "guest")
                            _, guest_data = db.login("guest", "guest")
                            return {"action": "MODE_SELECT", "user": "guest", "data": guest_data}
                        return {"action": "MODE_SELECT", "user": current_user, "data": user_data}
                    if not current_user and reg_rect.collidepoint((mx, my)):
                        is_popup_open = True
                        popup_message = ""
                        input_name.text = ""
                        input_code.text = ""
                        input_name.txt_surface = input_name.font.render("", True, (0, 255, 0))
                        input_code.txt_surface = input_code.font.render("", True, (0, 255, 0))
        if is_popup_open:
            input_name.update()
            input_code.update()
            action = draw_auth_popup(window, input_boxes, popup_mode, popup_message)
            if action == "CLOSE":
                is_popup_open = False
            elif action == "TOGGLE_MODE":
                popup_mode = "REGISTER" if popup_mode == "LOGIN" else "LOGIN"; popup_message = ""
            elif action == "SUBMIT":
                name = input_name.text.strip();
                code = input_code.text.strip()
                if not name or not code:
                    popup_message = "Please enter info!"
                else:
                    if popup_mode == "REGISTER":
                        success, msg = db.register(name, code);
                        popup_message = msg
                        if success: popup_mode = "LOGIN"; popup_message = "Success! Please Login."
                    elif popup_mode == "LOGIN":
                        success, result = db.login(name, code)
                        if success:
                            current_user = name; user_data = result; is_popup_open = False
                        else:
                            popup_message = result
        pygame.display.update()


def mode_select_screen(window):
    mode_bg_path = os.path.join(image_path, "menu_mode_select.png")
    bg_image = None
    try:
        bg_image = pygame.image.load(mode_bg_path); bg_image = pygame.transform.scale(bg_image,
                                                                                      (WINDOW_WIDTH, WINDOW_HEIGHT))
    except:
        pass

    class MenuItem:
        def __init__(self, text, y_pos):
            self.text = text;
            self.base_pos = (WINDOW_WIDTH // 2, y_pos)
            self.font = pygame.font.SysFont("comicsansms", 22, bold=True)
            self.current_scale = 1.0
            self.target_scale = 1.0
            self.rect = pygame.Rect(0, 0, 0, 0)
            self.hovered = False

        def update(self, mouse_pos):
            self.hovered = self.rect.collidepoint(mouse_pos)
            if self.hovered:
                self.target_scale = 1.2; color = (255, 215, 0)
            else:
                self.target_scale = 1.0; color = (255, 255, 255)
            self.current_scale += (self.target_scale - self.current_scale) * 0.2
            base_surf = self.font.render(self.text, True, color)
            new_w = int(base_surf.get_width() * self.current_scale)
            new_h = int(base_surf.get_height() * self.current_scale)
            scaled_surf = pygame.transform.smoothscale(base_surf, (new_w, new_h))
            self.rect = scaled_surf.get_rect(center=self.base_pos)
            return scaled_surf, self.rect

    items = [
        MenuItem("CLASSIC MODE", 260),
        MenuItem("PRACTICE", 295),
        MenuItem("MUSIC", 330),
        MenuItem("LEADERBOARD", 365),
        MenuItem("LOGOUT", 400),
        MenuItem("QUIT GAME", 435)
    ]

    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        if bg_image:
            window.blit(bg_image, (0, 0))
        else:
            window.fill(COLOR_BG)
        mx, my = pygame.mouse.get_pos()
        for item in items:
            surf, rect = item.update((mx, my))
            shadow_surf = pygame.transform.scale(surf, (rect.width, rect.height))
            shadow_surf.fill((0, 0, 0, 50), special_flags=pygame.BLEND_RGBA_MULT)
            window.blit(shadow_surf, (rect.x + 2, rect.y + 2))
            window.blit(surf, rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for item in items:
                    if item.hovered:
                        if item.text == "CLASSIC MODE":
                            return "START_CLASSIC"
                        elif item.text == "PRACTICE":
                            return "PRACTICE_MENU"
                        elif item.text == "MUSIC":
                            return "MUSIC_MENU"
                        elif item.text == "LEADERBOARD":
                            return "LEADERBOARD_MENU"
                        elif item.text == "LOGOUT":
                            return "LOGOUT"
                        elif item.text == "QUIT GAME":
                            return "QUIT"
        pygame.display.update()


# =============================================================================
# HÀM CHẠY CHÍNH (GRAPHIC MODE WRAPPER)
# =============================================================================

def run_graphic_mode():
    pygame.init()
    pygame.mixer.init()  # INITIALIZE MIXER FOR MUSIC

    # --- LOAD SOUND EFFECTS ---
    global game_sounds
    game_sounds = load_game_sounds()

    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Code Phantom - Mummy Maze Clone")

    # --- TỰ ĐỘNG PHÁT NHẠC ---
    init_startup_music()

    current_state = "START_SCREEN"
    selected_file = None;
    current_user_name = None;
    current_user_data = None
    level_list = [];
    current_level_idx = 0;
    db = UserManager();
    selected_difficulty = 1
    is_replay_mode = False
    loaded_game_data = None

    while True:
        if current_state == "START_SCREEN":
            result = start_screen(window)
            if result == "QUIT":
                break
            elif isinstance(result, dict) and result["action"] == "MODE_SELECT":
                current_state = "MODE_SELECT";
                current_user_name = result["user"];
                current_user_data = result["data"]
                print(f"Logged in: {current_user_name}")

        elif current_state == "MODE_SELECT":
            result = mode_select_screen(window)
            if result == "QUIT":
                break
            elif result == "LOGOUT":
                current_user_name = None
                current_user_data = None
                current_state = "START_SCREEN"
                continue
            elif result == "PRACTICE_MENU":
                current_state = "PRACTICE_MENU"
            elif result == "MUSIC_MENU":
                current_state = "MUSIC_MENU"
            elif result == "LEADERBOARD_MENU":
                current_state = "LEADERBOARD"
            elif result == "START_CLASSIC":
                # --- KIỂM TRA SAVE GAME ---
                saved_data = load_game_data()
                choice = "NEW_GAME"

                if saved_data:
                    lvl_num = saved_data.get("level_idx", 0) + 1
                    choice = draw_continue_or_new_popup(window, lvl_num)

                if choice == "CONTINUE":
                    loaded_game_data = saved_data
                    selected_file = saved_data["layout"]
                    current_level_idx = saved_data.get("level_idx", 0)
                    selected_difficulty = saved_data.get("difficulty", 1)  # Lấy độ khó từ save file
                    is_replay_mode = False
                    # Load map tương ứng độ khó
                    level_list = get_sorted_levels(selected_difficulty)
                    current_state = "PLAY"

                else:  # NEW GAME
                    clear_save_file()
                    loaded_game_data = None
                    is_replay_mode = False
                    start_level = 1;
                    saved_level = 1

                    if current_user_name: saved_level = db.get_level(current_user_name)

                    if saved_level > 1:
                        choice_db = continue_game_popup(window, saved_level)
                        if choice_db == "CONTINUE":
                            start_level = saved_level
                            selected_difficulty = db.get_difficulty(current_user_name)
                        elif choice_db == "NEW_GAME":
                            selected_difficulty = difficulty_select_popup(window)
                            db.update_difficulty(current_user_name, selected_difficulty)
                            start_level = 1
                            if current_user_name: db.reset_level(current_user_name)
                    else:
                        selected_difficulty = difficulty_select_popup(window)
                        db.update_difficulty(current_user_name, selected_difficulty)

                    # Load map sau khi đã có selected_difficulty
                    level_list = get_sorted_levels(selected_difficulty)
                    if not level_list:
                        print("Không tìm thấy map cho độ khó này!")
                        # Fallback về map thường nếu không thấy map hard
                        level_list = get_sorted_levels(1)

                    current_level_idx = start_level - 1
                    if current_level_idx >= len(level_list): current_level_idx = 0
                    selected_file = level_list[current_level_idx]
                    current_state = "PLAY"

        elif current_state == "MUSIC_MENU":
            result = music_select_screen(window, db, current_user_name)
            if result == "QUIT":
                break
            elif result == "BACK":
                current_state = "MODE_SELECT"

        elif current_state == "LEADERBOARD":
            result = leaderboard_screen(window, db)
            if result == "QUIT":
                break
            elif result == "BACK":
                current_state = "MODE_SELECT"

        elif current_state == "PRACTICE_MENU":
            result = practice_menu_screen(window)
            if result == "QUIT":
                break
            elif result == "BACK":
                current_state = "MODE_SELECT"
            elif result == "ALL_LEVELS":
                current_state = "REPLAY_SELECT"
            elif result == "GENERATE_MENU":
                current_state = "GENERATE_MENU"

        elif current_state == "GENERATE_MENU":
            result = generate_maze_screen(window)
            if result == "QUIT":
                break
            elif result == "BACK":
                current_state = "PRACTICE_MENU"
            elif result:
                # Result trả về là tên file map (custom_gen.txt)
                selected_file = result
                is_replay_mode = True  # Coi như là chế độ luyện tập
                selected_difficulty = 1  # Mặc định
                loaded_game_data = None
                current_state = "PLAY"

        elif current_state == "REPLAY_SELECT":
            result = all_level_select_screen(window)
            if result == "QUIT":
                break
            elif result == "BACK":
                current_state = "PRACTICE_MENU"
            elif result:
                selected_file = result
                is_replay_mode = True
                selected_difficulty = db.get_difficulty(current_user_name)
                loaded_game_data = None
                current_state = "PLAY"

        elif current_state == "PLAY":
            try:
                result = rungame(window, selected_file, "KeyboardAgent", True, selected_difficulty, loaded_game_data,
                                 current_level_idx)
            except Exception as e:
                print(f"Lỗi: {e}"); import traceback; traceback.print_exc(); current_state = "MODE_SELECT"; continue

            if result == "QUIT":
                break
            elif result == "QUIT_TO_MENU":
                current_state = "MODE_SELECT"
            elif result == "RETRY":
                loaded_game_data = None
            elif result == "NEXT_LEVEL":
                print(f"Hoàn thành level: {selected_file}")
                clear_save_file()
                loaded_game_data = None

                if current_user_name and not is_replay_mode:
                    db.add_score(current_user_name, 100)
                    db.update_progress(current_user_name, current_level_idx + 2)
                    new_score = db.get_score(current_user_name)
                    show_score_popup(window, new_score)
                    current_level_idx += 1
                    if current_level_idx < len(level_list):
                        selected_file = level_list[current_level_idx]
                    else:
                        print("WIN ALL!"); current_state = "MODE_SELECT"
                elif is_replay_mode:
                    print("Practice Completed!")
                    current_state = "REPLAY_SELECT"

    pygame.quit()
    sys.exit()


# =============================================================================
# KHỞI ĐỘNG (LAUNCHER)
# =============================================================================

if __name__ == '__main__':
    print("=" * 40)
    print(" MUMMY MAZE DELUXE - LAUNCHER")
    print("=" * 40)
    print("1. Chạy bản đồ họa đẹp (Graphic Mode)")
    print("2. Chạy bản ASCII (Console Mode)")
    print("=" * 40)

    choice = input("Lựa chọn của bạn (1/2): ")

    if choice == '2':
        # Chạy file ascii_game.py đã import
        ascii_game.run_ascii_game()
    else:
        # Mặc định chạy bản Graphic
        run_graphic_mode()