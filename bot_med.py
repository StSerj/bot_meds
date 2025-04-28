# Импортируем библиотеку для работы с Telegram ботом
import telebot
# Импортируем модуль для работы с датой и временем (хотя в текущем коде он не используется)
from datetime import datetime


# Создаем и настраиваем бота


from dotenv import load_dotenv
import os
import telebot

load_dotenv()  # Загружает переменные из .env
bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))  # Безопасное получение токена

# Создаем "базы данных" для хранения информации
user_data = {}  # Здесь будем временно хранить данные, пока пользователь их вводит
meds = {}       # Здесь будем хранить все лекарства постоянно

# Текст помощи - список команд, которые понимает бот
HELP = """
/help - Вывести список доступных команд.
/add - добавить лекарство.
/search - найти лекарство.
/update - изменить количество лекарства.
/show - напечатать все лекарства в наличии."""

# Обработчик команды /start - запускается при старте бота
@bot.message_handler(commands=["start"])
def start(message):
    # Создаем клавиатуру с кнопками для удобства
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    # Добавляем кнопки с командами
    markup.add('/add', '/show', '/help', '/search', '/update', '/start')
    # Отправляем сообщение с клавиатурой
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=markup)

# Вспомогательная функция для добавления лекарства в основной список
def add_to_list(chat_id, name, quantity, dose):
    """Функция для добавления в основной словарь"""
    # Если для этого пользователя еще нет списка лекарств - создаем его
    if chat_id not in meds:
        meds[chat_id] = []
    # Добавляем лекарство в список
    meds[chat_id].append({
        'name': name,        # Название
        'quantity': quantity, # Количество
        'dose': dose         # Дозировка
    })

# Обработчик команды /add - начинает процесс добавления лекарства
@bot.message_handler(commands=['add'])
def add_meds(message):
     # Просим ввести название и ждем ответа
     msg = bot.send_message(message.chat.id, "Введите название лекарства")
     # После ответа перейдем к функции name_input
     bot.register_next_step_handler(msg, name_input)

# Функция обработки ввода названия лекарства
def name_input(message):
    try:
        # Получаем идентификатор чата (уникальный номер разговора)
        chat_id = message.chat.id
        # Получаем текст сообщения, убирая пробелы по краям
        name_str = message.text.strip()
        # Проверяем, что название не слишком короткое
        if len(name_str) < 3:
            msg = bot.send_message(chat_id, "❌ Название слишком короткое. Введите еще раз:")
            # Снова ждем ввода названия
            bot.register_next_step_handler(msg, name_input)
            return
        
        # Сохраняем название во временные данные пользователя
        user_data[chat_id] = {'name': name_str.lower()}
        
        # Просим ввести количество и переходим к следующему шагу
        msg = bot.send_message(chat_id, "✏️ Теперь введите количество (упаковок):")
        bot.register_next_step_handler(msg, qty_input)

    # Если что-то пошло не так - сообщаем об ошибке
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# Функция обработки ввода количества
def qty_input(message):
    try:
        chat_id = message.chat.id
        quantity = message.text.strip()
        
        # Проверяем, что введено число
        if not quantity.isdigit():
            msg = bot.send_message(chat_id, "❌ Количество должно быть числом. Введите еще раз:")
            bot.register_next_step_handler(msg, qty_input)
            return
        
        # Сохраняем количество во временные данные
        user_data[chat_id]['quantity'] = quantity
        
        # Просим ввести дозировку и переходим к следующему шагу
        msg = bot.send_message(chat_id, "✏️ Теперь введите дозировку:")
        bot.register_next_step_handler(msg, dose_input)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# Функция обработки ввода дозировки
