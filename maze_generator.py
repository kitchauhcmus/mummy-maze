import random
import os
import sys

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path: sys.path.append(current_dir)
    import search
    import characters
except ImportError:
    pass


class MazeGenerator:
    def __init__(self, size, wall_density):
        self.size = size  # Ví dụ: 6
        self.density = wall_density / 100.0

        # Kích thước thực tế = (Size * 2) + 1
        # Với Size=6 -> 13x13. Viền tường nằm ở index 0 và 12.
        self.rows = 2 * size + 1
        self.cols = 2 * size + 1

        # Khởi tạo toàn bộ là tường (%) trước
        self.grid = [['%' for _ in range(self.cols)] for _ in range(self.rows)]
        self.exit_logic_pos = (0, 0)

    def generate(self):
        # 1. Đục lỗ tạo ô (Space) ở các vị trí LẺ (1, 3, 5...)
        # Điều này giữ lại hàng 0 và hàng cuối là tường -> Tạo viền bao quanh
        for r in range(self.size):
            for c in range(self.size):
                self.grid[2 * r + 1][2 * c + 1] = ' '

        # 2. Thuật toán Backtracker để nối các ô (tạo đường đi chính)
        visited = set()
        stack = [(0, 0)]  # Bắt đầu từ ô (0,0)
        visited.add((0, 0))

        while stack:
            current = stack[-1]
            r, c = current
            neighbors = []

            # 4 Hướng: Lên, Xuống, Trái, Phải
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size and (nr, nc) not in visited:
                    neighbors.append((nr, nc, dr, dc))

            if neighbors:
                nr, nc, dr, dc = random.choice(neighbors)

                # Đục bức tường nằm GIỮA 2 ô
                # ô gốc: (2r+1, 2c+1) | ô mới: (2nr+1, 2nc+1)
                wall_r = 2 * r + 1 + dr
                wall_c = 2 * c + 1 + dc
                self.grid[wall_r][wall_c] = ' '

                visited.add((nr, nc))
                stack.append((nr, nc))
            else:
                stack.pop()

        # 3. Xử lý Density (Đục thêm tường ngẫu nhiên)
        # Chỉ xét các bức tường BÊN TRONG (từ index 1 đến rows-2)
        # Tuyệt đối không đụng vào index 0 và index rows-1 (Viền ngoài)
        potential_walls = []
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                if self.grid[r][c] == '%':
                    # Kiểm tra xem tường này có kẹp giữa 2 khoảng trống không
                    is_vertical = (self.grid[r][c - 1] == ' ' and self.grid[r][c + 1] == ' ')
                    is_horizontal = (self.grid[r - 1][c] == ' ' and self.grid[r + 1][c] == ' ')

                    if is_vertical or is_horizontal:
                        potential_walls.append((r, c))

        open_ratio = 1.0 - self.density
        num_to_open = int(len(potential_walls) * open_ratio)
        random.shuffle(potential_walls)

        for i in range(num_to_open):
            wr, wc = potential_walls[i]
            self.grid[wr][wc] = ' '

        # 4. Tạo Cửa Ra (Exit) 'S'
        # Đặt ở Hàng 1, Cột 0 (Bên trái)
        self.grid[1][0] = 'S'
        self.exit_logic_pos = (0, 0)  # Ghi nhận exit ở khu vực ô (0,0)

        return self.grid

    def randomize_positions(self, num_enemies):
        # Lấy danh sách tất cả các ô là ô trống
        all_cells = [(r, c) for r in range(self.size) for c in range(self.size)]

        # 1. Chọn vị trí Explorer (Cách xa cửa ra)
        while True:
            explorer_pos = random.choice(all_cells)
            dist = abs(explorer_pos[0] - self.exit_logic_pos[0]) + abs(explorer_pos[1] - self.exit_logic_pos[1])
            # Yêu cầu khoảng cách tối thiểu
            if dist > self.size // 2: break

        all_cells.remove(explorer_pos)

        # 2. Chọn vị trí quái vật
        enemies = []
        safe_dist = 3
        attempts = 0

        while len(enemies) < num_enemies and attempts < 100:
            attempts += 1
            if not all_cells: break
            e_pos = random.choice(all_cells)

            # Tính khoảng cách
            dist = abs(e_pos[0] - explorer_pos[0]) + abs(e_pos[1] - explorer_pos[1])

            if dist >= safe_dist:
                # --- LOGIC CHỌN QUÁI ---
                if num_enemies == 1:
                    # Nếu chỉ có 1 quái -> BẮT BUỘC có xác ướp (Trắng/Đỏ)
                    types = ["MW", "MR"]
                    weights = [70, 30]  # 70% Trắng, 30% Đỏ
                else:
                    # Nhiều quái -> Có thể có Bọ cạp
                    types = ["MW", "MR", "SW", "SR"]
                    weights = [40, 30, 20, 10]

                e_type = random.choices(types, weights=weights, k=1)[0]
                enemies.append((e_type, e_pos))
                all_cells.remove(e_pos)

        return explorer_pos, enemies

    def save_to_files(self, maze_path, agent_path, explorer_pos, enemies):
        os.makedirs(os.path.dirname(maze_path), exist_ok=True)
        os.makedirs(os.path.dirname(agent_path), exist_ok=True)

        # Lưu file Maze
        with open(maze_path, 'w') as f:
            for row in self.grid:
                f.write("".join(row) + "\n")

        # Lưu file Agents
        #Convert tọa độ Logic -> Thực tế: (2*x + 1)
        real_ex_r = 2 * explorer_pos[0] + 1
        real_ex_c = 2 * explorer_pos[1] + 1

        with open(agent_path, 'w') as f:
            f.write(f"E {real_ex_r} {real_ex_c}\n")
            for e_type, pos in enemies:
                real_r = 2 * pos[0] + 1
                real_c = 2 * pos[1] + 1
                f.write(f"{e_type} {real_r} {real_c}\n")

    def is_solvable(self, explorer_pos, enemies):
        """Kiểm tra xem map có giải được không"""
        try:
            # Setup tọa độ thực tế để BFS chạy
            real_ex_r = 2 * explorer_pos[0] + 1
            real_ex_c = 2 * explorer_pos[1] + 1
            explorer = characters.Explorer(real_ex_r, real_ex_c)

            mw, mr, sw, sr = [], [], [], []
            for e_type, pos in enemies:
                real_r = 2 * pos[0] + 1
                real_c = 2 * pos[1] + 1

                # Tạo object quái vật (Difficulty 1 = Greedy Move chuẩn Mummy)
                enemy_obj = None
                if e_type == "MW":
                    enemy_obj = characters.mummy_white(real_r, real_c)
                elif e_type == "MR":
                    enemy_obj = characters.mummy_red(real_r, real_c)
                elif e_type == "SW":
                    enemy_obj = characters.scorpion_white(real_r, real_c)
                elif e_type == "SR":
                    enemy_obj = characters.scorpion_red(real_r, real_c)

                if enemy_obj:
                    enemy_obj.set_difficulty(1)
                    if e_type == "MW":
                        mw.append(enemy_obj)
                    elif e_type == "MR":
                        mr.append(enemy_obj)
                    elif e_type == "SW":
                        sw.append(enemy_obj)
                    elif e_type == "SR":
                        sr.append(enemy_obj)

            gate = {"isClosed": False}
            path = search.BFS(explorer, mw, mr, sw, sr, gate, [], (), self.grid)
            return path is not None and len(path) > 0

        except Exception as e:
            return False


def create_valid_level(size, density):
    """Hàm tạo level đảm bảo LUÔN GIẢI ĐƯỢC"""
    project_path = os.path.dirname(os.path.abspath(__file__))
    maze_file = os.path.join(project_path, "map", "maze", "custom_gen.txt")
    agent_file = os.path.join(project_path, "map", "agents", "custom_gen.txt")

    num_enemies = 1
    if size >= 8: num_enemies = 2
    if size >= 10: num_enemies = 3

    attempts = 0
    while True:
        # 1. Tạo cấu trúc tường
        gen = MazeGenerator(size, density)
        gen.generate()

        # 2. Thử đặt nhân vật 10 lần trên map này
        for _ in range(10):
            ex_pos, enemies = gen.randomize_positions(num_enemies)

            # 3. Check giải được không
            if gen.is_solvable(ex_pos, enemies):
                print(f"MAZE GEN: Found solvable map after {attempts} tries.")
                gen.save_to_files(maze_file, agent_file, ex_pos, enemies)
                return "custom_gen.txt"

            attempts += 1
            if attempts % 50 == 0:
                print(f"Generating... ({attempts} tries)")


