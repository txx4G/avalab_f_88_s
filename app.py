import os
import sqlite3
from telebot import TeleBot, types
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import logging
import speech_recognition as sr
from langchain_community.tools import DuckDuckGoSearchResults

from db import *
from model_chat_bot import *

# настройки телеграмм-бота
BOT_TOKEN = '7585724889:AAFgjrH1alpJK6HzK99G8KschDM4PIoxMug'
ADMIN_ID = 5849808027
bot = TeleBot(BOT_TOKEN)

# Настройка базы данных
USER_DB_PATH = "businessman.db"
DB_PATH = "qa_database.db"

# Инициализация базы данных
init_db()
init_activity_db()

# Переменные для режимов работы
MODE_MAIN_MENU = 1
MODE_FREQUENT_QUESTIONS = 2
MODE_ASK_QUESTION = 3

MODE_CHAT_BOT = 88

MODE_OPEN_DB = 10

MODE_QUEST_LEVEL = 101
MODE_QUEST_REGION = 102
MODE_QUEST_SPHERE = 103
MODE_QUEST_SUPPORT = 104
MODE_QUEST_NEW = 105
MODE_QUEST_SIZE = 106
MODE_QUEST = 11

MODE_ADMIN_MAIN_MENU = 4
MODE_ADMIN_DOC = 5
MODE_ADMIN_QA = 6

MODE_ADMIN_DEL_DOC = 7

MODE_ADMIN_UPDATE = 8
MODE_ADMIN_STAT = 9

MODE_CONSULTING = 99

MODE_SUP_TYPE = 200

MODE_SUP_FIN = 201
MODE_SUP_NOTFIN = 202
MODE_SUP_NOTFIN = 202
MODE_SUP_INF = 203
MODE_SUP_ADM = 204

MODE_SUP_LEVEL = 300

MODE_SUP_FED = 301
MODE_SUP_REG = 302
MODE_SUP_MUN = 303

MODE_SUP_GOAL = 400

MODE_SUP_NEW = 401
MODE_SUP_DOWN = 402
MODE_SUP_STAB = 403

#текущий режим
current_mode = MODE_MAIN_MENU


#структура информации о бизнесмене
prompt_dict = {
        "stage":"",
        "b2":"",
        "level":"",
        "region":"",
        "sphere":"",
        "size":""
}

#структура необходимых мер поддержки
problem_dict = {
        "type":"",
        "level":"",
        "goal":"",
}



# Переменные для работы
awaiting_question = {}  # Для отслеживания ожидания ввода вопроса пользователем
selected_question = None  # Для хранения выбранного вопроса из списка частых



'''# "Qwen/Qwen2.5-1.5B-Instruct"
#model_name = "models/qa_model"
#qa_pipeline = pipeline("text-generation", model=model_name)
sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
'''
# Логирование
logging.basicConfig(filename="errors.log", level=logging.ERROR)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_command(message):
    """
    Отправляет приветственное сообщение и сохраняет данные пользователя.
    """
    user_id = message.from_user.id
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    save_user_info(user_id,chat_id,username,first_name,last_name)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Поехали")
    bot.send_message(message.chat.id,
    "Добро пожаловать в бизнес-бот! 🤖",
    reply_markup=markup
    )
    help_command(message)

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_command(message):
    """
    Проверяет принятие соглашения и переводит в главное меню, если принято.
    """
    result =  get_agreement_accepted(message.from_user.id)
    bot.send_message(
        message.chat.id,
        "Бизнес-Навигатор AI реализует:\n"
        "1. Поиск мер поддержки для Вашего бизнеса.\n"
        "2. Общение с Чат-ботом по бизнес тематике.\n"
        "3. Поиск организаций, которые могу Вам помочь."
    )
    if result and result[0] == 1:
        show_main_menu(message.chat.id)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Принять", callback_data="accept_agreement"))
        bot.send_message(
            message.chat.id,
            "Для использования бота необходимо принять соглашение на обработку данных.\n"
            "Нажмите 'Принять' для продолжения.",
            reply_markup=markup
        )


# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: call.data == "accept_agreement")
def accept_agreement(call):
    #отметка в БД о соглашении
    set_agreement_accepted(call.from_user.id)
    bot.answer_callback_query(call.id, "Соглашение принято!")
    show_main_menu(call.message.chat.id)

