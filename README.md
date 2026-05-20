# UsagiMon — Game Nhập Vai Chiến Thuật 2D (OpenGL & Pygame)

**UsagiMon** là một tựa game nhập vai chiến thuật (RPG) 2D theo lượt lấy cảm hứng từ dòng game Pokémon cổ điển. Dự án kết hợp sức mạnh hệ thống của thư viện **Pygame** và khả năng dựng hình đồ họa tăng tốc phần cứng 2D mạnh mẽ từ **PyOpenGL**, mang đến trải nghiệm đồ họa mượt mà, sống động cùng lối chơi chiến thuật có chiều sâu.


##  Tính Năng Nổi Bật

* **Thế giới mở Overworld sinh động**: Người chơi điều khiển chú Thỏ trắng (Usagi) khám phá thế giới xung quanh với hệ thống bản đồ grid-based được thiết kế tỉ mỉ. Các bụi cỏ, đường mòn, cây cối và đấu trường trùm cuối đều được dựng hình độc đáo.
* **Hệ thống chiến đấu Turn-Based đậm chất cổ điển**:
  * Các loại đòn tấn công phong phú: Cận chiến (Melee), Viễn chinh (Ranged), Hồi máu (Heal).
  * Hiệu ứng chí mạng (Crit Chance), đánh hụt (Miss Chance) ngẫu nhiên tăng tính kịch tính.
  * Tính năng **Catch (Bắt quái thú)** sử dụng lưới bắt quái để thu phục các loại quái hoang dã (Slime, Bee) về làm đồng minh trong đội hình.
* **Quản lý Đội hình & Túi đồ nâng cao**:
  * **Túi đồ (Item Inventory)**: Sử dụng vật phẩm Carrot để phục hồi máu hay Revive để hồi sinh đồng minh đã ngã xuống.
  * **Đội hình (Party)**: Cho phép chứa tối đa 6 quái thú. Người chơi có thể tự do thay đổi vị trí chiến đấu, thả quái thú về tự nhiên (Release) hoặc chọn quái thú ra trận linh hoạt.
* **Đồ họa 2D tăng tốc phần cứng (Hardware-accelerated)**: Tận dụng hoàn toàn OpenGL để vẽ trực tiếp hình học nguyên thủy (Quads, Lines, Circles) và áp bản đồ vân bề mặt (Texture Mapping) cho các nhân vật có hoạt ảnh (Spritesheets) chạy ở khung hình 60 FPS cực kỳ mượt mà.
* **Hệ thống âm thanh sống động**: 
  * Âm thanh bước chân (Walk SFX) khi di chuyển trên Overworld.
  * Nhạc nền nền động tự động chuyển đổi giữa nhạc thám hiểm (Overworld) và nhạc chiến đấu (Battle Music).
  * Hiệu ứng âm thanh khi sử dụng vật phẩm phục hồi, hồi sinh, khi thua cuộc (Game Over) hoặc chiến thắng vinh quang.

---

##  Cấu Trúc Thư Mục Dự Án

```text
GamebyOpenGL/
├── assets/                  # Tài nguyên đồ họa và âm thanh
│   ├── img/                 # Hình ảnh nền, giao diện
│   ├── newassets/           # Các asset bổ sung
│   ├── player/              # Sprite của người chơi (Thỏ)
│   ├── sounds/              # Nhạc nền (.mp3) và hiệu ứng âm thanh (.wav/.mp3)
│   └── sprite_sheets/       # Spritesheet chuyển động của Thỏ, Slime, Bee, Cáo (Fox)
├── game/                    # Logic nghiệp vụ trò chơi
│   ├── __init__.py
│   ├── battle.py            # Hệ thống chiến đấu theo lượt (Turn-based Combat)
│   ├── combat_entities.py   # Định nghĩa thông số, kỹ năng của sinh vật (Rabbit, Fox, Slime, Bee)
│   ├── overworld.py         # Bản đồ, di chuyển và render môi trường OpenGL
│   └── ui.py                # Vẽ menu UI, bảng đội hình, hòm đồ bằng OpenGL
├── renderer/                # Xử lý kết xuất đồ họa cấp thấp
│   ├── __pycache__/
│   └── sprite_renderer.py   # Trình quản lý nạp và vẽ Sprite/Spritesheet từ GPU
├── utils/                   # Các công cụ bổ trợ hệ thống
│   ├── __pycache__/
│   ├── animation.py         # Quản lý vòng lặp frame hoạt ảnh nhân vật
│   ├── constants.py         # Các hằng số cấu hình (kích thước màn hình, tỷ lệ tấn công, mã màu)
│   ├── text_renderer.py     # Trình kết xuất font chữ TTF thành texture OpenGL
│   └── texture_loader.py    # Tiện ích nạp hình ảnh từ đĩa cứng lên VRAM
├── venv/                    # Môi trường ảo Python (Virtual Environment)
├── .gitignore
├── requirements.txt         # Liệt kê thư viện phụ thuộc (Pygame, PyOpenGL, Pillow, Numpy)
├── setup.bat                # Kịch bản tự động thiết lập môi trường (Windows)
├── run.bat                  # Kịch bản khởi chạy game nhanh (Windows)
├── main.py                  # Điểm khởi đầu của ứng dụng (Main Entry Point) và Vòng lặp game (Game Loop)
```

