import json
import os

class UserManager:
    def __init__(self):
        # Lấy đường dẫn tuyệt đối đến file users_data.json nằm cùng thư mục với script này
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.user_data_path = os.path.join(base_path, "users_data.json")
        
        # Nếu file chưa tồn tại thì tạo mới
        if not os.path.exists(self.user_data_path):
            try:
                with open(self.user_data_path, 'w') as f:
                    json.dump({}, f)
            except IOError as e:
                print(f"Error creating database file: {e}")

    def load_data(self):
        if not os.path.exists(self.user_data_path):
            return {}
        try:
            with open(self.user_data_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def save_data(self, data):
        try:
            with open(self.user_data_path, 'w') as f:
                json.dump(data, f, indent=4)
        except IOError as e:
            print(f"Error saving database: {e}")

    def register(self, username, password):
        data = self.load_data()
        if username in data:
            return False, "Username already exists!"
        
        # Tạo user mới với dữ liệu mặc định
        data[username] = {
            "password": password,
            "max_level": 1,
            "difficulty": 1,
            "score": 0  # Điểm số mặc định
        }
        self.save_data(data)
        return True, "Registration successful!"

    def login(self, username, password):
        data = self.load_data()
        if username not in data:
            return False, "Username not found!"
        if data[username]["password"] != password:
            return False, "Incorrect password!"
        return True, data[username]

    def get_level(self, username):
        data = self.load_data()
        return data.get(username, {}).get("max_level", 1)

    def get_difficulty(self, username):
        data = self.load_data()
        return data.get(username, {}).get("difficulty", 1)
    
    def get_score(self, username):
        data = self.load_data()
        return data.get(username, {}).get("score", 0)

    def update_difficulty(self, username, difficulty):
        data = self.load_data()
        if username in data:
            data[username]["difficulty"] = difficulty
            self.save_data(data)

    def update_progress(self, username, level):
        data = self.load_data()
        if username in data:
            # Chỉ cập nhật nếu level mới cao hơn level cũ
            if level > data[username].get("max_level", 1):
                data[username]["max_level"] = level
                self.save_data(data)

    def add_score(self, username, points):
        """Cộng điểm tích lũy cho người chơi"""
        data = self.load_data()
        if username in data:
            current_score = data[username].get("score", 0)
            data[username]["score"] = current_score + points
            self.save_data(data)
            
    def reset_level(self, username):
        """Reset level về 1 (dùng khi chọn độ khó mới hoặc chơi lại)"""
        data = self.load_data()
        if username in data:
            data[username]["max_level"] = 1
            # Lưu ý: Không reset điểm (score) để giữ tính cạnh tranh
            self.save_data(data)

    def get_leaderboard(self):
        """
        Trả về danh sách Top 7 người chơi có điểm cao nhất.
        Format trả về: [("Name1", Score1), ("Name2", Score2), ...]
        """
        if not os.path.exists(self.user_data_path):
            return []
        
        try:
            with open(self.user_data_path, "r") as f:
                data = json.load(f)
            
            # Chuyển đổi dict thành list các tuple (username, score)
            leaderboard = []
            for username, info in data.items():
                score = info.get("score", 0)
                # Chỉ thêm vào bảng xếp hạng nếu có điểm > 0
                if score >= 0: 
                    leaderboard.append((username, score))
            
            # Sắp xếp giảm dần theo điểm (score)
            leaderboard.sort(key=lambda x: x[1], reverse=True)
            
            # Chỉ lấy Top 7 để hiển thị cho vừa màn hình
            return leaderboard[:7]
        except Exception as e:
            print(f"Error loading leaderboard: {e}")
            return []