import graphics
import pygame
from collections import deque
import random

# --- THUẬT TOÁN TÌM ĐƯỜNG (BFS) ---
def bfs_find_next_step(start_pos, target_pos, maze, gate):
    # start_pos, target_pos: tuple (row, col)
    rows = len(maze)
    cols = len(maze[0])
    if start_pos == target_pos: return start_pos

    queue = deque([ [start_pos] ])
    visited = {start_pos}

    while queue:
        path = queue.popleft()
        current_node = path[-1]
        cx, cy = current_node

        if (cx, cy) == target_pos:
            return path[1] if len(path) > 1 else target_pos

        moves = [(-2, 0), (2, 0), (0, -2), (0, 2)]
        
        for dx, dy in moves:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < rows and 0 <= ny < cols:
                blocked = False
                if dx == 2: # Down
                    if maze[cx+1][cy] == "%" or (maze[cx+1][cy] == "G" and gate["isClosed"]): blocked = True
                elif dx == -2: # Up
                    if maze[cx-1][cy] == "%" or (maze[cx-1][cy] == "G" and gate["isClosed"]): blocked = True
                elif dy == 2: # Right
                    if maze[cx][cy+1] == "%": blocked = True
                elif dy == -2: # Left
                    if maze[cx][cy-1] == "%": blocked = True
                
                if not blocked and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    new_path = list(path)
                    new_path.append((nx, ny))
                    queue.append(new_path)
    
    return start_pos 

# --- BASE CLASSES ---
class character:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def check_same_position(self, character):
        return (character.x == self.x) and (character.y == self.y)

    def eligible_character_move(self, maze, gate, x, y, new_x, new_y):
        if new_x < 0 or new_x >= len(maze) or new_y < 0 or new_y >= len(maze[0]): return False
        if new_x == x + 2: # XUỐNG
            if maze[x+1][y] == "%" or (maze[x + 1][y] == "G" and gate["isClosed"]): return False
        if new_x == x - 2: # LÊN
            if maze[x-1][y] == "%" or (maze[x - 1][y] == "G" and gate["isClosed"]): return False
        if new_y == y + 2: # QUA PHẢI
            if maze[x][y+1] == "%": return False
        if new_y == y - 2: # QUA TRÁI
            if maze[x][y-1] == "%": return False
        return True

    def move_animation(self, x, y, screen, game, backdrop, floor, stair, stair_position, trap, trap_position,
                key, key_position, gate_sheet, gate, wall, explorer, mummy_white, mummy_red, scorpion_white, scorpion_red):
        raise NotImplementedError("This is base class method")

    def move_xy(self, new_x, new_y):
        self.x = new_x
        self.y = new_y

    def move(self, new_x, new_y, render, screen, game, backdrop, floor, stair, stair_position, trap, trap_position,
                key, key_position, gate_sheet, gate, wall, explorer, mummy_white, mummy_red, scorpion_white, scorpion_red):
        if render and (new_x != self.x or new_y != self.y) :
            self.move_animation(new_x, new_y, screen, game, backdrop, floor, stair, stair_position, trap, trap_position,
                key, key_position, gate_sheet, gate, wall, explorer, mummy_white, mummy_red, scorpion_white, scorpion_red)
        self.x = new_x
        self.y = new_y
    
    def set_x(self, x): self.x = x
    def set_y(self, y): self.y = y
    def get_x(self): return self.x
    def get_y(self): return self.y

