"""
Tạo file .vlw (font TFT_eSPI) có hỗ trợ tiếng Việt
=====================================================
Yêu cầu:
    pip install Pillow fonttools

Cách dùng:
    1. Đặt file .ttf font bạn muốn dùng (ví dụ: NotoSans-Regular.ttf) cùng thư mục với script này
    2. Chỉnh FONT_PATH, FONT_SIZE, OUTPUT_NAME bên dưới nếu cần
    3. Chạy: python tao_font_vlw.py
    4. Copy file .vlw vào thư mục data/ của project Arduino
    5. Upload LittleFS lên ESP32
"""

from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
import struct
import os

# ===================== CẤU HÌNH =====================
FONT_PATH   = "NotoSans-Regular.ttf"   # Đường dẫn tới file .ttf
FONT_SIZE   = 20                        # Kích thước font (pixel)
OUTPUT_NAME = "NotoSans-Regular20.vlw" # Tên file output
# =====================================================


def get_vietnamese_codepoints(tt_font):
    """Lấy tất cả codepoints tiếng Việt + ASCII có trong font."""
    cmap = tt_font.getBestCmap()
    needed = set()

    # ASCII cơ bản (space đến ~)
    for i in range(32, 127):
        needed.add(i)

    # Latin Extended (chứa â, ê, ô, ơ, ư, ă, đ ...)
    for i in range(0x00C0, 0x0250):
        needed.add(i)

    # Latin Extended Additional (chứa hầu hết tổ hợp dấu tiếng Việt)
    for i in range(0x1E00, 0x1F00):
        needed.add(i)

    # Chỉ giữ codepoint có trong font
    available = sorted(p for p in needed if p in cmap)
    return available


def render_glyph(ch, pil_font, canvas=100, ox=30, oy=50):
    """
    Render một ký tự vào canvas lớn, tự detect vùng có pixel, trả về bitmap thực tế.
    Tránh dùng textbbox vì không chính xác với Unicode phức tạp.
    """
    img = Image.new('L', (canvas, canvas), 0)
    draw = ImageDraw.Draw(img)
    draw.text((ox, oy), ch, font=pil_font, fill=255)

    pixels = list(img.getdata())
    nonzero = [(i % canvas, i // canvas) for i, p in enumerate(pixels) if p > 0]

    if not nonzero:
        # Ký tự không có glyph hiển thị (ví dụ: space)
        adv_draw = ImageDraw.Draw(Image.new('L', (200, 80), 0))
        adv_bbox = adv_draw.textbbox((0, 0), ch, font=pil_font)
        advance = max(4, adv_bbox[2])
        return bytes([0, 0, 0, 0]), 2, 2, advance, 1, 0

    min_x = min(c[0] for c in nonzero)
    max_x = max(c[0] for c in nonzero)
    min_y = min(c[1] for c in nonzero)
    max_y = max(c[1] for c in nonzero)

    w = max_x - min_x + 1
    h = max_y - min_y + 1

    cropped = img.crop((min_x, min_y, max_x + 1, max_y + 1))
    bitmap = bytes(cropped.getdata())

    # Advance width (width thực mà cursor tiến khi in ký tự này)
    adv_draw = ImageDraw.Draw(Image.new('L', (200, 80), 0))
    adv_bbox = adv_draw.textbbox((0, 0), ch, font=pil_font)
    advance = max(1, adv_bbox[2])

    # top = số pixel từ đỉnh glyph lên baseline
    top  = oy - min_y
    left = min_x - ox

    return bitmap, w, h, advance, top, left


def create_vlw(font_path, font_size, output_path):
    print(f"Đang load font: {font_path}")
    pil_font = ImageFont.truetype(font_path, font_size)
    tt_font  = TTFont(font_path)

    # Lấy ascent/descent từ font metrics
    ascent_units  = tt_font['OS/2'].sTypoAscender
    descent_units = tt_font['OS/2'].sTypoDescender
    units_per_em  = tt_font['head'].unitsPerEm
    ascent_px  = round(ascent_units  * font_size / units_per_em)
    descent_px = round(abs(descent_units) * font_size / units_per_em)
    print(f"Font metrics: ascent={ascent_px}px, descent={descent_px}px")

    codepoints = get_vietnamese_codepoints(tt_font)
    print(f"Tổng số ký tự sẽ tạo: {len(codepoints)}")

    # Render từng glyph
    glyph_list = []
    for idx, cp in enumerate(codepoints):
        ch = chr(cp)
        bitmap, w, h, advance, top, left = render_glyph(ch, pil_font)
        glyph_list.append((cp, w, h, advance, top, left, bitmap))

        if (idx + 1) % 100 == 0:
            print(f"  Đã xử lý {idx+1}/{len(codepoints)} ký tự...")

    print(f"Render xong {len(glyph_list)} glyphs. Đang ghi file...")

    # === Ghi file VLW ===
    # Header: 6 x uint32 big-endian
    num_glyphs = len(glyph_list)
    header = struct.pack('>IIIIII',
        num_glyphs,
        11,           # version (Processing/TFT_eSPI dùng version 11)
        font_size,
        0,            # reserved
        ascent_px,
        descent_px
    )

    # Glyph records: mỗi record 28 bytes
    # [codepoint(4), height(4), width(4), advance(4), top(4), left(4), reserved(4)]
    glyph_records = b''
    for cp, w, h, advance, top, left, bitmap in glyph_list:
        glyph_records += struct.pack('>IIIiiiI',
            cp, h, w, advance, top, left, 0
        )

    # Bitmap data: nối tất cả
    bitmap_data = b''
    for cp, w, h, advance, top, left, bitmap in glyph_list:
        bitmap_data += bitmap

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(glyph_records)
        f.write(bitmap_data)

    total_size = len(header) + len(glyph_records) + len(bitmap_data)
    print(f"\n✓ Hoàn thành! File: {output_path}")
    print(f"  Kích thước: {total_size:,} bytes ({total_size/1024:.1f} KB)")
    print(f"  Số glyphs : {num_glyphs}")
    print(f"\nBước tiếp theo:")
    print(f"  1. Copy '{output_path}' vào thư mục data/ của project Arduino")
    print(f"  2. Upload LittleFS lên ESP32 (Tools > ESP32 Sketch Data Upload)")


if __name__ == '__main__':
    if not os.path.exists(FONT_PATH):
        print(f"LỖI: Không tìm thấy file font '{FONT_PATH}'")
        print(f"Hãy tải NotoSans-Regular.ttf từ https://fonts.google.com/noto/specimen/Noto+Sans")
        print(f"và đặt cùng thư mục với script này.")
    else:
        create_vlw(FONT_PATH, FONT_SIZE, OUTPUT_NAME)
