"""Put a real app screenshot onto the blank screen of a phone or laptop in a generated photo.

usage: python screen_composite.py <photo.png> <screenshot.png> <out.png> [x1,y1,x2,y2,x3,y3,x4,y4]

Best input: the device generated with its screen "filled with flat pure green (#00FF00)" (Task 58's trick).
The green gives an exact screen shape. A plain white screen also works, but bright windows and walls can
fool the detector. It prints the corners it used. If they're wrong, pass the 4 corners in yourself.
The screenshot is perspective-warped onto the screen, then gets a faint glow, a soft glass reflection and
the photo's own grain, so it sits in the photo instead of looking pasted on.
"""
import sys
import cv2
import numpy as np

photo = cv2.imread(sys.argv[1])
shot = cv2.imread(sys.argv[2])
out_path = sys.argv[3]
H, W = photo.shape[:2]


def order(pts):
    pts = np.array(pts, dtype=np.float32).reshape(-1, 2)
    s, d = pts.sum(1), np.diff(pts, axis=1).ravel()
    return np.array([pts[s.argmin()], pts[d.argmin()], pts[s.argmax()], pts[d.argmax()]], dtype=np.float32)


def quad_of(cnt):
    approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)
    return order(approx if len(approx) == 4 else cv2.boxPoints(cv2.minAreaRect(cnt)))


def find_green():
    hsv = cv2.cvtColor(photo, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (40, 120, 90), (85, 255, 255))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    cnts = [c for c in cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            if cv2.contourArea(c) > 0.003 * W * H]
    return quad_of(max(cnts, key=cv2.contourArea)) if cnts else None


def find_white():
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY)
    _, m = cv2.threshold(gray, 228, 255, cv2.THRESH_BINARY)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    best, best_score = None, 0
    for cnt in cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[0]:
        area = cv2.contourArea(cnt)
        if area < 0.003 * W * H:
            continue
        _, (rw, rh), _ = cv2.minAreaRect(cnt)
        fill, ar = area / max(rw * rh, 1), min(rw, rh) / max(rw, rh, 1)
        box = np.zeros_like(gray)
        cv2.drawContours(box, [cnt], -1, 255, -1)
        std = cv2.meanStdDev(gray, mask=box)[1][0][0]
        if fill < 0.85 or std > 14 or not (0.38 < ar < 0.7):
            continue  # windows and walls are uneven or the wrong shape
        score = fill * area * (1 - std / 20)
        if score > best_score:
            best, best_score = quad_of(cnt), score
    return best


if len(sys.argv) > 4:
    quad = order([float(v) for v in sys.argv[4].split(",")])
    how = "given"
else:
    quad, how = find_green(), "green"
    if quad is None:
        quad, how = find_white(), "white"
    if quad is None:
        sys.exit("no blank screen found: pass the 4 corners")
print(f"{how} screen corners:", ",".join(f"{int(x)},{int(y)}" for x, y in quad))

# rounded screen corners sit slightly inside the detected area
ctr = quad.mean(0)
quad = ctr + (quad - ctr) * (1.0 if how == "given" else 0.985)

sh, sw = shot.shape[:2]
src = np.array([[0, 0], [sw, 0], [sw, sh], [0, sh]], dtype=np.float32)
M = cv2.getPerspectiveTransform(src, quad.astype(np.float32))
warped = cv2.warpPerspective(shot, M, (W, H), flags=cv2.INTER_AREA)
mask = cv2.warpPerspective(np.full((sh, sw), 255, np.uint8), M, (W, H))
if how == "green":
    # also cover any green fringe left at the edges
    hsv = cv2.cvtColor(photo, cv2.COLOR_BGR2HSV)
    fringe = cv2.inRange(hsv, (40, 80, 60), (85, 255, 255))
    mask = cv2.max(mask, cv2.dilate(fringe, np.ones((3, 3), np.uint8)) & cv2.dilate(mask, np.ones((15, 15), np.uint8)))
mask = cv2.GaussianBlur(mask, (3, 3), 0).astype(np.float32)[..., None] / 255.0

# match the photo: a slight blur, a touch less contrast, its grain
warped = cv2.GaussianBlur(warped, (0, 0), 0.6).astype(np.float32)
warped = np.clip(warped * 0.96 + 7 + np.random.normal(0, 4.0, warped.shape), 0, 255)

# soft diagonal glass reflection across the screen
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
x0, y0 = quad[0]
diag = ((xx - x0) + (yy - y0)) / (np.linalg.norm(quad[2] - quad[0]) + 1)
glare = np.clip(0.06 * np.exp(-((diag - 0.35) / 0.18) ** 2), 0, 0.06)[..., None]
warped = warped + (255 - warped) * glare

out = photo.astype(np.float32) * (1 - mask) + warped * mask
glow = cv2.GaussianBlur((mask * 255).astype(np.uint8), (0, 0), 18).astype(np.float32)[..., None] / 255.0
out = out + (1 - mask) * glow * 10
cv2.imwrite(out_path, np.clip(out, 0, 255).astype(np.uint8))
print("composited", out_path)