# Функция отображения главного меню
def show_main_menu(chat_id):
    global current_mode
    if chat_id == ADMIN_ID:
        current_mode = MODE_ADMIN_MAIN_MENU
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 Посмотреть статистику", "📫 Работа с ресурсами")
        markup.add("➕ Работа с документами", "🔥 Работа с вопросами")
        markup.add("👥 Работа с пользователями", "👁 Проверить метрики модели")
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)
    else:
        current_mode = MODE_MAIN_MENU
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📝 Пройти анкету")
        markup.add("🆘 Получить программу поддержки", "🤖 Бизнес чат-бот")
        markup.add("🔑 Бизнес-план под ключ", "🔥 Частые вопросы")
        bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

def admin_statistics(message):
    """
    Отправляет статистику по базе данных.
    """
    count, avg_rating = get_statistics()
    bot.send_message(
        message.chat.id,
        f"Статистика базы данных:\n"
        f"Общее количество вопросов: {count}\n"
        f"Средняя оценка пользователей: {avg_rating}"
    )

# Обработка голосового сообщения
def process_voice_message(voice_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(voice_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="ru-RU")
            return text
    except Exception as e:
        logging.error(f"Ошибка обработки голосового сообщения: {e}")
        return None

# Обработка вопросов
'''def process_question(chat_id, question):
    try:
        msg = bot.send_message(chat_id, "Ищу ответ, подождите...")
        answer = qa_pipeline(question)[0]["generated_text"]
        # Сохранение в базу данных
        save_question_to_db(question, answer)
        #bot.delete_message(chat_id=message.chat.id, message_id=msg.message_id)
        bot.delete_message(message.chat.id, msg.message_id)
        bot.send_message(chat_id, f"Ответ:\n{answer}")
        bot.send_message(chat_id, "Оцените ответ от 1 до 4:")
        bot.register_next_step_handler_by_chat_id(chat_id, handle_rating, question, answer)
    except Exception as e:
        logging.error(f"Ошибка обработки вопроса: {e}")
        bot.send_message(chat_id, "Произошла ошибка при обработке вопроса.")
        show_main_menu(chat_id)'''

# Обработка рейтинга ответа
def handle_rating(message, question, answer):
    try:
        rating = int(message.text)
        if 1 <= rating <= 4:
            bot.send_message(message.chat.id, "Спасибо за вашу оценку!")
            set_rating(question,rating)
        else:
            bot.send_message(message.chat.id, "Пожалуйста, введите оценку от 1 до 4.")
            bot.register_next_step_handler(message, handle_rating, question, answer)
            return
    except ValueError:
        #bot.send_message(message.chat.id, "Кнопки убраны. Вы можете продолжать общение.", reply_markup=ReplyKeyboardRemove())
        bot.send_message(message.chat.id, "Введите число от 1 до 4.")
        bot.register_next_step_handler(message, handle_rating, question, answer)

        return
    except Exception as e:
        logging.error(f"Ошибка при сохранении оценки: {e}")

    # Возврат в главное меню
    show_main_menu(message.chat.id)


# Вывод частых вопросов
def show_frequent_questions(chat_id):
    global current_mode
    current_mode = MODE_FREQUENT_QUESTIONS
    try:
        questions = show_top_5()

        if not questions:
            bot.send_message(chat_id, "Нет часто задаваемых вопросов.")
            show_main_menu(chat_id)
        else:
            response = "Часто задаваемые вопросы:\n"
            for idx, (_, question_text) in enumerate(questions, 1):
                response += f"{idx}. {question_text}\n"
            response += "Введите номер вопроса или нажмите 'Назад'."
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Назад")
            bot.send_message(chat_id, response, reply_markup=markup)
    except Exception as e:
        logging.error(f"Ошибка получения частых вопросов: {e}")
        bot.send_message(chat_id, "Произошла ошибка при загрузке частых вопросов.")
        show_main_menu(chat_id)


#атрибуты бизнесмена
stages = ["Хочу открыть бизнес","Хочу развивать бизнес","Хочу расширяться"]
levels = ["Международный","Федеральный","Региональный"]
b2 = ["B2B","B2C","B2G"]
sizes = ["Микро","Малый","Средний","Крупный"]

#атрибуты мер поддержки
types_ch = ["Финансовая","Нефинансовая","Информационная","Административная"]
provids = ["Федеральный","Региональный","Муниципальный"]
goals = ["Развитие новых направлений","Снижение издержек","Устойчивость в кризисных ситуациях"]

types_ch_f = ["Гранты","Субсидии","Льготные кредиты и займы","Налоговые льготы и каникулы"]
types_ch_n = ["Консультации и образовательные программы","Бизнес-акселераторы и инкубаторы","Предоставление льготной инфраструктуры","Поиск инвесторов"]
types_ch_i = ["Доступ к базам данных","Консультации по законодательству","Организация форумов и мероприятий"]
types_ch_a = ["Поцедура регистрации","Лицензирование деятельности"]


# Обработчик сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    global current_mode

    if message.text == "Назад":
        show_main_menu(message.chat.id)
        return

    if current_mode == MODE_MAIN_MENU:

            
        if message.text == "🔑 Бизнес-план под ключ":
            #model_anser= get_user_dialog(prompt_dict, "no q", "business_plan")
            
            bot.send_message(message.chat.id, get_user_dialog(prompt_dict, "no q", "business_plan"))
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Назад")
            bot.send_message(message.chat.id, "Радуйтесь!", reply_markup=markup)
            current_mode = MODE_ADMIN_MAIN_MENU

        elif message.text == "🆘 Получить программу поддержки":
            bot.send_message(message.chat.id, "Чтобы найти необходимые ресурсы по поддержке Вашего бизнеса:")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for ts in types_ch:
                markup.add(ts)
            markup.add("Назад")
            bot.send_message(message.chat.id, "👥 Определим тип поддержки, который Вам необходим:", reply_markup=markup)
            current_mode = MODE_SUP_TYPE



        elif message.text == "🤖 Бизнес чат-бот":
            
            bot.send_message(message.chat.id, "Привет, я Бизнес Чат-Бот (если устали со мной общаться нажмите -Назад-):")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Назад")
            bot.send_message(message.chat.id, "Напишите свой вопрос:", reply_markup=markup)
            current_mode = MODE_CHAT_BOT


        elif message.text == "📝 Пройти анкету":
            bot.send_message(message.chat.id, "Чтобы улучшить наши ответы, пройдите анкету:")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Хочу открыть бизнес")
            markup.add("Хочу развивать бизнес")
            markup.add("Хочу расширять бизнес")
            markup.add("Назад")
            bot.send_message(message.chat.id, "👥 Охарактеризуйте стадию Вашего бизнеса:", reply_markup=markup)
            current_mode = MODE_OPEN_DB

        elif message.text == "🔥 Частые вопросы":
            show_frequent_questions(message.chat.id)
            #current_mode = MODE_FREQUENT_QUESTIONS

    elif current_mode == MODE_SUP_TYPE:

        if message.text == "Финансовая":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for i in types_ch_f:
                markup.add("✅ "+i)
            markup.add("Назад")
            bot.send_message(message.chat.id, "👥 Конкретизируйте:", reply_markup=markup)
            current_mode = MODE_SUP_FIN
        elif message.text == "Нефинансовая":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for i in types_ch_n:
                markup.add("✅ "+i)
            markup.add("Назад")
            bot.send_message(message.chat.id, "👥 Что Вас интересует:", reply_markup=markup)
            current_mode = MODE_SUP_NOTFIN
        elif message.text == "Информационная":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for i in types_ch_i:
                markup.add("✅ "+i)
            markup.add("Назад")
            bot.send_message(message.chat.id, "👥 Что Вас интересует:", reply_markup=markup)
            current_mode = MODE_SUP_INF
        elif message.text == "Административная":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for i in types_ch_a:
                markup.add("✅ "+i)
            markup.add("Назад")
            bot.send_message(message.chat.id, "👥 Что Вас интересует:", reply_markup=markup)
            current_mode = MODE_SUP_ADM

    elif current_mode == MODE_SUP_FIN:
        if message.text in types_ch_f:
            problem_dict["type"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in provids:
            markup.add("✅ "+i)
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 Какого уровня поддержка Вас интересует:", reply_markup=markup)
        current_mode = MODE_SUP_GOAL

    elif current_mode == MODE_SUP_NOTFIN:
        if message.text in types_ch_n:
            problem_dict["type"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in provids:
            markup.add("✅ "+i)
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 Какого уровня поддержка Вас интересует:", reply_markup=markup)
        current_mode = MODE_SUP_GOAL

    elif current_mode == MODE_SUP_ADM:
        if message.text in types_ch_a:
            problem_dict["type"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in provids:
            markup.add("✅ "+i)
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 Какого уровня поддержка Вас интересует:", reply_markup=markup)
        current_mode = MODE_SUP_GOAL

    elif current_mode == MODE_SUP_INF:
        if message.text in types_ch_i:
            problem_dict["type"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for i in provids:
            markup.add("✅ "+i)
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 Какого уровня поддержка Вас интересует:", reply_markup=markup)
        current_mode = MODE_SUP_GOAL


    elif current_mode == MODE_SUP_GOAL:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if message.text in provids:
            problem_dict["level"] = message.text
        for i in goals:
            markup.add("✅ "+i)
        markup.add("Назад")
        bot.send_message(message.chat.id, "🥇 С какой целью:", reply_markup=markup)
        current_mode = MODE_SUP_NEW

    elif current_mode == MODE_SUP_NEW:
        if message.text in goals:
            problem_dict["goal"] = message.text
        
        bot.send_message(message.chat.id, get_user_dialog(prompt_dict, str(problem_dict), "no sense"))
        bot.send_message(message.chat.id, f"❗️ Обратите внимание на следующие ресурсы:")
        search = DuckDuckGoSearchResults(output_format="list")
        prompt_qa = f"{problem_dict['type']} на {problem_dict['level'] } уровне для {problem_dict['goal']}"
        link_list = search.invoke(prompt_qa)
        links = [item['link'] for item in link_list]
        message_str = ""
        for i, link in enumerate(links, start=1):
            message_str += f"{i}. {link}\n"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Назад")
        bot.send_message(message.chat.id, message_str, reply_markup=markup)
        current_mode = MODE_MAIN_MENU

    elif current_mode == MODE_CHAT_BOT:
        model_anser= get_user_dialog(prompt_dict, message.text, "no sense")
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Назад")
        bot.send_message(message.chat.id, model_anser)
        bot.send_message(message.chat.id, "Хорошо, еще вопросы..", reply_markup=markup)

    elif current_mode == MODE_OPEN_DB:
        if message.text in stages:
            prompt_dict["stage"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("B2B")
        markup.add("B2C")
        markup.add("B2G")
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 Формат Вашего бизнеса:", reply_markup=markup)
        current_mode = MODE_QUEST_SIZE

    elif current_mode == MODE_QUEST_SIZE:
        if message.text in b2:
            prompt_dict["b2"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Микро")
        markup.add("Малый")
        markup.add("Средний")
        markup.add("Крупный")
        markup.add("Назад")
        bot.send_message(message.chat.id, "⭐️ Масштаб Вашего бизнеса:", reply_markup=markup)
        current_mode = MODE_QUEST_SUPPORT


    elif current_mode == MODE_QUEST_SUPPORT:
        if message.text in sizes:
            prompt_dict["size"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Международный")
        markup.add("Федеральный")
        markup.add("Региональный")
        markup.add("Назад")
        bot.send_message(message.chat.id, "🌎 Размах Вашего бизнеса:", reply_markup=markup)
        current_mode = MODE_QUEST_REGION


    elif current_mode == MODE_QUEST_REGION:

        if message.text in levels:
            prompt_dict["level"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Пропустить")
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 В каком регионе Ваш бизнес?\n(если неважно нажмите -Пропустить-):", reply_markup=markup)
        current_mode = MODE_QUEST_SPHERE

    elif current_mode == MODE_QUEST_SPHERE:
        if message.text == "Пропустить":
            prompt_dict["region"] = "Россия"
        else:
            prompt_dict["region"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Пропустить")
        markup.add("Назад")
        bot.send_message(message.chat.id, "👥 В какой сфере (отрасли) Ваш бизнес?\n(если неважно нажмите -Пропустить-):", reply_markup=markup)
        current_mode = MODE_QUEST_NEW

    elif current_mode == MODE_QUEST_NEW:
        if message.text == "Пропустить":
            prompt_dict["sphere"] = "Любая"
        else:
            prompt_dict["sphere"] = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("Назад")
        bot.send_message(message.chat.id, f"{ get_user_dialog(prompt_dict, str(prompt_dict), 'no sense')}", reply_markup=markup)
        save_businessman_data(message.chat.id, prompt_dict)
        bot.send_message(message.chat.id, "👥 Спасибо, мы будем учитывать эту информацию при поиске Ваших запросов.", reply_markup=markup)



    elif current_mode == MODE_FREQUENT_QUESTIONS:
        if message.text.isdigit():
            question_number = int(message.text) - 1
            questions = get_questions()

            if 0 <= question_number < len(questions):
                _, answer = questions[question_number]
                bot.send_message(message.chat.id, f"Ответ:\n{answer}")
                show_main_menu(message.chat.id)
            else:
                bot.send_message(message.chat.id, "Неверный номер. Попробуйте снова.")
        else:
            bot.send_message(message.chat.id, "Введите номер вопроса или нажмите 'Назад'.")

    elif current_mode == MODE_ASK_QUESTION:
        bot.send_message(message.chat.id, "Задавайте вопросы только через интерфейс 'Задать вопрос'!")

    elif current_mode == MODE_ADMIN_MAIN_MENU:
        if message.text == "📊 Посмотреть статистику":
            admin_statistics(message)

        elif message.text == "👥 Работа с пользователями":
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Назад")
            bot.send_message(message.chat.id, str(admin_panel_user()), reply_markup=markup)

        elif message.text == "➕ Работа с документами":
            current_mode = MODE_ADMIN_DOC
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("📁 Ознакомиться с базой данных")
            markup.add("📊 Добавить документ")
            markup.add("➕ Удалить документ")
            markup.add("Назад")
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

        elif message.text == "🔥 Работа с вопросами":
            current_mode = MODE_ADMIN_QA
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("📊 Удалить вопрос")
            markup.add("Назад")
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    


    elif current_mode == MODE_ADMIN_DOC:
        if message.text == "📁 Ознакомиться с базой данных":
            files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.pdf')]
            if files:
                numbered_files = "\n".join(f"{i + 1}. {file}" for i, file in enumerate(files))
                bot.send_message(message.chat.id, "Доступные документы:\n" + numbered_files)
            else:
                bot.send_message(message.chat.id, "Документы в папке отсутствуют.")

        elif message.text == "📊 Добавить документ":
            bot.send_message(message.chat.id, "Загрузите документ .pdf.")

        elif message.text == "➕ Удалить документ":
            files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.pdf')]
            if files:
                bot.send_message(message.chat.id, "Доступные документы:\n" + "\n".join(files))

            else:
                bot.send_message(message.chat.id, "Документы в папке отсутствуют.")
                show_main_menu(message.chat.id)
            bot.send_message(message.chat.id, "Выберите номер документа для удаления:")
            current_mode = MODE_ADMIN_DEL_DOC
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add("Назад")
            bot.send_message(message.chat.id, text=None, reply_markup=markup)
    
    elif current_mode == MODE_ADMIN_DEL_DOC:
        if message.text.isdigit():
            question_number = int(message.text)
            delete_pdf_by_number(question_number)# return result str
        




    elif current_mode == MODE_ADMIN_QA:
        pass


@bot.message_handler(content_types=['document'])
def handle_uploaded_document(message):
    """
    Обрабатывает загруженные документы.
    """
    if message.chat.id == ADMIN_ID:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = os.path.join(DATA_FOLDER, message.document.file_name)
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        bot.send_message(message.chat.id, f"Документ {message.document.file_name} успешно сохранён!")
    else:
        bot.send_message(message.chat.id, "Загрузка файлов доступна только администратору.")

# Обработка нового вопроса (текст или голос)
'''@bot.message_handler(content_types=["voice"])
def handle_new_question(message):
        voice_file = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        question = process_voice_message(voice_file)
        if question:
            process_question(message.chat.id, question)
        else:
            bot.send_message(message.chat.id, "Не удалось распознать голосовое сообщение. Попробуйте снова.")
            show_main_menu(message.chat.id)
'''

# Функция для запуска бота с обработкой ошибок
def start_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(5)

if __name__ == "__main__":
    print("now")
    start_bot()