import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

class ImageGridViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image Grid Viewer")
        self.geometry("900x600")

        #
        self.offset_x = 1
        self.offset_y = 7

        # Controls frame
        ctrl = tk.Frame(self)
        ctrl.pack(side="top", fill="x")
        tk.Button(ctrl, text="Open Image", command=self.open_image).pack(side="left")
        tk.Label(ctrl, text="Grid size:").pack(side="left", padx=(8,0))
        self.grid_size_var = tk.IntVar(value=36)
        tk.Spinbox(ctrl, from_=4, to=512, increment=1, textvariable=self.grid_size_var, width=6, command=self.redraw_grid).pack(side="left")
        self.show_grid_var = tk.BooleanVar(value=True)
        tk.Checkbutton(ctrl, text="Show grid", variable=self.show_grid_var, command=self.redraw_grid).pack(side="left", padx=8)
        tk.Button(ctrl, text="Fit to window", command=self.fit_to_window).pack(side="left", padx=8)

        # Canvas + scrollbars
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg="black")
        self.hbar = tk.Scrollbar(container, orient="horizontal", command=self.canvas.xview)
        self.vbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.hbar.pack(side="bottom", fill="x")
        self.vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Status bar
        self.status = tk.Label(self, text="No image loaded", anchor="w")
        self.status.pack(side="bottom", fill="x")

        # Mouse bindings
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)

        # Image state
        self.img = None           # PIL Image (original)
        self.tkimg = None         # PhotoImage shown on canvas
        self.img_id = None        # canvas image id
        self.grid_ids = []        # canvas line ids

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Images","*.png;*.jpg;*.jpeg;*.bmp;*.gif;*.tiff"),("All files","*.*")])
        if not path:
            return
        self.img = Image.open(path).convert("RGBA")
        self.display_image(self.img)

    def display_image(self, pil_image):
        self.canvas.delete("all")
        self.grid_ids.clear()
        w, h = pil_image.size
        self.tkimg = ImageTk.PhotoImage(pil_image)
        self.img_id = self.canvas.create_image(0, 0, image=self.tkimg, anchor="nw")
        # set scroll region to image size
        self.canvas.config(scrollregion=(0,0,w,h))
        self.status.config(text=f"Image loaded: {w}x{h} px")
        self.redraw_grid()

    def redraw_grid(self):
        print("REDRAW GRID with size:", self.grid_size_var.get())
        # remove old grid lines
        for gid in self.grid_ids:
            try:
                self.canvas.delete(gid)
            except Exception:
                pass
        self.grid_ids.clear()
        if not self.img or not self.show_grid_var.get():
            return
        grid = max(1, int(self.grid_size_var.get()))
        w, h = self.img.size
        # Draw light lines (every grid) and darker lines (every 8th)
        color_light = "blue"  # semi-transparent white (alpha ignored by Tk; gives hex fallback)
        color_dark = "red"
        for x in range(0, w+1, grid):
            color = color_dark if (x//grid) % 8 == 0 else color_light
            gid = self.canvas.create_line(self.offset_x+x, self.offset_y, self.offset_x+x, h, fill=color)
            self.grid_ids.append(gid)
        for y in range(0, h+1, grid):
            color = color_dark if (y//grid) % 8 == 0 else color_light
            gid = self.canvas.create_line(self.offset_x, self.offset_y+y, self.offset_x+w, self.offset_y+y, fill=color)
            self.grid_ids.append(gid)

    def on_mouse_move(self, event):
        if not self.img:
            return
        # canvas coords -> image pixel coords (account for scrolling)
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        ix, iy = int(canvas_x), int(canvas_y)
        w, h = self.img.size
        if 0 <= ix < w and 0 <= iy < h:
            self.status.config(text=f"X: {ix}  Y: {iy}   (Grid: {self.grid_size_var.get()} px)")
        else:
            self.status.config(text=f"Outside image  (X: {ix}  Y: {iy})")

    def on_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        print("Clicked at:", int(canvas_x), int(canvas_y))

    def fit_to_window(self):
        if not self.img:
            return
        # scale image to fit canvas visible area while preserving aspect ratio
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            self.after(50, self.fit_to_window); return
        w, h = self.img.size
        scale = min(cw / w, ch / h, 1.0)
        if scale == 1.0:
            self.display_image(self.img)
            return
        new = self.img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
        # store a scaled version but keep original for coordinate mapping
        self.tkimg = ImageTk.PhotoImage(new)
        self.canvas.delete("all")
        self.img_id = self.canvas.create_image(0, 0, image=self.tkimg, anchor="nw")
        self.canvas.config(scrollregion=(0,0,new.width, new.height))
        # When scaled, adjust grid drawing to scaled pixels
        # draw grid using scaled spacing proportional to original grid size
        grid = max(1, int(self.grid_size_var.get()))
        scaled_grid = max(1, int(grid * (new.width / w)))
        self.grid_ids.clear()
        color_light = "#ffffff40"
        color_dark = "#ffffff80"
        for x in range(0, new.width+1, scaled_grid):
            color = color_dark if (x//scaled_grid) % 8 == 0 else color_light
            gid = self.canvas.create_line(x, 0, x, new.height, fill=color)
            self.grid_ids.append(gid)
        for y in range(0, new.height+1, scaled_grid):
            color = color_dark if (y//scaled_grid) % 8 == 0 else color_light
            gid = self.canvas.create_line(0, y, new.width, y, fill=color)
            self.grid_ids.append(gid)

if __name__ == "__main__":
    app = ImageGridViewer()
    app.mainloop()
