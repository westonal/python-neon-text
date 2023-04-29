#!/usr/bin/env python3

import argparse
import array
import math

import cairo
from PIL import ImageFilter, Image
from tools import transform_color
import cv2
import numpy as np


class NeonGlowText:
    """Neon glow text"""

    MIN_FONT_SIZE = 20
    MAX_FONT_SIZE = 300
    MAX_PADDING = 120
    MIN_SHADOW = 20
    FONT = "Zapfino"

    BG_COLOR = '000000'
    GLOW_COLOR = 'ec0e77'  # (0.929, 0.055, 0.467)
    FG_COLOR_1 = 'ff31f4'  # (1, 0.196, 0.957)
    FG_COLOR_2 = 'ffd796'  # (1, 0.847, 0.592)
    FILL_COLOR = 'FFFFFF'

    def __init__(self, args_dict):
        self.text = args_dict.get('text')
        self.filename = args_dict.get('filename')
        self.width = args_dict.get('width')
        self.height = args_dict.get('height')
        self.font = args_dict.get('font')
        self.font_size = None
        self.bg_color = args_dict.get('bg_color')
        self.glow_color = args_dict.get('glow_color')
        self.fill_color = args_dict.get('fill_color')
        self.stroke_1_color = args_dict.get('stroke_1_color')
        self.stroke_2_color = args_dict.get('stroke_2_color')

    def draw_loop(self):
        frame = 0
        while True:
            surface = self.draw(angle=math.radians(frame % 360))

            buf = surface.get_data()
            array = np.ndarray(shape=(surface.get_width(), surface.get_height(), 4), dtype=np.uint8, buffer=buf)

            frame += 1
            print(f"Frame {frame}")
            cv2.imshow("Gauge", array)
            key = cv2.waitKey(1000 // 50)

            if key != -1:
                break

        cv2.destroyAllWindows()  # destroy all windows

    def draw(self, angle=None):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)

        cr = cairo.Context(surface)

        self._set_font(cr)
        self._move_to_center(cr)

        self._paint_bg(cr)

        # cr.text_path(self.text)
        # cr.arc(120, 120, 100, 1, 2)
        cr.new_sub_path()
        start_angle = 0 + math.pi/2

        end_angle = angle + math.pi/2
        cr.arc(120, 120, 100, start_angle, end_angle)
        self._draw_neon(cr, width_mul=5.0)
        cr.new_sub_path()
        cr.arc(120, 120, 50, start_angle, end_angle)
        self._draw_neon(cr, width_mul=5.0)

        # Make glow darker
        intensity = 0.6
        cr.set_source_rgba(0, 0, 0, 1 - intensity)
        cr.fill()

        # surface.write_to_png(self.filename + ".bg.png")

        surface = self._blur(surface, 10)
        cr = cairo.Context(surface)

        # cr.arc(120, 120, 100, 1, 2)
        # self._draw_neon(cr)

        # self._set_font(cr)
        # self._move_to_center(cr)
        #
        cr.new_sub_path()
        cr.arc(120, 120, 100, start_angle, end_angle)
        self._draw_neon(cr)
        cr.new_sub_path()
        cr.arc(120, 120, 50, start_angle, end_angle)
        self._draw_neon(cr)

        surface = self._blur(surface, 1)
        cr = cairo.Context(surface)

        # surface.write_to_png(self.filename)
        return surface

    def _set_font(self, cr):
        cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        if self.font_size:
            cr.set_font_size(self.font_size)
            return

        # Let's find an appropriate font size...
        f_size = self.MAX_FONT_SIZE

        while True:
            cr.set_font_size(f_size)
            _, _, t_width, t_height, _, _ = cr.text_extents(self.text)

            # Check if text is within the desired boundaries
            if not (t_width > self.width - min(self.MAX_PADDING, f_size) or
                    t_height > self.height - min(self.MAX_PADDING, f_size)) \
                    or f_size <= self.MIN_FONT_SIZE:
                break

            f_size -= 2

        self.font_size = f_size

    def _move_to_center(self, cr):
        cr.select_font_face(self.font, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(self.font_size)
        x_bearing, y_bearing, t_width, t_height, _, _ = cr.text_extents(self.text)

        x = self.width / 2 - (t_width / 2 + x_bearing)
        y = self.height / 2 - (t_height / 2 + y_bearing)

        cr.move_to(x, y)

    def _paint_bg(self, cr):
        cr.set_source_rgb(*transform_color(self.bg_color))
        cr.paint()

    def _draw_glow(self, cr):
        stroke_width = max(self.font_size / 3, self.MIN_SHADOW)
        self._draw_stroke(cr, self.glow_color, stroke_width)
        # self._fill(cr, self.fill_color)

    def _draw_stroke(self, cr, rgb, stroke_width):
        cr.set_source_rgb(*transform_color(rgb))
        cr.set_line_width(stroke_width)
        cr.set_line_cap(cairo.LineCap.ROUND)
        cr.stroke_preserve()

    def _fill(self, cr, rgb):
        cr.set_source_rgb(*transform_color(rgb))
        cr.fill()

    def _draw_neon(self, cr, width_mul=1.0):
        cr.set_line_cap(cairo.LineCap.ROUND)
        self._draw_stroke(cr, self.stroke_1_color, (10 if self.font_size > 100 else 5) * width_mul)
        self._draw_stroke(cr, self.stroke_2_color, (5 if self.font_size > 100 else 2) * width_mul)
        # self._fill(cr, self.fill_color)
        pass

    def _blur(self, surface, blur_amount):
        # Load as PIL Image
        bg_image = Image.frombuffer("RGBA", (surface.get_width(), surface.get_height()), surface.get_data(), "raw",
                                    "RGBA", 0, 1)

        # Apply blur
        blurred_image = bg_image.filter(ImageFilter.GaussianBlur(blur_amount))

        # Restore cairo surface
        image_bytes = blurred_image.tobytes()
        image_array = array.array('B', image_bytes)
        stride = cairo.ImageSurface.format_stride_for_width(cairo.FORMAT_ARGB32, self.width)

        return surface.create_for_data(image_array, cairo.FORMAT_ARGB32, self.width, self.height, stride)


def main():
    args = _parse_arguments()
    neon_text = NeonGlowText(args)
    neon_text.draw_loop()


def _parse_arguments():
    parser = argparse.ArgumentParser(
        description='Creates a neon glow effect image with the given text')

    parser.add_argument('-t', '--text',
                        help='Text to render',
                        default="Alan")
    parser.add_argument('-f', '--filename',
                        help='Image filename (png)',
                        default=None)

    parser.add_argument('--width',
                        help='Image width in pixels',
                        type=int,
                        default=240)
    parser.add_argument('--height',
                        help='Image height in pixels',
                        type=int,
                        default=240)

    parser.add_argument('--font',
                        help='Font name',
                        default=NeonGlowText.FONT)

    parser.add_argument('-bc', '--bg-color',
                        help='Image background color in hex (e.g. 020202)',
                        default=NeonGlowText.BG_COLOR)
    parser.add_argument('-gc', '--glow-color',
                        help='Text glow color in hex (e.g. EC0E77)',
                        default=NeonGlowText.GLOW_COLOR)
    parser.add_argument('-fc', '--fill-color',
                        help='Text fill color in hex (e.g. FFFFFF)',
                        default=NeonGlowText.FILL_COLOR)
    parser.add_argument('-s1c', '--stroke-1-color',
                        help='Text stroke 1 color in hex (e.g. FF31F4)',
                        default=NeonGlowText.FG_COLOR_1)
    parser.add_argument('-s2c', '--stroke-2-color',
                        help='Text stroke 2 color in hex (e.g. FFD796)',
                        default=NeonGlowText.FG_COLOR_2)

    return vars(parser.parse_args())


if __name__ == '__main__':
    main()
    # neon_text = NeonGlowText({
    #     'width':240,
    #     'height': 240,
    # })
    # neon_text.draw_loop()
