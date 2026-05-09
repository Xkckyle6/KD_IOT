import tkinter as tk
import math
from sprite_loader import SpriteLoader

# --- Config ---
SPRITESHEET_PATH = "games/steroids/assets/ship3.png"
FRAME_W, FRAME_H = 48, 48
SHEET_COLS = 8
SHEET_ROWS = 0
SHEET_ROW=0
ANGLE_STEP = 10
FRAME_TICK_MS = 1000

# --- Initialize sprite loader ---
sprite_loader = SpriteLoader(
    spritesheet_path=SPRITESHEET_PATH,
    frame_w=FRAME_W,
    frame_h=FRAME_H,
    base_x=0,
    base_y=0,
    sheet_cols=SHEET_COLS,
    sheet_rows=SHEET_ROWS,
    sheet_row=SHEET_ROW,
    angle_step=ANGLE_STEP
)

# Optionally precompute all rotations for all frames (uncomment to pre-render)
# sprite_loader.preload_frames()

# --- Sprite / Player ---
class Player:
    def __init__(self, x, y, loader, frame=0, angle=0.0):
        self.x = x
        self.y = y
        self.frame = frame
        self.angle = angle
        self.loader = loader
        self.photo = loader.get_rotated_photo(self.frame, self.angle)
        self.canvas_id = None

# --- Tk setup ---
root = tk.Tk()
canvas = tk.Canvas(root, width=800, height=600, bg="gray20")
canvas.pack()

# Example dynamic list of players (can add/remove freely)
players = [
    Player(200, 200, sprite_loader, frame=0, angle=0),
    # Player(400, 250, sprite_loader, frame=1, angle=0),
    # Player(600, 350, sprite_loader, frame=2, angle=0)
]

# create canvas items
for p in players:
    p.canvas_id = canvas.create_image(p.x, p.y, image=p.photo)

text1 = canvas.create_text(
    780,
    30,
    anchor="ne",
    fill="#ffffff",
    font=("Arial", 12),
    text="plr0: --",
)

def on_key(event):
    global FRAME_W, FRAME_H
    if event.keysym == "Left":
        print("Spin Left")
        FRAME_W-=1
    elif event.keysym == "Right":
        print("Spin Right")
        FRAME_W+=1
    elif event.keysym == "Up":
        print("Spin Up")
        FRAME_H-=1
    elif event.keysym == "Down":
        print("Spin Down")
        FRAME_H+=1




# --- Update loop ---
def update_all():
    for i, p in enumerate(players):
        # Example logic: rotate and advance frame
        # p.angle = (p.angle + 6 + i*2) % 360
        p.frame = (p.frame + 1) % p.loader.num_frames

        photo = p.loader.get_rotated_photo(p.frame, p.angle)
        p.photo = photo  # keep ref
        canvas.itemconfig(p.canvas_id, image=photo)
        canvas.coords(p.canvas_id, p.x, p.y)  # recenter; expand=True can change size

    #
    canvas.itemconfigure(text1, text=f"plr0: {int(players[0].x)}, {int(players[0].y)}, th={round(players[0].angle,2)}, v={round(0,2)}, FRAME_W={FRAME_W}, FRAME_H={FRAME_H}, Frame={players[0].frame}")

    root.after(FRAME_TICK_MS, update_all)

# --- Dynamic add/remove helpers ---
def add_player(x, y):
    p = Player(x, y, sprite_loader)
    p.canvas_id = canvas.create_image(p.x, p.y, image=p.photo)
    players.append(p)

def remove_player(index=-1):
    if not players:
        return
    p = players.pop(index)
    canvas.delete(p.canvas_id)

root.bind("<Key>", on_key)

# Start loop
root.after(1000, update_all)
root.mainloop()
