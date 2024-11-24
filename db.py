import sqlite3

USER_DB_PATH = "businessman.db"
DB_PATH = "qa_database.db"

#  информация про пользователя
def init_db():
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businessmen (
            user_id INTEGER PRIMARY KEY,
            chat_id INTEGER,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            stage TEXT,
            b2 TEXT,
            level TEXT,
            region TEXT,
            sphere TEXT,
            size TEXT,
            agreement_accepted INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

    
def save_businessman_data(user_id, prompt_dict):
    """
    Сохраняет данные бизнесмена из словаря в базу данных.
    :param user_id: Идентификатор пользователя.
    :param prompt_dict: Словарь с данными (stage, b2, level, region, sphere, size).
    """
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    # Проверим, существует ли пользователь в базе данных
    cursor.execute("SELECT * FROM businessmen WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is not None:
        # Обновляем данные пользователя
        cursor.execute('''
            UPDATE businessmen
            SET stage = ?, b2 = ?, level = ?, region = ?, sphere = ?, size = ?
            WHERE user_id = ?
        ''', (prompt_dict["stage"], prompt_dict["b2"], prompt_dict["level"],
            prompt_dict["region"], prompt_dict["sphere"], prompt_dict["size"], user_id))
    else:
        # Если пользователя нет в базе, добавляем его
        cursor.execute('''
            INSERT INTO businessmen (user_id, stage, b2, level, region, sphere, size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, prompt_dict["stage"], prompt_dict["b2"], prompt_dict["level"],
            prompt_dict["region"], prompt_dict["sphere"], prompt_dict["size"]))
    
    conn.commit()
    conn.close()

def save_user_info(user_id,chat_id,username,first_name,last_name):
        # Сохраняем пользователя в базе данных, если его еще нет
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businessmen WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO businessmen (user_id, chat_id, username, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
            (user_id, chat_id, username, first_name, last_name)
        )
        conn.commit()
    conn.close()


def get_agreement_accepted(user_id):
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT agreement_accepted FROM businessmen WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def set_agreement_accepted(user_id):
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE businessmen SET agreement_accepted = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def admin_panel_user():
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM businessmen")
    results = cursor.fetchall()
    conn.close()
    return results

def get_statistics():
    """
    Возвращает статистику по частоте вопросов и средней оценке.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        SELECT COUNT(*), AVG(rating)
        FROM Questions
    ''')
    count, avg_rating = cur.fetchone()
    conn.close()
    return count, round(avg_rating, 2) if avg_rating else 0

def show_top_5():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, question_text FROM Questions ORDER BY frequency DESC LIMIT 5")
    result = cursor.fetchall()
    conn.close()
    return result

# Сохранение вопроса в базу данных
def save_question_to_db(question, answer):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Questions (question_text, answer_text, frequency) VALUES (?, ?, ?)",
            (question, answer, 1),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка сохранения вопроса в базу данных: {e}")
def set_rating(question,rating):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
                "INSERT INTO Ratings (question_text, rating) VALUES (?, ?)",
                (question, rating),
                )
    conn.commit()
    conn.close()

# активность пользователя
def init_activity_db():
    """
    Создает таблицу активности пользователей, если она не существует.
    """
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            activity_type TEXT,
            activity_details TEXT,
            FOREIGN KEY(user_id) REFERENCES businessmen(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def log_user_activity(user_id, activity_type, activity_details):
    """
    Записывает активность пользователя в базу данных.
    
    :param user_id: Идентификатор пользователя.
    :param activity_type: Тип активности (например, "вопрос", "рекомендация").
    :param activity_details: Детали активности (например, текст вопроса).
    """
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_activity (user_id, activity_type, activity_details) VALUES (?, ?, ?)",
        (user_id, activity_type, activity_details)
    )
    conn.commit()
    conn.close()

def admin_panel(query_type, user_id=None, activity_type=None):
    """
    Админ-панель для просмотра активности пользователей.

    :param query_type: Тип выборки ("all", "by_user", "by_type").
    :param user_id: Идентификатор пользователя (для выборки по пользователю).
    :param activity_type: Тип активности (для выборки по типу).
    :return: Список записей, соответствующих запросу.
    """
    conn = sqlite3.connect(USER_DB_PATH)
    cursor = conn.cursor()
    
    if query_type == "all":
        cursor.execute("SELECT * FROM user_activity")
    elif query_type == "by_user" and user_id:
        cursor.execute("SELECT * FROM user_activity WHERE user_id = ?", (user_id,))
    elif query_type == "by_type" and activity_type:
        cursor.execute("SELECT * FROM user_activity WHERE activity_type = ?", (activity_type,))
    else:
        conn.close()
        raise ValueError("Некорректный тип запроса или параметры!")
    
    results = cursor.fetchall()
    conn.close()
    return results


def delete_question():
    cur.execute('SELECT id, question_text FROM Questions')
    all_questions = cur.fetchall()

    # Вывод списка вопросов с номерами
    for idx, question in enumerate(all_questions, 1):
        print(f"{idx}. {question[1]}")

    # Запрос номера вопроса для удаления
    question_num = int(input("Введите номер вопроса для удаления: "))

    if 1 <= question_num <= len(all_questions):
        question_id = all_questions[question_num - 1][0]
        cur.execute('DELETE FROM Questions WHERE id = ?', (question_id,))
        conn.commit()
        print("Вопрос успешно удален.")
    else:
        print("Неправильный номер вопроса.")


def get_questions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT question_text, answer_text FROM Questions ORDER BY frequency DESC LIMIT 5")
    questions = cursor.fetchall()
    conn.close()
    return questions

# локальная база документов

def delete_pdf_by_number(file_number):
    folder_path = "data"
    try:
        # Получить список всех PDF-файлов в папке
        pdf_files = [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

        # Убедиться, что список не пуст
        if not pdf_files:
            print("В папке нет PDF-файлов.")
            return

        # Убедиться, что номер файла корректен
        if file_number < 1 or file_number > len(pdf_files):
            print(f"Некорректный номер файла. В папке всего {len(pdf_files)} PDF-файлов.")
            return

        # Получить имя файла и путь к нему
        file_to_delete = pdf_files[file_number - 1]
        file_path = os.path.join(folder_path, file_to_delete)

        # Удалить файл
        os.remove(file_path)
        print(f"Файл '{file_to_delete}' успешно удален.")

    except Exception as e:
        print(f"Ошибка: {e}")