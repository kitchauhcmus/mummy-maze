import os


# Ký tự đại diện
CHAR_PLAYER = "P"
CHAR_MUMMY = "M"
CHAR_WALL = "█"
CHAR_FLOOR = " "
CHAR_GOAL = "E"
CHAR_KEY = "K"
CHAR_GATE_OPEN = "="
CHAR_GATE_CLOSED = "X"

project_path = os.path.dirname(os.path.abspath(__file__))
map_path = os.path.join(project_path, "map", "maze")
agent_path = os.path.join(project_path, "map", "agents")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_level(filename):
    # Đọc Map
    maze = []
    try:
        with open(os.path.join(map_path, filename), "r") as f:
            for line in f:
                row = []
                for char in line.strip():
                    if char == "%": row.append(CHAR_WALL)
                    elif char == ".": row.append(CHAR_FLOOR)
                    elif char == "S": row.append(CHAR_GOAL)
                    elif char == "K": row.append(CHAR_KEY)
                    elif char == "G": row.append(CHAR_GATE_CLOSED)
                    else: row.append(char)
                maze.append(row)
    except FileNotFoundError:
        print(f"Error: Map {filename} not found.")
        return None, None, None

    # Đọc Vị trí (Giả lập đơn giản: Chỉ lấy Player và 1 Mummy đầu tiên)
    player_pos = [2, 2]
    mummy_pos = []
    
    agent_file = filename  # Tên file agent thường trùng tên file map
    try:
        with open(os.path.join(agent_path, agent_file), "r") as f:
            for line in f:
                parts = line.split()
                if not parts: continue
                if parts[0] == "E":
                    player_pos = [int(parts[1]), int(parts[2])]
                elif parts[0] in ["MW", "MR", "SW", "SR"]:
                    mummy_pos.append([int(parts[1]), int(parts[2])])
    except: pass

    return maze, player_pos, mummy_pos

def print_board(maze, p_pos, m_list):
    # Tạo bản sao để vẽ đè nhân vật lên
    display_maze = [row[:] for row in maze]
    
    # Vẽ Mummy
    for m in m_list:
        if 0 <= m[0] < len(display_maze) and 0 <= m[1] < len(display_maze[0]):
            display_maze[m[0]][m[1]] = CHAR_MUMMY
            
    # Vẽ Player
    if 0 <= p_pos[0] < len(display_maze) and 0 <= p_pos[1] < len(display_maze[0]):
        display_maze[p_pos[0]][p_pos[1]] = CHAR_PLAYER

    print("\n" * 2)
    print(f"  --- ASCII MODE: {CHAR_PLAYER}=You, {CHAR_MUMMY}=Enemy, {CHAR_GOAL}=Exit ---")
    print("  Controls: W (Up), S (Down), A (Left), D (Right) + Enter")
    print("  Type 'q' to Quit.\n")
    
    for row in display_maze:
        print("  " + "".join(row))

def run_ascii_level(filename):
    maze, player, mummies = load_level(filename)
    if not maze: return

    while True:
        clear_screen()
        print_board(maze, player, mummies)
        
        # Check Win
        if maze[player[0]][player[1]] == CHAR_GOAL:
            print("\n  *** YOU ESCAPED! ***")
            input("  Press Enter to continue...")
            return

        # Check Lose
        for m in mummies:
            if player == m:
                print("\n  *** CAUGHT BY MUMMY! GAME OVER ***")
                input("  Press Enter to continue...")
                return

        move = input("\n  Your Move: ").lower().strip()
        if move == 'q': return
        
        # Logic di chuyển đơn giản cho Player
        new_p = player[:]
        if move == 'w': new_p[0] -= 2 # Bước nhảy là 2 do map có tường xen kẽ
        elif move == 's': new_p[0] += 2
        elif move == 'a': new_p[1] -= 2
        elif move == 'd': new_p[1] += 2
        
        # Check tường (đơn giản hoá)
        if 0 <= new_p[0] < len(maze) and 0 <= new_p[1] < len(maze[0]):
            # Kiểm tra xem ô giữa có phải tường không
            mid_r, mid_c = (player[0]+new_p[0])//2, (player[1]+new_p[1])//2
            if maze[mid_r][mid_c] != CHAR_WALL and maze[mid_r][mid_c] != CHAR_GATE_CLOSED:
                player = new_p

        # Logic di chuyển đơn giản cho Mummy (Luôn bám theo Player)
        # Đây là AI "ngu" hơn bản đồ họa để demo thôi
        for m in mummies:
            step = 2
            # Di chuyển theo chiều dọc trước
            if m[0] < player[0]: m[0] += step
            elif m[0] > player[0]: m[0] -= step
            # Nếu bằng chiều dọc thì đi chiều ngang
            elif m[1] < player[1]: m[1] += step
            elif m[1] > player[1]: m[1] -= step

def run_ascii_game():
    levels = sorted([f for f in os.listdir(map_path) if f.endswith(".txt")])
    while True:
        clear_screen()
        print("=== MUMMY MAZE DELUXE (ASCII VERSION) ===")
        print("Select Level:")
        for i, lvl in enumerate(levels):
            print(f"{i+1}. {lvl}")
        print("0. Back to Launcher")
        
        choice = input("\nChoose (0-{}): ".format(len(levels)))
        if choice == '0': break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(levels):
                run_ascii_level(levels[idx])
        except ValueError: pass

if __name__ == "__main__":
    run_ascii_game()