import asyncio
import os
import time

from PIL import Image, ImageOps, ImageFont, ImageDraw
from aiogram import Bot, Dispatcher, F, types
import requests
import textwrap
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, PhotoSize
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.redis import RedisStorage, Redis
from config import Config, load_config

config: Config = load_config()
BOT_TOKEN: str = config.tg_bot.token
URL = 'https://api.telegram.org/bot'
redis = Redis(host='5.35.11.130')
# Создаем объекты бота и диспетчера
storage = RedisStorage(redis=redis)
settings_dict = {}
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

LEXICON: dict[str, str] = {
    'bt_black': '⚫ Чёрный',
    'bt_white': '⚪ Белый',
    'bt_red': '🔴 Красный',
    'bt_orange': '🟠 Оранжевый',
    'bt_yellow': '🟡 Жёлтый',
    'bt_green': '🟢 Зелёный',
    'bt_blue': '🔵 Синий',
    'bt_turquoise': '❄️Бирюзовый',
    'bt_hotpink': '🌸 Розовый',
    'bt_purple': '💜 Пурпурный'
}


class FSMEditPhoto(StatesGroup):
    upload_photo = State()
    fill_need_text = State()
    fill_color = State()
    fill_text = State()
    fill_send_photo = State()


@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text='Отменять нечего. Мы ещё не начали работать\n\n'
             'Чтобы перейти редактированию фото - '
             'отправьте команду /editphoto'
    )


# @dp.message(Command(commands='cancel'), ~StateFilter(default_state))
# async def process_cancel_command_state(message: Message, state: FSMContext):
#     await message.answer(
#         text='Вы вышли из редактирования фото\n\n'
#              'Чтобы снова перейти редактированию - '
#              'отправьте команду /editphoto'
#     )
#     await state.clear()


# @dp.message(Command(commands='editphoto'), StateFilter(default_state))
# async def process_editphoto_command(message: Message, state: FSMContext):
#     await message.answer(text='Пожалуйста пришлите фото для редактирования')
#     # Устанавливаем состояние ожидания ввода имени
#     await state.set_state(FSMEditPhoto.upload_photo)


