import json
import queue
import threading
import time
from tkinter import *
import tkinter as tk
from tkinter import messagebox

from config import *
import math

from PIL import Image, ImageTk
import os

FRAME_W, FRAME_H = 64, 64      # single frame size
NUM_FRAMES = 8
SHEET_X_OFFSET = 0             # if frames start with margin
SHEET_Y_OFFSET = 0

SPRITESHEET_PATH = os.path.join("games", "steroids", "media", "ships.png")


# create a class to store player information
class Player:
    def __init__(self, player_id, username="Player", sprite=None, imagetk=None, sprite_id=0, frame=0):
        self.player_id = player_id
        self.username = username
        self.x = 100
        self.y = 100
        self.v = 0
        self.accel = 0
        self.th = 1 # rotation
        self.thd = 0 # rotation speed
        self.thdd = 0 # rotation acceleration
        self.radius = 10
        self.color = "#33cc33" if player_id == "local" else "#ff4444"
        self.level=1
        self.score=0
        self.alive = True
        self.sprite = sprite

        self.sprite_id = sprite_id   # unused here but left for multi-sprite support
        self.frame = frame
        self.image_ref = None        # holds current PhotoImage
        self.image_tk = image_tk

    #     
    def update(self, dt):
        """
        Main gameplay update.
        dt = delta time in seconds.
        """

        # # Rotation
        # if self.input_state["left"]:
        #     self.rotation -= self.turn_speed * dt

        # if self.input_state["right"]:
        #     self.rotation += self.turn_speed * dt

        # # Thrust
        # if self.input_state["up"]:
        #     forward = Vector2(1, 0).rotate(self.rotation)

        #     self.velocity += (
        #         forward * self.acceleration * dt
        #     )

        # # Clamp speed
        # if self.velocity.length() > self.max_speed:
        #     self.velocity.scale_to_length(self.max_speed)

        # Movement
        # self.x += self.v * math.cos(self.th) * dt
        # self.y += self.v * math.sin(self.th) * dt
        # self.th += self.thd * dt

        # print(f"Before update: x={self.x}, y={self.y}, th={self.th}, v={self.v}")
        self.x=self.x+self.v*math.cos(self.th)*dt
        self.y=self.y+self.v*math.sin(self.th)*dt
        self.th=self.th+self.thd*dt

        # Friction
        # self.v *= 0.95
        # self.thd *= 0.95

    def can_fire(self):
        now = time.time()

        return (
            now - self.last_fire_time
            >= self.fire_cooldown
        )

    def fire(self):
        if self.can_fire():
            self.last_fire_time = time.time()

            return True

        return False

    def get_network_state(self):
        """
        Minimal replicated state.
        """

        return {
            "id": self.player_id,
            "x": self.position.x,
            "y": self.position.y,
            "vx": self.velocity.x,
            "vy": self.velocity.y,
            "rot": self.rotation,
            "alive": self.alive
        }

    def apply_network_state(self, data):
        """
        Apply state from server.
        """

        self.position.x = data["x"]
        self.position.y = data["y"]

        # self.velocity.x = data["vx"]
        # self.velocity.y = data["vy"]

        self.rotation = data["th"]

        self.alive = data["alive"]
plrs = {}
plrs[0] = Player(0, "Player 1")

