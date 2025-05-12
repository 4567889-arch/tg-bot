# Импорт необходимых библиотек
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from textblob import TextBlob
import yake

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация роутера
router = Router()

# 🔑 Класс состояний FSM
class AnalysisState(StatesGroup):
    waiting_for_text = State()
    waiting_for_keywords = State()
    waiting_for_wordcount = State()
    waiting_for_style = State()

# Клавиатуры
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Стилистический анализ')],
        [KeyboardButton(text='Лексический анализ')],
        [KeyboardButton(text='О проекте')]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите пункт меню'
)

catalog_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Стиль', callback_data='style')],
        [InlineKeyboardButton(text='Тональность', callback_data='tone')]
    ]
)

keywords_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Ключевые слова', callback_data='keywords')],
        [InlineKeyboardButton(text='Количество слов и читаемость', callback_data='count_words')]
    ]
)

infor_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='О боте', callback_data='about')]
    ]
)

# Команда /start
@router.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer('Привет! Готов помочь с анализом, выбери пункт', reply_markup=main_keyboard)

# Команда /help
@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('вы нажали помощь')

# Стилистический анализ
@router.message(F.text == 'Стилистический анализ')
async def handle_stylistic_analysis(message: Message):
    await message.answer('Выберите:', reply_markup=catalog_keyboard)

