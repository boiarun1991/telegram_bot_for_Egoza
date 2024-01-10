from PIL import Image, ImageOps, ImageFont, ImageDraw
import requests
import textwrap
import os

from config import Config, load_config

config: Config = load_config()
BOT_TOKEN: str = config.tg_bot.token
URL = 'https://api.telegram.org/bot'


class Photo:
    def __init__(self, chat_id, img):
        self.chat_id = chat_id
        self.img = img

    @staticmethod
    def create_photo(text, chat_id, color=None):
        colors = {'⚫ Чёрный': 'black',
                  '🔴 Красный': 'red',
                  '🔵 Синий': 'blue',
                  '🟢 Зелёный': 'green',
                  '💜 Пурпурный': 'purple',

                  '⚪ Белый': 'white',
                  '❄️Бирюзовый': 'turquoise',
                  '🌸 Розовый': 'hotpink',
                  '🟠 Оранжевый': 'orange',
                  '🟡 Жёлтый': 'yellow',
                  }

        if color in list(colors)[:5]:
            stroke_color = 'white'
        else:
            stroke_color = 'black'

        def settings_font_cube(wrap_count):
            settings = {}
            if wrap_count == 1:
                settings.setdefault('x', int(base_image.size[0] / 18))
                settings.setdefault('y', height - watermark.size[1] / 2.3)
                settings.setdefault('font_size', int(watermark.size[1] / 4.8))
                return settings
            elif wrap_count == 2:
                settings.setdefault('x', int(base_image.size[0] / 12))
                settings.setdefault('y', int(height - watermark.size[1] / 2.1))
                settings.setdefault('font_size', int(watermark_line.size[1] / 3.9))
                return settings
            elif wrap_count == 3:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 12))
                settings.setdefault('y', int(height - watermark_line.size[1] / 1.2))
                settings.setdefault('font_size', int(watermark_line.size[1] / 3.7))
                return settings

        def settings_font_horizontal(wrap_count):
            settings = {}
            if wrap_count == 1:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 15))
                settings.setdefault('y', int(height - watermark_line.size[1] / 1.5))
                settings.setdefault('font_size', int(watermark.size[1] / 3.5))
                return settings
            elif wrap_count == 2:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 5))
                settings.setdefault('y', int(height - watermark.size[1] / 2))
                settings.setdefault('font_size', int(watermark_line.size[1] / 2.75))
                return settings
            elif wrap_count == 3:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 6))
                settings.setdefault('y', int(height - watermark_line.size[1] / 1.2))
                settings.setdefault('font_size', int(watermark_line.size[1] / 3.7))
                return settings

        def settings_font_vertical(wrap_count):
            settings = {}
            if wrap_count == 1:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 12))
                settings.setdefault('y', int(height - watermark_line.size[1] / 1.8))
                settings.setdefault('font_size', int(watermark.size[1] / 5.2))
                return settings
            elif wrap_count == 2:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 12))
                settings.setdefault('y', int(height - watermark_line.size[1] / 1.4))
                settings.setdefault('font_size', int(watermark_line.size[1] / 3.5))
                return settings
            elif wrap_count == 3:
                settings.setdefault('x', int((base_image.size[0] - watermark.size[0]) / 12))
                settings.setdefault('y', int(height - watermark_line.size[1] / 1.2))
                settings.setdefault('font_size', int(watermark_line.size[1] / 3.5))
                return settings

        base_image = Image.open(f'download_photo_{chat_id}.jpg')

        width, height = base_image.size
        num_lines = len(textwrap.wrap(text, width=20, max_lines=3))
        if width > height:
            watermark_line = Image.open('files/gradient_80.png').resize(
                (base_image.size[0], int(base_image.size[1] / 5.5)))
            watermark = Image.open('files/egoza_logo_cube.png').resize(
                (int(watermark_line.size[1] * 1.5), int(watermark_line.size[1] * 1.5)))
            position_watermark = (width - watermark.size[0], int(height - watermark.size[0] * 1.1))
            position_line = (0, base_image.size[1] - watermark_line.size[1])
            transparent = Image.new('RGB', (width, height), (0, 0, 0,))
            transparent.paste(base_image, (0, 0))
            transparent.paste(watermark_line, position_line, mask=watermark_line)
            transparent.paste(watermark, position_watermark, mask=watermark)
            font = ImageFont.truetype('fonts/AppetiteNew.ttf', settings_font_horizontal(num_lines).get('font_size'))
            drawer = ImageDraw.Draw(transparent)
            drawer.text((settings_font_horizontal(num_lines).get('x'), settings_font_horizontal(num_lines).get('y')),
                        "\n".join(textwrap.wrap(text, width=20, max_lines=3)), align='center', font=font,
                        fill=colors.get(color),
                        stroke_width=4, stroke_fill=stroke_color)
            transparent.save(f'download_photo_{chat_id}.jpg')
        elif width < height:

            watermark_line = Image.open('files/gradient_80.png').resize(
                (base_image.size[0], int(base_image.size[1] / 7)))
            watermark = Image.open('files/egoza_logo_cube.png').resize(
                (int(watermark_line.size[1] * 1.6), int(watermark_line.size[1] * 1.5)))
            position_watermark = (int(width - watermark.size[0]), int(height - watermark.size[0]))
            position_line = (0, base_image.size[1] - watermark_line.size[1])
            transparent = Image.new('RGB', (width, height), (0, 0, 0,))
            transparent.paste(base_image, (0, 0))
            transparent.paste(watermark_line, position_line, mask=watermark_line)
            transparent.paste(watermark, position_watermark, mask=watermark)

            font = ImageFont.truetype('fonts/AppetiteNew.ttf', settings_font_vertical(num_lines).get('font_size'))
            drawer = ImageDraw.Draw(transparent)
            drawer.text((settings_font_vertical(num_lines).get('x'), settings_font_vertical(num_lines).get('y')),
                        "\n".join(textwrap.wrap(text, width=20, max_lines=3)), align='center', font=font,
                        fill=colors.get(color),
                        stroke_width=4, stroke_fill=stroke_color)
            transparent.save(f'download_photo_{chat_id}.jpg')
        else:
            watermark_line = Image.open('files/gradient_80.png').resize(
                (base_image.size[0], int(base_image.size[1] / 5.5)))
            watermark = Image.open('files/egoza_logo_cube.png').resize(
                (int(watermark_line.size[1] * 1.6), int(watermark_line.size[1] * 1.5)))
            position_watermark = (width - watermark.size[0], int(height - watermark.size[0] * 1.05))
            position_line = (0, base_image.size[1] - watermark_line.size[1])
            transparent = Image.new('RGB', (width, height), (0, 0, 0,))
            transparent.paste(base_image, (0, 0))
            transparent.paste(watermark_line, position_line, mask=watermark_line)
            transparent.paste(watermark, position_watermark, mask=watermark)
            font = ImageFont.truetype('fonts/AppetiteNew.ttf', settings_font_cube(num_lines).get('font_size'))
            drawer = ImageDraw.Draw(transparent)
            drawer.text((settings_font_cube(num_lines).get('x'), settings_font_cube(num_lines).get('y')),
                        "\n".join(textwrap.wrap(text, width=20, max_lines=3)), align='center', font=font,
                        fill=colors.get(color),
                        stroke_width=4, stroke_fill='black')
            transparent.save(f'download_photo_{chat_id}.jpg')

    @staticmethod
    def paste_watermark(chat_id=None):
        base_image = Image.open(f'download_photo_{chat_id}.jpg')
        width, height = base_image.size
        if width >= height:
            watermark = Image.open('files/egoza_logo_cube.png').resize(
                (int(base_image.size[1] / 4.5), int(base_image.size[1] / 6)))
            position_watermark = (int(width - watermark.size[0]), height - watermark.size[1])
            transparent = Image.new('RGB', (width, height), (0, 0, 0,))
            transparent.paste(base_image, (0, 0))
            transparent.paste(watermark, position_watermark, mask=watermark)
            transparent.save(f'download_photo_{chat_id}.jpg')
        else:
            watermark = Image.open('files/egoza_logo_cube.png').resize(
                (int((base_image.size[0] / 4.5)), int(base_image.size[1] / 6)))
            position_watermark = (int(width - watermark.size[0]), int(height - watermark.size[1]))
            transparent = Image.new('RGB', (width, height), (0, 0, 0,))
            transparent.paste(base_image, (0, 0))
            transparent.paste(watermark, position_watermark, mask=watermark)
            transparent.save(f'download_photo_{chat_id}.jpg')

    def send_photo_file(self):
        files = {'photo': open(self.img, 'rb')}
        requests.post(f'{URL}{BOT_TOKEN}/sendPhoto?chat_id={self.chat_id}', files=files)
        files.clear()
        os.remove(self.img)
