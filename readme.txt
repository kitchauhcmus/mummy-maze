================================================================================
  ĐỒ ÁN MÔN HỌC: CƠ SỞ LẬP TRÌNH CHO TRÍ TUỆ NHÂN TẠO
================================================================================
Link video giới thiệu: https://www.youtube.com/watch?v=K_knNxC-yiQ
1. THÔNG TIN NHÓM THỰC HIỆN (CODE PHANTOM)
--------------------------------------------------------------------------------
- Trường: Đại học Khoa học Tự nhiên - ĐHQG TP.HCM
- Lớp: 25TNT1
- Giảng viên hướng dẫn: Thầy Trần Hoàng Quân
- Thành viên nhóm:
  1. Nguyễn Châu Tuấn Kiệt (25122026) 
  2. Võ Duy Phát           (25122013)
  3. Phan Phước Quang Minh (25122029)
  4. Nguyễn Minh Quang     (25122038)

2. YÊU CẦU HỆ THỐNG (PREREQUISITES)
--------------------------------------------------------------------------------
Để chạy được trò chơi, máy tính cần cài đặt:
- Python: Phiên bản 3.8 trở lên (Khuyến nghị 3.14).
- Thư viện Pygame: Dùng để xử lý đồ họa và âm thanh.

3. HƯỚNG DẪN CÀI ĐẶT (INSTALLATION)
--------------------------------------------------------------------------------
Bước 1: Giải nén và mở thư mục source code

Bước 2: Mở Terminal (Command Prompt) và trỏ đến thư mục vừa giải nén.

Bước 3: Cài đặt các thư viện phụ thuộc bằng lệnh sau:
    pip install pygame

(Lưu ý: Các thư viện os, sys, random, json, math, re là thư viện chuẩn của Python, không cần cài đặt thêm).

Bước 4: Đảm bảo cấu trúc thư mục đầy đủ như sau để tránh lỗi thiếu file:
    /Project_Folder
      ├── main.py              (File chạy chính)
      ├── characters.py        (Logic nhân vật & AI)
      ├── graphics.py          (Xử lý hiển thị)
      ├── maze_generator.py    (Thuật toán sinh mê cung)
      ├── search.py            (Thuật toán tìm đường & kiểm chứng)
      ├── database.py          (Quản lý người dùng & Save game)
      ├── ascii_game.py        (Chế độ Console)
      ├── users_data.json      (File dữ liệu người dùng - tự sinh nếu chưa có)
      ├── savegame.json        (File lưu game - tự sinh khi save)
      ├── /map                 (Chứa dữ liệu bản đồ .txt)
      ├── /image               (Chứa hình ảnh sprites)
      ├── /sound               (Chứa hiệu ứng âm thanh)
      └── /music               (Chứa nhạc nền)

4. HƯỚNG DẪN CHẠY GAME (HOW TO RUN)
--------------------------------------------------------------------------------
Game hỗ trợ 2 chế độ hiển thị: Đồ họa (Graphic) và Ký tự (ASCII Console).

Cách chạy:
1. Tại Terminal, gõ lệnh:
    python main.py

2. Màn hình Launcher sẽ hiện ra yêu cầu chọn chế độ:
    - Nhập '1' và nhấn Enter: Để chơi chế độ Đồ họa (Graphic Mode) - Khuyên dùng.
    - Nhập '2' và nhấn Enter: Để chơi chế độ Console (ASCII Mode).
5. HƯỚNG DẪN CHƠI (CONTROLS & GAMEPLAY)
--------------------------------------------------------------------------------
A. MỤC TIÊU:
- Điều khiển Nhà thám hiểm đi đến ô Cầu thang ('S') để qua màn.
- Tránh va chạm với Xác ướp (Mummy), Bọ cạp (Scorpion) và Bẫy ('T').

B. ĐIỀU KHIỂN (Trong chế độ Đồ họa):
- Di chuyển:
    + Sử dụng phím Mũi tên (Lên, Xuống, Trái, Phải).
    + Hoặc Click chuột trái vào ô bên cạnh để di chuyển.
    + Có thể nhấn phím Space để nhân vật đứng im tại chỗ 1 lượt (trong lượt này thì xác ướp vẫn di chuyển bình thường)
- Chức năng hỗ trợ:
    + Nút UNDO: Quay lại nước đi trước (Không giới hạn số lần).
    + Nút RESET: Chơi lại màn hiện tại từ đầu.
    + Phím ESC: Mở Menu tạm dừng để Lưu game (Save) hoặc Thoát.

C. CƠ CHẾ ĐẶC BIỆT:
- Chìa khóa & Cổng: Đi vào ô Chìa khóa ('K') để Đóng/Mở các Cổng ('G') màu đỏ.
- AI Quái vật:
    + Mummy Trắng: Ưu tiên di chuyển Ngang.
    + Mummy Đỏ: Ưu tiên di chuyển Dọc.
    + (Độ khó Hard): Quái vật thông minh hơn, biết đi đường vòng và chặn đầu.

6. CÁC TÍNH NĂNG NỔI BẬT
--------------------------------------------------------------------------------
1. Sinh Mê cung ngẫu nhiên (Practice Mode):
   - Vào menu "Practice" -> "Generate Maze".
   - Chọn Size (6x6, 8x8...) và Mật độ tường (Density) để tạo map mới không trùng lặp.

2. Hệ thống Database & Save Game:
   - Có thể Đăng ký/Đăng nhập tài khoản.
   - Bảng xếp hạng (Leaderboard) cập nhật theo thời gian thực.
   - Save/Load game giữ nguyên vị trí nhân vật và trạng thái cổng.