class Explorer(character):
    def move_animation(self, x, y, screen, game, backdrop, floor, stair, stair_position, trap, trap_position,
                key, key_position, gate_sheet, gate, wall, explorer, mummy_white, mummy_red, scorpion_white, scorpion_red):
        explorer_start_x = game.coordinate_screen_x + game.cell_rect * (self.y // 2)
        explorer_start_y = game.coordinate_screen_y + game.cell_rect * (self.x // 2)
        if game.maze[x - 1][y] == "%" or game.maze[x - 1][y] == "G":
            explorer_start_y += 3
        explorer["coordinates"] = [explorer_start_x, explorer_start_y]
        step_stride = game.cell_rect // 5
        coordinates = list(explorer["coordinates"])
        
        for i in range(6):
            pygame.event.pump()
            if i < 5:
                if explorer["direction"] == "UP": coordinates[1] -= step_stride
                if explorer["direction"] == "DOWN": coordinates[1] += step_stride
                if explorer["direction"] == "LEFT": coordinates[0] -= step_stride
                if explorer["direction"] == "RIGHT": coordinates[0] += step_stride
            explorer["coordinates"] = list(coordinates)
            explorer["cellIndex"] = i % 5
            graphics.draw_screen(screen, game.maze, backdrop, floor, game.maze_size, game.cell_rect, stair, stair_position,
                                trap, trap_position, key, key_position, gate_sheet, gate, wall,
                                explorer, mummy_white, mummy_red, scorpion_white, scorpion_red)
            pygame.time.delay(100)
            pygame.display.update()

class enemy(character):
    def __init__(self, x, y, difficulty=1):
        self.attempt = 0
        self.step_count = 0
        self.difficulty = difficulty 
        super().__init__(x, y)

    def set_difficulty(self, diff):
        self.difficulty = diff

    # --- LOGIC ĐIỀU KHIỂN ---
    def ai_move(self, maze, gate, explorer, is_horizontal_first):
        
        # EASY
        if self.difficulty == 1:
            return self.move_greedy(maze, gate, explorer, is_horizontal_first)
        
        # MEDIUM (CHASE)
        elif self.difficulty == 2:
            return self.move_smart_bfs(maze, gate, explorer)

        # HARD (ZONE DEFENSE + PATROL)
        elif self.difficulty == 3:
            s_pos = None
            for r in range(len(maze)):
                for c in range(len(maze[0])):
                    if maze[r][c] == 'S':
                        s_pos = (r, c); break
                if s_pos: break
            
            target_pos = None
            if s_pos:
                neighbors = [(s_pos[0]+1, s_pos[1]), (s_pos[0]-1, s_pos[1]), 
                             (s_pos[0], s_pos[1]+1), (s_pos[0], s_pos[1]-1)]
                for nr, nc in neighbors:
                    if 0 <= nr < len(maze) and 0 <= nc < len(maze[0]):
                        if maze[nr][nc] != '%': 
                             target_pos = (nr, nc); break
            
            dist_to_player = abs(self.x - explorer.x) + abs(self.y - explorer.y)
            
            # Tấn công nếu người chơi gần
            if not target_pos or dist_to_player <= 6:
                return self.move_smart_bfs(maze, gate, explorer)
            
            # Nếu người chơi xa: Chạy về cửa
            else:
                next_pos = bfs_find_next_step((self.x, self.y), target_pos, maze, gate)
                
                # NẾU CÒN ĐƯỜNG ĐẾN CỬA -> ĐI TIẾP
                if next_pos != (self.x, self.y):
                    self.move_xy(next_pos[0], next_pos[1])
                    self.step_count += 1
                
                # NẾU ĐÃ ĐỨNG TẠI CỬA (next_pos == current) -> ĐI TUẦN (PATROL)
                else:
                    # Tìm tất cả các ô xung quanh có thể đi được
                    valid_moves = []
                    directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
                    for dx, dy in directions:
                        nx, ny = self.x + dx, self.y + dy
                        if self.eligible_character_move(maze, gate, self.x, self.y, nx, ny):
                            valid_moves.append((nx, ny))
                    
                    # Chọn ngẫu nhiên 1 ô để bước sang (giả vờ đi tuần)
                    if valid_moves:
                        choice = random.choice(valid_moves)
                        self.move_xy(choice[0], choice[1])
                        self.step_count += 1
                        
                return self

        return self

    def move_greedy(self, maze, gate, explorer, is_horizontal_first):
        if is_horizontal_first:
            if self.get_y() != explorer.get_y():
                self = self.move_Horizontal(maze, gate, explorer)
                if self.step_count >= 1: return self 
            self = self.move_Vertical(maze, gate, explorer)
        else:
            if self.get_x() != explorer.get_x():
                self = self.move_Vertical(maze, gate, explorer)
                if self.step_count >= 1: return self 
            self = self.move_Horizontal(maze, gate, explorer)
        return self

    def move_smart_bfs(self, maze, gate, explorer):
        next_pos = bfs_find_next_step((self.x, self.y), (explorer.x, explorer.y), maze, gate)
        if next_pos != (self.x, self.y):
            self.move_xy(next_pos[0], next_pos[1])
            self.step_count += 1
        return self

    def move_Vertical(self, maze, gate, explorer):
        if self.step_count >= 1: return self 
        diff = explorer.get_x() - self.get_x()
        if diff == 0: return self
        new_x = self.get_x() + 2 * sign(diff)
        new_y = self.get_y()
        if self.eligible_character_move(maze, gate, self.get_x(), self.get_y(), new_x, new_y):
            self.move_xy(new_x, new_y)
            self.step_count += 1
        else:
            self.attempt += 1
        return self

    def move_Horizontal(self, maze, gate, explorer):
        if self.step_count >= 1: return self 
        diff = explorer.get_y() - self.get_y()
        if diff == 0: return self
        new_x = self.get_x()
        new_y = self.get_y() + 2 * sign(diff)
        if self.eligible_character_move(maze, gate, self.get_x(), self.get_y(), new_x, new_y):
            self.move_xy(new_x, new_y)
            self.step_count += 1
        else:
            self.attempt += 1
        return self

    def set_attempt(self, attempt): self.attempt = attempt
    def get_attempt(self): return self.attempt
    def set_step_count(self, step_count): self.step_count = step_count
    def get_step_count(self): return self.step_count

class mummy_white(enemy):
    def white_move(self, maze, gate, explorer):
        if self.check_same_position(explorer): return self
        self.set_step_count(0); self.set_attempt(0) 
        return self.ai_move(maze, gate, explorer, is_horizontal_first=True)

class mummy_red(enemy):
    def red_move(self, maze, gate, explorer):
        if self.check_same_position(explorer): return self
        self.set_step_count(0); self.set_attempt(0) 
        return self.ai_move(maze, gate, explorer, is_horizontal_first=False)

class scorpion_white(mummy_white): pass
class scorpion_red(mummy_red): pass

def sign(x):
    if x == 0: return 0
    return x // abs(x)