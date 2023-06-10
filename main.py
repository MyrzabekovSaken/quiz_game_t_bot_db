from aiogram import Bot, Dispatcher, types, executor
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
import asyncio
import os


load_dotenv()


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


if not BOT_TOKEN:
    raise ValueError("No BOT token provided")
else:
    print("BOT token is successfully loaded")


logging.basicConfig(level=logging.INFO)


MONGO_URL = os.getenv("MONGO_URL")
MONGODB_DATABASE = "test"
MONGODB_COLLECTION_QUESTIONS = "questions"
MONGODB_COLLECTION_RESULTS = "quiz_result"


client = MongoClient(MONGO_URL)
db = client[MONGODB_DATABASE]
questions_collection = db[MONGODB_COLLECTION_QUESTIONS]
results_collection = db[MONGODB_COLLECTION_RESULTS]

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.reply("Welcome to the quiz game, to start quiz game, use '/quiz")


@dp.message_handler(commands=['quiz'])
async def start_quiz(message: types.Message):
    quiz = list(questions_collection.find())
    score = await run_quiz(quiz, message.chat.id)
    first_name = message.from_user.first_name
    save_results_to_mongodb(first_name, score)
    await message.reply(f"Your score is: {score}")


async def run_quiz(quiz, chat_id):
    score = 0
    for text in quiz:
        question = text["question"]
        options = text["options"]
        answer = text["answer"]
        options_text = "\n".join([f"{key}) {value}" for key, value in options.items()])
        button1 =  types.KeyboardButton("A")
        button2 =  types.KeyboardButton("B")
        button3 =  types.KeyboardButton("C")
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True).row(button1).add(button2).add(button3)    
        message_text = f"{question}\n\n{options_text}"
        await bot.send_message(chat_id, message_text, reply_markup=keyboard)
        user_answer = await get_user_answer(chat_id)
        if user_answer.text.upper() == answer.upper():
            await bot.send_message(chat_id, "Correct answer!")
            score += 1
        else:
            await bot.send_message(chat_id, "Wrong answer!")
    return score

async def get_user_answer(chat_id):
    user_answers = {}
    async def handle_user_answer(message: types.Message):
        user_answers[message.chat.id] = message
    dp.register_message_handler(handle_user_answer, chat_id=chat_id)
    while chat_id not in user_answers:
        await asyncio.sleep(0.5)
    dp.message_handlers.unregister(handle_user_answer)
    return user_answers[chat_id]


def save_results_to_mongodb(first_name, score):
    results_collection.insert_one({"first_name": first_name, "score": score})


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