@dp.message(F.photo)
async def process_photo_sent(message: Message,
                             state: FSMContext):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище
    # по ключам "photo_unique_id" и "photo_id"
    file_id = message.photo[len(message.photo) - 1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    await bot.download_file(file_path, f'download_photo_{message.chat.id}.jpg')
    await state.update_data(
        photo_unique_id=file_path,
        photo_id=file_id
    )
    # Создаем объекты инлайн-кнопок
    button_yes = InlineKeyboardButton(
        text='✅ Да',
        callback_data='bt_yes'
    )
    button_no = InlineKeyboardButton(
        text='❌ Нет',
        callback_data='bt_no'
    )
    keyboard: list[list[InlineKeyboardButton]] = [[button_yes, button_no]]

    # Создаем объект инлайн-клавиатуры
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    # Отправляем пользователю сообщение с клавиатурой
    await message.answer(
        text='🖼️ Фото загружено\n\n ✒️Нужна ли надпись?\n\n'
             '☝️ Учтите ограниченность области для надписи\n'
             'Количество символов = 6️⃣0️⃣',
        reply_markup=markup
    )
    await state.set_state(FSMEditPhoto.fill_color)


# Этот хэндлер будет срабатывать, если во время отправки фото
# будет введено/отправлено что-то некорректное
# @dp.message(StateFilter(FSMEditPhoto.upload_photo))
# async def warning_not_photo(message: Message):
#     await message.answer(
#         text='Пожалуйста, на этом шаге отправьте '
#              'фото\n\nЕсли вы хотите прервать '
#              'редактирование - отправьте команду /cancel'
#     )


@dp.callback_query(StateFilter(FSMEditPhoto.fill_color), F.data.in_(['bt_yes']))
async def process_color_vote(callback: CallbackQuery, state: FSMContext):
    await state.update_data(need_text=callback.data)
    keyboard = create_inline_kb(2, 'bt_black', 'bt_white', 'bt_red',
                                'bt_blue', 'bt_yellow', 'bt_green', 'bt_hotpink',
                                'bt_purple', 'bt_turquoise', 'bt_orange')
    await callback.message.edit_text(
        text='Отлично!\n\n🎨 Выберите цвет для надписи...',
        reply_markup=keyboard
    )
    await state.set_state(FSMEditPhoto.fill_color)


@dp.callback_query(StateFilter(FSMEditPhoto.fill_color),
                   F.data.in_(['bt_black', 'bt_white', 'bt_red',
                               'bt_blue', 'bt_yellow', 'bt_green', 'bt_hotpink',
                               'bt_purple', 'bt_turquoise', 'bt_orange']))
async def process_wish_news_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(color=callback.data)
    await callback.message.edit_text(
        text='👌 Хорошо! Данные сохранены!\n\n'
             '✍️ Введите текст надписи...'
    )

    await state.set_state(FSMEditPhoto.fill_text)


@dp.message(StateFilter(FSMEditPhoto.fill_text))
async def process_name_sent(message: Message, state: FSMContext):
    await state.update_data(text_on_photo=message.text)
    await message.answer(text='🤏 Ещё чуть-чуть...\n\n🤖⚙️ Работаю, ожидайте')
    settings_dict[message.chat.id] = await state.get_data()
    await state.clear()
    photo_creator = Photo(message.chat.id, f'download_photo_{message.chat.id}.jpg')
    photo_creator.create_photo(text=settings_dict.get(message.chat.id, {}).get('text_on_photo'),
                               chat_id=message.chat.id,
                               color=LEXICON.get(settings_dict.get(message.chat.id, {}).get('color')))
    photo_creator.send_photo_file()
    await message.answer(text='🤗 Рад был помочь\n\n'
                              '😉 До новых встреч!\n\n'
                              '🤖📷 Если вы хотите продолжить, просто отправьте мне новое фото!')
    print(settings_dict)
    print(LEXICON.get(settings_dict.get(message.chat.id, {}).get('color')))


@dp.callback_query(StateFilter(FSMEditPhoto.fill_color), F.data.in_(['bt_no']))
async def process_color_vote(callback: CallbackQuery, state: FSMContext):
    await state.update_data(need_text=callback.data)
    await callback.message.edit_text(text='👌 Хорошо.\n\n🤖 Работаю, ожидайте...')
    settings_dict[callback.message.chat.id] = await state.get_data()
    await state.clear()
    photo_creator = Photo(callback.message.chat.id, f'download_photo_{callback.message.chat.id}.jpg')
    photo_creator.paste_watermark(chat_id=callback.message.chat.id)
    photo_creator.send_photo_file()


def create_inline_kb(width: int,
                     *args: str,
                     **kwargs: str) -> InlineKeyboardMarkup:
    # Инициализируем билдер
    kb_builder = InlineKeyboardBuilder()
    # Инициализируем список для кнопок
    buttons: list[InlineKeyboardButton] = []

    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=LEXICON[button] if button in LEXICON else button,
                callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))
    kb_builder.row(*buttons, width=width)
    return kb_builder.as_markup()


#

#
#
# # Этот хэндлер будет срабатывать на команду "/start"
@dp.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(f'Здравствуйте!\n'
                         f'этот бот предназначен для помощи воспитателям\n'
                         f'детского сада "Егоза" c. Култаево\n\n'
                         f'Работать с ботом очень просто\n'
                         f'отправьте ему фото и следуйте инструкциям.\n'
                         f'Желаю удачи!')



#
#
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
            watermark_line = Image.open('files/gradient_80.png').resize((base_image.size[0], int(base_image.size[1] / 5.5)))
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

            watermark_line = Image.open('files/gradient_80.png').resize((base_image.size[0], int(base_image.size[1] / 7)))
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
            watermark_line = Image.open('files/gradient_80.png').resize((base_image.size[0], int(base_image.size[1] / 5.5)))
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


if __name__ == '__main__':
    dp.run_polling(bot)

# Приходящие callback с сервера
# print(callback.model_dump_json(indent=4, exclude_none=True))