---

##  Công Nghệ Sử Dụng

* **Python**: Ngôn ngữ lập trình cốt lõi chính của dự án.
* **Pygame**: Quản lý tạo cửa sổ, xử lý sự kiện (Event Handling), đầu vào bàn phím/chuột và thiết lập bộ trộn âm thanh (Pygame Mixer).
* **PyOpenGL**: Sử dụng đặc tả OpenGL để kết xuất đồ họa phần cứng 2D trực tiếp từ GPU.
* **Pillow (PIL)**: Nạp và xử lý định dạng hình ảnh PNG trước khi chuyển đổi sang dạng dữ liệu nhị phân (Buffer) đẩy lên bộ nhớ đồ họa GPU.
* **NumPy**: Hỗ trợ tính toán hiệu năng cao cho việc thao tác cấu trúc lưới tọa độ bản đồ.

---

##  Hướng Dẫn Cài Đặt & Chạy Game

> [!IMPORTANT]
> Game chạy ổn định nhất trên **Python 3.9 đến 3.12**.
> Do cấu trúc hệ thống âm thanh và đồ họa nâng cao, thư viện **Pygame** có thể gặp một số lỗi không tương thích trên phiên bản Python 3.13+. Vui lòng đảm bảo máy tính của bạn đã được cài đặt Python nằm trong khoảng phiên bản được khuyến nghị.

### 1. Trên Windows (Sử dụng script có sẵn)

Dự án đã tích hợp sẵn 2 tập tin lệnh tự động hóa giúp bạn cài đặt môi trường và khởi động game cực kỳ dễ dàng:

1. **Bước 1**: Nhấp đúp chuột vào tập tin `setup.bat`. Tập tin này sẽ tự động:
   * Tìm kiếm phiên bản Python phù hợp (3.9 - 3.12) có trên máy của bạn.
   * Khởi tạo một môi trường ảo cục bộ trong thư mục `venv`.
   * Cập nhật bộ quản lý gói `pip`.
   * Tự động cài đặt toàn bộ các thư viện phụ thuộc trong `requirements.txt`.
2. **Bước 2**: Nhấp đúp chuột vào tập tin `run.bat` để kích hoạt môi trường ảo và bắt đầu chiến game ngay lập tức!

---

### 2. Cài đặt thủ công (Mọi hệ điều hành)

Nếu bạn sử dụng MacOS, Linux hoặc muốn thiết lập bằng dòng lệnh, hãy thực hiện theo các bước sau:

**Bước 1**: Mở terminal hoặc cửa sổ dòng lệnh CMD ngay tại thư mục gốc dự án và tạo môi trường ảo Python:
```bash
python -m venv venv
```

**Bước 2**: Kích hoạt môi trường ảo:
* **Trên Windows (CMD/PowerShell)**:
  ```powershell
  venv\Scripts\activate
  ```
* **Trên MacOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

**Bước 3**: Tiến hành cài đặt các gói phụ thuộc cần thiết:
```bash
pip install -r requirements.txt
```

**Bước 4**: Khởi chạy trò chơi:
```bash
python main.py
```

---

##  Hướng Dẫn Điều Khiển

### 1. Tại Overworld (Bản đồ thế giới)

| Phím bấm | Hành động tương ứng |
| :--- | :--- |
| **W, A, S, D** hoặc **Mũi tên** | Di chuyển chú Thỏ đi thám hiểm thế giới |
| **ESC** | Bật / Tắt menu điều khiển nhanh hệ thống |
| **ENTER**, **Z** hoặc **SPACE** | Xác nhận chọn các mục menu (Action, Party, Exit) |
| **X** hoặc **BACKSPACE** | Hủy bỏ / Quay lại giao diện màn hình trước đó |

---

### 2. Trong Trận Chiến (Battle Screen)

Khi chạm trán quái vật hoang dã hoặc trùm cuối, giao diện chiến đấu xuất hiện:

| Phím bấm | Hành động tương ứng |
| :--- | :--- |
| **W, S (Lên/Xuống)** | Di chuyển con trỏ lựa chọn giữa các hành động chiến đấu |
| **A, D (Trái/Phải)** | Di chuyển nhanh giữa các cột lệnh tùy chọn |
| **ENTER**, **Z** hoặc **SPACE** | Đồng ý ra chiêu thức tấn công hoặc sử dụng vật phẩm |
| **X** | Quay lại menu cấp trên (Khi đang chọn vật phẩm/đội hình lẻ) |

---

## ⚔ Cơ Chế Gameplay Chính