@router.callback_query(F.data == 'style')
async def ask_for_style(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте текст для стилистического анализа.")
    await state.set_state(AnalysisState.waiting_for_style)
    await callback.answer()

@router.message(AnalysisState.waiting_for_style)
async def analyze_style(message: Message, state: FSMContext):
    text = message.text.lower()

    conversational_markers = ['я', 'ты', 'мы', 'мне', 'тебе', 'тебя', 'моя', 'твоя', 'наш', 'короче', 'типа', 'вообще', 'чё', 'ладно', 'ага', 'блин', 'кстати', 'жесть', 'давай', 'пошли', 'вот', 'честно', 'правда', 'прикольно', 'ну', 'а', 'такой', 'эта', 'было', 'значит', 'если что', 'вообще-то', 'ну типа', 'ой', 'эх', 'мм', 'ага']
    official_markers = ['данный', 'реализация', 'обеспечение', 'осуществление', 'в соответствии', 'в рамках', 'регламентируется', 'настоящий', 'внедрение', 'предоставление', 'согласно', 'выполнение', 'протокол', 'отчетность', 'нормативный', 'утверждение', 'распоряжение', 'предусмотрено', 'целесообразно', 'направление', 'документация', 'исполнение', 'процедура', 'положения', 'правовое', 'договор', 'требование', 'структура', 'обязательства', 'введение', 'стандарт', 'административный', 'должностное лицо']
    publicistic_markers = ['важно', 'нужно', 'считаем', 'несомненно', 'однако', 'следует отметить', 'безусловно', 'очевидно', 'необходимо', 'представляется', 'на наш взгляд', 'как известно', 'по сути', 'несмотря на', 'общество', 'граждане', 'актуально', 'должны', 'проблема', 'вызов времени', 'на сегодняшний день', 'значительно', 'стоит подчеркнуть', 'в целом', 'целью является', 'особое внимание', 'в современном мире', 'остро стоит вопрос', 'мнение экспертов', 'общественное мнение', 'событие', 'социальный', 'ценности']

    score = {
        'Разговорный': sum(word in text for word in conversational_markers),
        'Официально-деловой': sum(word in text for word in official_markers),
        'Публицистический': sum(word in text for word in publicistic_markers)
    }

    style = max(score, key=score.get)
    explanation = {
        'Разговорный': "Текст содержит личные местоимения, разговорные частицы и неформальные выражения.",
        'Официально-деловой': "Текст использует канцеляризмы, официальную лексику и сложные конструкции.",
        'Публицистический': "Текст содержит оценочные выражения, общественные термины и риторику."
    }

    await message.answer(
        f"\U0001F4D8 Предположительный стиль текста:\n\n"
        f"\U0001F539 {style}\n\n"
        f"\U0001F4CE {explanation[style]}"
    )
    await state.clear()

# Анализ тональности
@router.callback_query(F.data == 'tone')
async def analyze_tone(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте текст для анализа тональности.")
    await state.set_state(AnalysisState.waiting_for_text)
    await callback.answer()

@router.message(AnalysisState.waiting_for_text)
async def analyze_text(message: Message, state: FSMContext):
    blob = TextBlob(message.text)
    polarity = blob.sentiment.polarity
    score = int((polarity + 1) * 50)

    if score >= 60:
        category = "Положительный 😊"
        explanation = "Текст воспринимается как доброжелательный или оптимистичный."
    elif score <= 40:
        category = "Негативный 😕"
        explanation = "Текст содержит выражения с отрицательной окраской."
    else:
        category = "Нейтральный 😐"
        explanation = "Эмоциональная окраска выражена слабо или сбалансирована."

    await message.answer(
        f"\U0001F4CA Анализ тональности:\n\n"
        f"\U0001F539 Оценка: {score}/100\n"
        f"\U0001F539 Категория: {category}\n\n"
        f"\U0001F4CE {explanation}"
    )
    await state.clear()

# Лексический анализ
@router.message(F.text == 'Лексический анализ')
async def handle_lexical_analysis(message: Message):
    await message.answer('Выберите:', reply_markup=keywords_keyboard)

@router.callback_query(F.data == 'keywords')
async def ask_for_keywords(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте текст, чтобы извлечь ключевые слова.")
    await state.set_state(AnalysisState.waiting_for_keywords)
    await callback.answer()

@router.message(AnalysisState.waiting_for_keywords)
async def extract_keywords(message: Message, state: FSMContext):
    text = message.text
    kw_extractor = yake.KeywordExtractor(lan="ru", n=2, top=10)
    keywords = kw_extractor.extract_keywords(text)

    if keywords:
        keyword_list = "\n".join(f"• {kw}" for kw, _ in keywords)
        await message.answer(f"\U0001F511 Ключевые слова:\n\n{keyword_list}")
    else:
        await message.answer("Не удалось извлечь ключевые слова. Попробуйте другой текст.")

    await state.clear()

@router.callback_query(F.data == 'count_words')
async def ask_for_wordcount(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте текст, чтобы посчитать количество слов.")
    await state.set_state(AnalysisState.waiting_for_wordcount)
    await callback.answer()

@router.message(AnalysisState.waiting_for_wordcount)
async def count_words(message: Message, state: FSMContext):
    text = message.text
    words = text.split()
    word_count = len(words)
    char_count = len(text.replace(" ", ""))
    avg_word_len = (char_count / word_count) if word_count > 0 else 0

    long_words = [w for w in words if len(w) >= 8]
    long_word_count = len(long_words)
    percent_long = (long_word_count / word_count * 100) if word_count > 0 else 0

    if avg_word_len < 4:
        level = "\U0001F4DA Начальный\n\U0001F4CE Рекомендуется для начальной школы."
    elif avg_word_len < 5:
        level = "\U0001F3EB Школьный\n\U0001F4CE Подходит для школьной аудитории."
    elif avg_word_len < 6:
        level = "\U0001F393 Университет\n\U0001F4CE Хорошо читается взрослыми."
    else:
        level = "\U0001F9E0 Продвинутый\n\U0001F4CE Текст сложный — возможно, стоит упростить."

    await message.answer(
        f"\U0001F4D8 Статистика текста:\n\n"
        f"\U0001F539 Слов: {word_count}\n"
        f"\U0001F4CA Длинных слов (8+ символов): {long_word_count} ({percent_long:.1f}%)\n"
        f"\U0001F4CF Средняя длина слова: {avg_word_len:.2f}\n\n"
        f"\U0001F4C8 Уровень читаемости: {level}"
    )
    await state.clear()

# О проекте
@router.message(F.text == 'О проекте')
async def handle_about_project(message: Message):
    await message.answer('раздел о боте', reply_markup=infor_keyboard)

@router.callback_query(F.data == 'about')
async def about(callback: CallbackQuery):
    await callback.answer('Что это такое?', show_alert=True)
    await callback.message.answer('Бот создан лингвистами ИМОиВ, впервые занимающимися разработкой на Python.')

# Обработка прочих сообщений
@router.message()
async def echo(message: Message):
    await message.answer(message.text)
    await message.reply('Будем работать? Выбери нужный пункт')

# Основной запуск бота
async def main():
    # Получение токена бота из переменных окружения
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("Не указан токен бота в .env файле")
    
    bot = Bot(token=BOT_TOKEN) 
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

# Запуск при старте скрипта
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')
