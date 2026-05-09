"""
SpriteLoader - Manages sprite sheet loading, frame extraction, and caching.
Handles rotation transformations and photo image caching for efficient rendering.
"""

from PIL import Image, ImageTk
import os


class SpriteLoader:
    """
    Loads and manages sprites from a spritesheet with support for:
    - Frame extraction from grids
    - Rotation caching
    - PhotoImage management for Tkinter rendering
    """

    def __init__(self, spritesheet_path, frame_w, frame_h, base_x=0, base_y=0,
                 sheet_cols=None, sheet_rows=None, sheet_row=None, num_frames=None, angle_step=10):
        """
        Initialize sprite loader.

        Args:
            spritesheet_path: Path to the spritesheet image
            frame_w: Width of a single frame in pixels
            frame_h: Height of a single frame in pixels
            base_x: X offset to start reading frames from
            base_y: Y offset to start reading frames from
            sheet_cols: Number of columns in spritesheet (None = auto-infer)
            sheet_rows: Number of rows in spritesheet (None = auto-infer)
            num_frames: Total number of frames (None = auto-infer from cols*rows)
            angle_step: Degrees between cached rotations (e.g., 10 = 36 directions)
        """
        self.spritesheet_path = spritesheet_path
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.base_x = base_x
        self.base_y = base_y
        self.angle_step = angle_step

        # Load spritesheet
        self.sheet = Image.open(spritesheet_path).convert("RGBA")
        sheet_w, sheet_h = self.sheet.size

        # Infer spritesheet layout
        self.sheet_cols = sheet_cols or (sheet_w // frame_w)
        self.sheet_rows = sheet_rows or max(1, sheet_h // frame_h)
        self.sheet_row = sheet_row or 1
        self.num_frames = num_frames or (self.sheet_cols * self.sheet_rows)

        # Cache for rotated frames: (frame_index, quantized_angle) -> PhotoImage
        self._image_cache = {}

    def crop_frame(self, frame_index):
        """
        Extract a single frame from the spritesheet.

        Args:
            frame_index: Index of the frame (wraps around if > num_frames)

        Returns:
            PIL Image of the extracted frame
        """
        fi = frame_index % self.num_frames
        col = fi % self.sheet_cols
        row = self.sheet_row + fi // self.sheet_cols
        left = self.base_x + col * self.frame_w
        upper = self.base_y + row * self.frame_h
        return self.sheet.crop((left, upper, left + self.frame_w, upper + self.frame_h))

    def quantize_angle(self, angle):
        """
        Round angle to nearest step for caching efficiency.

        Args:
            angle: Angle in degrees

        Returns:
            Quantized angle in degrees (0-359)
        """
        return int(round(angle / self.angle_step) * self.angle_step) % 360

    def get_rotated_photo(self, frame_index, angle=0):
        """
        Get a rotated PhotoImage, using cache if available.

        Args:
            frame_index: Index of the frame
            angle: Rotation angle in degrees (clockwise)

        Returns:
            ImageTk.PhotoImage object ready for Tkinter canvas
        """
        q = self.quantize_angle(angle)
        key = (frame_index % self.num_frames, q)

        # if key in self._image_cache:
        #     return self._image_cache[key]

        # Extract frame and rotate
        base = self.crop_frame(key[0])
        rotated = base.rotate(-q, resample=Image.BICUBIC, expand=True)
        photo = ImageTk.PhotoImage(rotated)

        # Cache the result
        self._image_cache[key] = photo
        return photo

    def preload_frames(self, frame_indices=None):
        """
        Pre-render frames with all rotation angles.
        Useful for avoiding lag during gameplay.

        Args:
            frame_indices: List of frame indices to preload (None = all frames)
        """
        indices = frame_indices or range(self.num_frames)
        for fi in indices:
            for angle in range(0, 360, self.angle_step):
                self.get_rotated_photo(fi, angle)

    def clear_cache(self):
        """Clear the image cache to free memory."""
        self._image_cache.clear()

    def get_cache_size(self):
        """Return number of cached images."""
        return len(self._image_cache)
