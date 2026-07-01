# create_font_vlw.py
Using script python to create font vlw. 
**#Begining**

Cách dùng script



Bước 1 — Cài thư viện (chạy một lần):
pip install Pillow fonttools



Bước 2 — Tải font NotoSans:
Vào https://fonts.google.com/noto/specimen/Noto+Sans → Download family → giải nén → lấy file NotoSans-Regular.ttf



Bước 3 — Đặt file đúng chỗ:
📁 Thư mục bất kỳ/
    ├── tao_font_vlw.py
    └── NotoSans-Regular.ttf   ← đặt cùng chỗ với script


    
Bước 4 — Chạy:
python tao_font_vlw.py
Sẽ tạo ra file NotoSans-Regular20.vlw (~160KB) có đầy đủ 744 ký tự tiếng Việt.



Bước 5 — Copy vào project:

Thay file cũ trong data/NotoSans-Regular20.vlw
Upload LittleFS lại lên ESP32

Muốn tạo thêm size khác (16, 24, 32) thì chỉnh FONT_SIZE và OUTPUT_NAME trong script. File cho các size đó bạn đã có sẵn trong thư mục store vlw file/ nhưng đều thiếu tiếng Việt, nên cần tạo lại hết.