## Main game class --------------------------------------------
class MouseMQTTGame:
    def __init__(self, root, config, width=800, height=600):
        self.root = root
        self.config = config
        self.latest_mouse = (0, 0)
        self.remote_mouse = None
        self.receive_queue = queue.Queue()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.root.title("Steroids! Do'em!")
        self.root.geometry(f"{width}x{height}")
        self.canvas = tk.Canvas(root, width=width, height=height, bg="#4E3F3F")
        self.canvas.pack(fill="both", expand=True)
        self.status_text = self.canvas.create_text(
            10,
            10,
            anchor="nw",
            fill="#ffffff",
            font=("Arial", 12),
            text="Connecting to MQTT...",
    
        )
        self.plr_updateTime_last = 0
        # delay 1 second
        time.sleep(1)


        sheet = Image.open(SPRITESHEET_PATH).convert("RGBA")

        # self.local_circle = self.canvas.create_oval(0, 0, 20, 20, fill="#33cc33", outline="")
        self.remote_circle = self.canvas.create_oval(0, 0, 0, 0, fill="#ff4444", outline="")
        #triangle
        self.local_sprite = self.canvas.create_polygon(plrs[0].x-5, plrs[0].y, plrs[0].x+5, plrs[0].y-20, plrs[0].x+15, plrs[0].y, fill="#33cc33", outline="#FFFFFF")
        self.local_sprite2 = self.canvas.create_polygon(400, 300, 405, 280, 415, 300, fill="#334acc", outline="#AD2C2C")

        self.remote_text = self.canvas.create_text(
            780,
            10,
            anchor="ne",
            fill="#ffffff",
            font=("Arial", 12),
            text="Remote: --",
        )
        self.plr0_text = self.canvas.create_text(
            780,
            30,
            anchor="ne",
            fill="#ffffff",
            font=("Arial", 12),
            text="plr0: --",
        )

        self.connect_mqtt()

        self.canvas.bind("<Motion>", self.on_mouse_move)

        root.bind("<Key>", self.on_key)

        # self.canvas.bind("<Left arrrow>", lambda e: print("Spin Left"))

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.update_loop()
        self.publish_loop()
        self.plr_update_loop()
    
    # Helper: extract frame index -> PIL Image
    def get_frame_image(self,frame_index):
        fi = frame_index % NUM_FRAMES
        left = SHEET_X_OFFSET + fi * FRAME_W
        upper = SHEET_Y_OFFSET
        box = (left, upper, left + FRAME_W, upper + FRAME_H)
        return self.sheet.crop(box)
    # Cache rotated frames for a given animation frame and angle (optional)
    _cache = {}  # key: (frame_index, angle) -> ImageTk.PhotoImage

    def get_rotated_photo(frame_index, angle):
        key = (frame_index, angle % 360)
        if key in _cache:
            return _cache[key]
        frame = get_frame_image(frame_index)
        rotated = frame.rotate(-angle, resample=Image.BICUBIC, expand=True)
        photo = ImageTk.PhotoImage(rotated)
        _cache[key] = photo
        return photo
    
    def connect_mqtt(self):
        host = parse_mqtt_host(self.config["server"])
        port = self.config["port"]
        try:
            self.client.connect(host, port, keepalive=60)
        except Exception as exc:
            print(f"Error connecting to MQTT broker {host}:{port}: {exc}")
            #insert 1 player link
            #
            messagebox.showerror("MQTT Connection", f"Unable to connect to MQTT broker {host}:{port}\n{exc}")
            self.root.destroy()
            return

        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        status = "connected" if rc == 0 else f"failed (rc={rc})"
        self.canvas.itemconfigure(self.status_text, text=f"MQTT {status} to {self.config['server']}:{self.config['port']}")
        if rc == 0:
            client.subscribe(self.config["sub_topic"])
            print(f"MQTT connected successfully to {self.config['server']}:{self.config['port']}")
        else:
            messagebox.showerror("MQTT Connection", f"Failed to connect to MQTT broker: {status}")  
            print(f"MQTT connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            event = json.loads(payload)
            x = int(event.get("x", 0))
            y = int(event.get("y", 0))
            self.receive_queue.put((x, y))
            # print(f"Received MQTT message: {payload}")
        except Exception:
            # ignore invalid payloads
            # print(f"Received invalid MQTT message: {msg.payload}")
            pass

    def on_mouse_move(self, event):
        self.latest_mouse = (event.x, event.y)
        # self.canvas.coords(
        #     self.local_sprite,
        #     event.x - 2,
        #     event.y - 2,
        #     event.x + 2,
        #     event.y + 2,
        # )
    
    def on_key(self,event):
        # dx = dy = 0
        if event.keysym == "Left":
            print("Spin Left")
            plrs[0].thd += 0.1
        elif event.keysym == "Right":
            # dx = 10
            print("Spin Right")
            plrs[0].thd -= 0.1
            plrs[0].x = plrs[0].x+10
        elif event.keysym == "Up":
            # dy = -10
            print("Spin Up")
            plrs[0].v += 0.1
        elif event.keysym == "Down":
            # dy = 10
            print("Spin Down")
            plrs[0].v -= 0.1
        # if dx or dy:
        #     c.move(rect, dx, dy)

    def update_loop(self):
        while not self.receive_queue.empty():
            self.remote_mouse = self.receive_queue.get_nowait()
        if self.remote_mouse is not None:
            rx, ry = self.remote_mouse
            self.canvas.coords(self.remote_circle, rx - 5, ry - 5, rx + 5, ry + 5)
            self.canvas.itemconfigure(self.remote_text, text=f"Remote: {rx}, {ry}")
        else:
            self.canvas.coords(self.remote_circle, 0, 0, 0, 0)
            self.canvas.itemconfigure(self.remote_text, text="Remote: --")
        # update local player text
        self.canvas.itemconfigure(self.plr0_text, text=f"plr0: {int(plrs[0].x)}, {int(plrs[0].y)}, th={round(plrs[0].th,2)}, v={round(plrs[0].v,2)}")
        self.root.after(50, self.update_loop)

    def publish_loop(self):
        x, y = self.latest_mouse
        payload = json.dumps({"x": x, "y": y, "timestamp": time.time()})
        self.client.publish(self.config["pub_topic"], payload, qos=0)
        self.root.after(50, self.publish_loop)

    def plr_update_loop(self):
        # dt = time.time() - self.plr_updateTime_last

        for plr in plrs.values():
            plr.update(0.05)  # seconds


        # update local sprite position
        # self.canvas.coords(
        #     self.local_sprite,
        #     plrs[0].x - 5,
        #     plrs[0].y,
        #     plrs[0].x + 5,
        #     plrs[0].y - 20,
        #     plrs[0].x + 15,
        #     plrs[0].y
        # )

        # rotate local sprite
        # x0, y0 = plrs[0].x, plrs[0].y
        # th = plrs[0].th
        # points = [
        #     (x0 - 5, y0),
        #     (x0 + 5, y0 - 20),
        #     (x0 + 15, y0)
        # ]
        # rotated_points = []

        # self.root.after(int(dt * 1000), self.plr_update_loop)
        self.root.after(50, self.plr_update_loop)

    def on_close(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    cfg = load_config()
    root = tk.Tk()
    app = MouseMQTTGame(root, cfg)
    root.mainloop()
