# add an iPhone status bar + home indicator to a 1179x2556 page capture
import sys
from PIL import Image, ImageDraw, ImageFont
im = Image.open(sys.argv[1]).convert("RGB"); W, H = im.size
bar = 150
canvas = Image.new("RGB", (W, H), (255, 255, 255))
canvas.paste(im.crop((0, 0, W, H - bar)), (0, bar))
d = ImageDraw.Draw(canvas)
# the clock face: a semibold sans (Noto Sans SemiBold, then DejaVu Sans Bold, then Pillow's default).
def clock_font(size):
    for path, index, variation in (("/usr/share/fonts/truetype/noto/NotoSans-SemiBold.ttf", 0, None),
                                   ("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 0, None),
                                   ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 0, None)):
        try:
            f = ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
        if variation:
            try: f.set_variation_by_name(variation)
            except (OSError, ValueError, AttributeError): pass
        return f
    return ImageFont.load_default(size)
f = clock_font(50)
d.text((150, 75), sys.argv[3], font=f, fill=(0, 0, 0), anchor="mm")
x = 870  # signal bars
for i, h in enumerate([14, 20, 27, 34]):
    d.rounded_rectangle((x + i * 17, 92 - h, x + i * 17 + 11, 92), 3, fill=(0, 0, 0))
cx, cy = 980, 92  # wifi
for r, w in [(34, 8), (22, 8)]:
    d.arc((cx - r, cy - r - 4, cx + r, cy + r - 4), 225, 315, fill=(0, 0, 0), width=w)
d.ellipse((cx - 6, cy - 14, cx + 6, cy - 2), fill=(0, 0, 0))
d.rounded_rectangle((1030, 58, 1110, 94), 10, outline=(0, 0, 0), width=4)  # battery
d.rounded_rectangle((1037, 65, 1086, 87), 5, fill=(0, 0, 0))
d.rounded_rectangle((1114, 69, 1120, 83), 2, fill=(0, 0, 0))
d.rounded_rectangle((W // 2 - 210, H - 40, W // 2 + 210, H - 26), 7, fill=(20, 20, 20))
canvas.save(sys.argv[2])
