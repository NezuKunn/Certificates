from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import asyncio
import logging
from PIL import Image, ImageDraw, ImageFont
import random

from config import token

class HelperStates(StatesGroup):
    question = State()



class MyBot:
    def __init__(self, token):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        )
        logger = logging.getLogger(__name__)
        logger.error("Starting bot")

        self.numbers = []
        self.tg_ids = []

        self.bot = Bot(token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        self.register_handlers()
        asyncio.gather(self.set_commands())

    
    def make_sert(self, fio, number):
        image = Image.open("сертификат.jpg")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype("arial.ttf", size=100)

        text = f'Данный сертификат подтверждает, что \n{fio}\nуспешно завершил(а) курс "Математика для занятых"\nи может нести эти знания людям,\nвнося вклад в развитие общества.'
        lines = text.split('\n')

        image_width, image_height = image.size
        y_start = 1000
        text_color = (0, 0, 0)
        y = y_start

        for line in lines:
            text_bbox = draw.textbbox((0, 0), line, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (image_width - text_width) / 2
            draw.text((x, y), line, fill=text_color, font=font)
            y += text_height + 80

        num_font = ImageFont.truetype("arial.ttf", size=80)
        num_text = f"Номер сертификата: {number}"
        draw.text((250, image_height - 330), num_text, fill=text_color, font=num_font)

        image.save(f"results/sert_{number}.jpg", "JPEG")

    async def send_welcome(self, message: types.Message, state: FSMContext):
        await self.bot.delete_message(
            message.chat.id,
            message.message_id
        )

        if message.from_user.id in self.tg_ids:
            await self.bot.send_message(
                chat_id=message.chat.id,
                text="Вы уже забрали свой сертификат.",
                parse_mode=types.ParseMode.MARKDOWN,
            )
            await state.set_state(None)
            return
        
        window = await self.bot.send_message(
            chat_id=message.chat.id,
            text="Здравствуй! Введи своё *ФИО* для получения персонального сертификата.\n\n*Внимание!* Сертификат можно получить только один раз!",
            parse_mode=types.ParseMode.MARKDOWN,
        )
        await state.update_data(window=window)
        await HelperStates.question.set()
        return

    async def question(self, message: types.Message, state: FSMContext):
        data = await state.get_data()

        fio = message.text
        number = random.randint(10**12, 10**13 - 1)
        
        while number in self.numbers:
            number = random.randint(10**12, 10**13 - 1)

        self.numbers.append(number)
        self.tg_ids.append(message.from_user.id)
        self.make_sert(fio=fio, number=number)

        await self.bot.delete_message(
            message.chat.id,
            message.message_id
        )

        await self.bot.delete_message(
            message.chat.id,
            data["window"].message_id
        )

        with open(f"results/sert_{number}.jpg", 'rb') as photo:
            await self.bot.send_photo(
                chat_id=message.chat.id,
                photo=photo,
                caption=f"Вот Ваш сертификат, {fio}. Поздравляем!", 
                parse_mode=types.ParseMode.MARKDOWN
            )
        
        await state.set_state(None)
        return

    async def set_commands(self):
        commands = [
            types.BotCommand(command="/start", description="Start Bot")
        ]
        await self.bot.set_my_commands(commands)

    def register_handlers(self):
        self.dp.register_message_handler(self.send_welcome, commands=['start'])
        self.dp.register_message_handler(self.question, state=HelperStates.question)


bot = MyBot(token)
executor.start_polling(bot.dp, skip_updates=True)