1. **Khám Phá & Chạm Trán**:
   * Di chuyển chú Thỏ vào các khu vực bụi cỏ tròn xanh lá cây (Bụi cỏ 1 hoặc Bụi cỏ 2) để gặp quái thú hoang dã ngẫu nhiên.
   * Cấp độ của quái hoang dã sẽ tự động tỷ lệ tương thích theo cấp độ hiện tại của chú Thỏ để đảm bảo tính thử thách hợp lý.
   * Để đối đầu với Trùm cuối (Boss Fox), người chơi di chuyển lên đấu trường rực lửa phía trên cùng bản đồ.
2. **Chiến Đấu & Tiến Hóa**:
   * Khi quái thú đối phương bị đánh bại, quái thú trong đội hình của bạn trực tiếp tham gia chiến đấu sẽ nhận được điểm kinh nghiệm (EXP).
   * Khi tích lũy đủ điểm kinh nghiệm, quái thú sẽ được tăng cấp (Level Up), giúp tăng vọt các chỉ số sức mạnh cơ bản như HP và ATK.
3. **Bắt & Quản Lý Quái Thú**:
   * Trong lượt đi của bạn, chọn mục túi đồ và sử dụng **Net (Lưới)** để thực hiện việc bắt quái thú đối diện.
   * Nếu thu phục thành công, quái thú hoang dã đó sẽ trở thành một người bạn trung thành trong đội hình Party tối đa 6 quái. Nếu đội hình chính đã đầy, bạn có thể giải phóng bớt quái thú khác bằng tính năng **Release** trong túi đồ.

---

##  Kiến Trúc Kỹ Thuật Đồ Họa

### 1. Dựng Hình Với OpenGL
Dự án không dùng bộ vẽ hình mặc định của Pygame, thay vào đó chuyển hoàn toàn trạng thái dựng sang cổng đồ họa **OpenGL 2D**:
* **Không gian trực giao 2D (Orthographic Projection)**: Thiết lập thông qua hàm `gluOrtho2D(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)` khớp chính xác pixel-by-pixel với độ phân giải màn hình 1280x720.
* **Vẽ hình học trực tiếp**: Xây dựng tối ưu hóa các đối tượng địa hình (cỏ dại, cây cối, bờ tường rào) thông qua các lệnh hình học nguyên thủy như `glBegin(GL_QUADS)` (vẽ ô vuông), `glBegin(GL_LINES)` (vẽ các chi tiết đường thẳng cỏ đứt đoạn) và thuật toán chia nhỏ góc `GL_TRIANGLE_FAN` để vẽ các bụi cỏ hình tròn mềm mại mà không cần lưu nhiều file hình nặng.

### 2. Bộ Dựng Sprite & SpriteSheet (SpriteRenderer)
Lớp `SpriteRenderer` đảm nhận vai trò cầu nối hiệu quả từ hình ảnh lên GPU:
* Chuyển đổi dữ liệu thô (Raw Pixel Buffer) từ thư viện **Pillow** sang một OpenGL Texture ID thông số định danh.
* Tự động tính toán các tọa độ bản đồ vân bề mặt (Texture Coordinates `u, v`) dựa vào hàng và cột chỉ định để tách chi tiết các khung hình (Frame) hoạt ảnh từ một bảng Spritesheet duy nhất, tránh việc nạp nhiều ảnh rời rạc gây phân mảnh bộ nhớ VRAM.
* Hỗ trợ lật ngược hướng ngang bằng cách đảo tọa độ trục kết cấu (`flip_x`), phục vụ việc vẽ nhân vật quay trái/phải mượt mà.

### 3. Dựng Text Bằng Bitmap Texture (TextRenderer)
Vì OpenGL thuần không hỗ trợ trực tiếp hiển thị font chữ hệ thống:
* Dự án tận dụng bộ vẽ chữ của Pygame (`pg.font.Font.render`) để kết xuất dòng chữ ra một bề mặt đệm tạm thời (Surface).
* Bề mặt đệm đó ngay lập tức được giải nén chuyển hóa thành Texture 2D động tải lên GPU của card đồ họa.
* Trình xử lý dựng một tấm Quad phẳng phủ bề mặt vân chứa ký tự đó lên màn hình tọa độ mong muốn giúp chữ hiển thị sắc nét, không nhòe và cực kỳ hiệu năng.

### 4. Xử Lý Va Chạm (Collision Detection)
* Sử dụng phương pháp kiểm tra hộp bao va chạm AABB (Axis-Aligned Bounding Box) tại bốn góc điểm rìa nhân vật.
* Trước khi người chơi thực sự thay đổi vị trí `(x, y)`, hàm `_blocked_at` sẽ tính toán thử vị trí mới trên lưới ma trận tọa độ `TILEMAP`. Nếu ô đích chứa thuộc tính vật cản cứng (cây cối, tường rào, nhà cửa), chuyển động sẽ bị chặn đứng tại rìa ô đó một cách tự nhiên.

---

**Chúc bạn chơi game vui vẻ !**
