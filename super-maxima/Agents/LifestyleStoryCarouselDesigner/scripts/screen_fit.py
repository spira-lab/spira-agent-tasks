"""Fit a real screenshot exactly into a green phone screen.
usage: fit_screen.py photo.png shot.png out.png
- alpha = the green blob itself (keeps rounded corners and the notch)
- corners = intersection of lines fitted to each straight side of the blob
- spill clean only in a thin band around the screen (no global green kill)
"""
import sys, cv2, numpy as np

photo = cv2.imread(sys.argv[1]); shot = cv2.imread(sys.argv[2]); out = sys.argv[3]
H, W = photo.shape[:2]
hsv = cv2.cvtColor(photo, cv2.COLOR_BGR2HSV)
g = cv2.inRange(hsv, (40, 110, 80), (85, 255, 255))
n, lab, st, _ = cv2.connectedComponentsWithStats(g)
# the screen is the brightest big green blob (a green cutting mat can be bigger but is darker)
big = [k for k in range(1, n) if st[k, cv2.CC_STAT_AREA] > 0.005 * H * W] or [1 + np.argmax(st[1:, cv2.CC_STAT_AREA])]
i = max(big, key=lambda k: hsv[..., 2][lab == k].mean())
blob = np.uint8(lab == i) * 255
blob = cv2.morphologyEx(blob, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
cnt = max(cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
filled = np.zeros_like(blob); cv2.drawContours(filled, [cnt], -1, 255, -1)
# notch: black pixels inside the hull but not green stay out of the alpha
hull = np.zeros_like(blob); cv2.drawContours(hull, [cv2.convexHull(cnt)], -1, 255, -1)

pts = cnt.reshape(-1, 2).astype(np.float32)
rect = cv2.minAreaRect(pts); box = cv2.boxPoints(rect)
c = pts.mean(0)
# assign each contour point to the nearest box side, skip points near corners (rounded)
def side_lines():
    lines = []
    for k in range(4):
        a, b = box[k], box[(k + 1) % 4]
        ab = b - a; L = np.linalg.norm(ab); u = ab / L; nrm = np.array([-u[1], u[0]])
        t = (pts - a) @ u; d = np.abs((pts - a) @ nrm)
        sel = (t > 0.18 * L) & (t < 0.82 * L) & (d < 0.06 * L + 6)
        if sel.sum() < 10:  # a wide notch fills the middle of the top edge: use the shoulders beside it
            sel = (t > 0.06 * L) & (t < 0.94 * L) & (d < 0.03 * L + 4)
        vx, vy, x0, y0 = cv2.fitLine(pts[sel], cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        lines.append((np.array([x0, y0]), np.array([vx, vy])))
    return lines
def inter(l1, l2):
    p, r = l1; q, s = l2
    A = np.array([r, -s]).T
    t = np.linalg.solve(A, q - p)[0]
    return p + t * r
ls = side_lines()
corners = np.array([inter(ls[k - 1], ls[k]) for k in range(4)], np.float32)
# order TL, TR, BR, BL
s, d = corners.sum(1), np.diff(corners, axis=1).ravel()
quad = np.array([corners[s.argmin()], corners[d.argmin()], corners[s.argmax()], corners[d.argmax()]], np.float32)
print("corners", quad.round(1).tolist())

sh, sw = shot.shape[:2]
src = np.float32([[0, 0], [sw, 0], [sw, sh], [0, sh]])
M = cv2.getPerspectiveTransform(src, quad)
warped = cv2.warpPerspective(shot, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

# alpha: green blob grown 1px to swallow the fringe, soft edge
loose = cv2.inRange(hsv, (35, 35, 60), (90, 255, 255))
alpha = cv2.max(blob, loose & cv2.dilate(blob, np.ones((7, 7), np.uint8)))
alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
# smooth the stair-stepped mask edge (blocky green from the image model) into a clean curve
alpha = np.uint8(cv2.GaussianBlur(alpha, (0, 0), 2.5) > 127) * 255
# never paint outside the phone: green-lit things next to it (a book page, a cheek) are not screen
poly = np.zeros_like(alpha); cv2.fillConvexPoly(poly, quad.astype(np.int32), 255)
alpha = cv2.bitwise_and(alpha, cv2.dilate(poly, np.ones((5, 5), np.uint8)))
blob = alpha
alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8).astype(np.float32)[..., None] / 255

# match the photo: its sharpness, a screen that is lit by the room, not pure #FFF
warped = cv2.GaussianBlur(warped, (0, 0), 0.7)
bg = photo[(hull > 0) & (blob == 0)] if ((hull > 0) & (blob == 0)).any() else None
warped = warped * 0.90 + 10                     # lift blacks, drop whites to ~240
# fall-off: slightly darker toward the screen edges (glass + viewing angle)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
Minv = np.linalg.inv(M)
den = Minv[2, 0] * xx + Minv[2, 1] * yy + Minv[2, 2]
u = (Minv[0, 0] * xx + Minv[0, 1] * yy + Minv[0, 2]) / den / sw
v = (Minv[1, 0] * xx + Minv[1, 1] * yy + Minv[1, 2]) / den / sh
fall = 1 - 0.07 * ((2 * u - 1) ** 2 + (2 * v - 1) ** 2)
warped *= fall[..., None]
# soft diagonal reflection in screen coordinates
diag = (u + v) / 2
glare = 0.07 * np.exp(-((diag - 0.30) / 0.16) ** 2)
warped += (255 - warped) * glare[..., None]
warped += np.random.normal(0, 3.5, warped.shape)

res = photo.astype(np.float32) * (1 - alpha) + warped * alpha
# green spill: only a thin band just outside the screen
# the green screen also lit what is near it (a page, a cheek, a hand): clear that cast in a wide ring
reach = int(np.linalg.norm(quad[0] - quad[2]))
band = (cv2.dilate(blob, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (reach, reach))) > 0) & (blob == 0)
r_, g_, b_ = res[..., 2], res[..., 1], res[..., 0]
lim = np.maximum(r_, b_) + 4
spill = band & (g_ > lim)
res[..., 1][spill] = lim[spill]
# faint screen light onto the bezel
glow = cv2.GaussianBlur(blob, (0, 0), 10).astype(np.float32)[..., None] / 255
res += (1 - alpha) * glow * 8
cv2.imwrite(out, np.clip(res, 0, 255).astype(np.uint8))
print("ok", out)