def dose_input(message):
    try:
        chat_id = message.chat.id
        dose = message.text.strip()
           
        # Проверяем, что дозировка не пустая
        if not dose:
            msg = bot.send_message(chat_id, "❌ Дозировка не может быть пустой. Введите еще раз:")
            bot.register_next_step_handler(msg, dose_input)
            return
        
        # Сохраняем дозировку
        user_data[chat_id]['dose'] = dose
        
        # Достаем сохраненные данные
        name = user_data[chat_id]['name']
        quantity = user_data[chat_id]['quantity']
        
        # Добавляем лекарство в основной список
        add_to_list(chat_id, name, quantity, dose)
        
        # Сообщаем об успешном добавлении
        bot.send_message(chat_id, f"✅ Лекарство '{name}' добавлено в количестве {quantity} уп., в дозировке {dose}.")

        # Очищаем временные данные
        if chat_id in user_data:
            del user_data[chat_id]

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# Обработчик команды /show - показывает лекарства
@bot.message_handler(commands=["show"])  
def show(message):
    # Проверяем, есть ли лекарства у пользователя
    if not meds.get(message.chat.id):  
        bot.send_message(message.chat.id, "Список лекарств пуст")
        return
    
    # Просим ввести название или "все" для полного списка
    msg = bot.send_message(message.chat.id, 
        "Введите название лекарства, или 'все' для полного списка:")
    bot.register_next_step_handler(msg, choose_name)
    
# Функция обработки выбора, что показать
def choose_name(message):
    try:
        chat_id = message.chat.id  
        name_input = message.text.strip().lower()

        # Проверяем, что введено не пустое значение
        if not name_input:
            msg = bot.send_message(chat_id, "❌ Значение не может быть пустым. Введите еще раз:")
            bot.register_next_step_handler(msg, choose_name)
            return
        
        text = ""
        # Если введено "все" - показываем весь список
        if name_input == "все":
            if chat_id in meds:
                for item in meds[chat_id]:
                    text += f"{item['name']} - {item['quantity']} уп., {item['dose']}\n"
            else:
                text = "У вас нет сохраненных лекарств"
        else:
            # Ищем конкретное лекарство
            found = False
            if chat_id in meds:
                for item in meds[chat_id]:
                    if item['name'] == name_input:
                        text = f"{item['name']} - {item['quantity']} уп., {item['dose']}"
                        found = True
                        break
            if not found:
                text = "Лекарство не найдено"
        
        # Отправляем результат
        bot.send_message(chat_id, text if text else "Нет данных для отображения")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Произошла ошибка: {str(e)}")

# Обработчик команды /update - обновляет количество лекарства
@bot.message_handler(commands=['update'])
def update_medication(message):
    msg = bot.send_message(message.chat.id, "Введите название лекарства для изменения:")
    bot.register_next_step_handler(msg, process_update_name)

# Обработка ввода названия для обновления
def process_update_name(message):
    try:
        chat_id = message.chat.id
        target_name = message.text.strip().lower()
        
        # Проверяем, существует ли такое лекарство
        if chat_id not in meds or not any(m['name'] == target_name for m in meds[chat_id]):
            bot.send_message(chat_id, "❌ Лекарство не найдено")
            return
            
        # Просим ввести новое количество
        msg = bot.send_message(chat_id, "Введите новое количество:")
        # Используем lambda-функцию чтобы передать название лекарства дальше
        bot.register_next_step_handler(msg, lambda m: process_update_quantity(m, target_name))
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# Обработка ввода нового количества
def process_update_quantity(message, target_name):
    try:
        chat_id = message.chat.id
        new_quantity = message.text.strip()
        
        # Проверяем, что введено число
        if not new_quantity.isdigit():
            bot.send_message(chat_id, "❌ Количество должно быть числом")
            return
            
        # Находим лекарство и обновляем количество
        for medication in meds[chat_id]:
            if medication['name'] == target_name:
                medication['quantity'] = new_quantity
                bot.send_message(chat_id, f"✅ Количество изменено на {new_quantity}")
                break
                
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {e}")

# Запускаем бота на постоянную работу
bot.polling(none_stop=True)