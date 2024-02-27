import logging
from collections import deque
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from datetime import datetime
import sqlite3

logging.basicConfig(level=logging.INFO)
bot = Bot(token="5973966334:AAHjG4FY4yj__zJ0NxXLFkmSVem550Hb238")
dp = Dispatcher(bot)

'''
Структура: 
subjects - массив предметов
Subject - класс (Название предмета, массив дат с очередями)
QueueInDay - класс очередь в текущий день
Класс очередь - очередь из строк + строка в формате дд.мм.гггг
'''

subjects = []
users = {}
admins = []
regs = {}
surname = None

def load_from_db():
    global subjects
    global users

    conn = sqlite3.connect('data.db')

    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM subjects')
        temp_subjects = cursor.fetchall()
        cursor.execute('SELECT * FROM dates')
        temp_dates = cursor.fetchall()
        cursor.execute('SELECT * FROM people')
        temp_people = cursor.fetchall()
        cursor.execute('SELECT * FROM users')
        temp_users = cursor.fetchall()
    except:
        return False
    conn.close()

    print(temp_subjects)
    print(temp_dates)
    print(temp_people)
    print(temp_users)

    subjects.clear()

    users = dict(temp_users)

    for temp in temp_subjects:
        sub_ind, name = temp
        subjects.append(Subject(name))

    for temp in temp_dates:
        sub_ind, date_ind, date = temp
        subjects[sub_ind].add_obj(QueueInDay(date))

    for temp in temp_people:
        sub_ind, date_ind, person_id, name = temp
        try:
            subjects[sub_ind].ListOfDate[date_ind].add((person_id, name))
        except:
            print(sub_ind, date_ind, person_id, name)
    return True

def save_to_db():
    global subjects
    global users
    
    to_save_subjects = []
    to_save_dates = []
    to_save_people = []
    sub_ind = 0

    to_save_users = list(users.items())

    for sub in subjects:

        to_save_subjects.append((sub_ind, sub.name))
        date_ind = 0  

        for date in sub.ListOfDate:

            to_save_dates.append((sub_ind, date_ind, date.date))
            tqueue = date.queue.copy()

            while len(tqueue) > 0:
                elem = tqueue.popleft()
                to_save_people.append((sub_ind, date_ind, elem[0], elem[1]))

            date_ind += 1
        
        sub_ind += 1

    print(to_save_subjects)
    print(to_save_dates)
    print(to_save_users)
    print(to_save_people)

    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS subjects')
    cursor.execute('DROP TABLE IF EXISTS dates')
    cursor.execute('DROP TABLE IF EXISTS people')
    cursor.execute('DROP TABLE IF EXISTS users')

    cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
                   subject_id INTEGER PRIMARY KEY,
                   subject_name TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS dates (
                    subject_id INTEGER,
                    date_id INTEGER,
                    date_value TEXT,
                    FOREIGN KEY(subject_id) REFERENCES subjects(subject_id))''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                   person_id INTEGER PRIMARY KEY,
                   person_name TEXT)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS people (
                    subject_id INTEGER,
                    date_id INTEGER,
                    person_id INTEGER,
                    person_name TEXT,
                    FOREIGN KEY(person_id) REFERENCES users(person_id)
                    FOREIGN KEY(subject_id) REFERENCES subjects(subject_id))''')
    
    cursor.executemany('INSERT INTO subjects VALUES (?, ?)', to_save_subjects)
    cursor.executemany('INSERT INTO dates VALUES (?, ?, ?)', to_save_dates)
    cursor.executemany('INSERT INTO users VALUES (?, ?)', to_save_users)
    cursor.executemany('INSERT INTO people VALUES (?, ?, ?, ?)', to_save_people)
    conn.commit()
    conn.close()
        
class QueueInDay:
    def __init__(self, date: str):
        self.date = date
        self.queue = deque()
        
    def add(self, to_add):
        if to_add in self.queue:
            return False
        self.queue.append(to_add)
        return True
        
    def insert(self, name: str, index: int):  #Вставить в очередь фамилию по индексу
        for elem in self.queue:
            if elem[1] == name:
                return False
        to_add = (0, name)
        if (index < 0) or (index > len(self.queue)):
            return False
        self.queue.insert(index, to_add)
        return True
    
    def popn(self, n: int):                         #Удалить первых n людей
        if (n <= 0) or (n >= len(self.queue)):
            return False
        for _ in range(n):
            self.queue.popleft()
        return True

    def isEmpty(self):
        return len(self.queue) == 0

    def get(self):  #Получить строку с фимилиями и порядковым номером в очереди
        if self.isEmpty():
            return "Очередь пуста"
        temp = self.queue.copy()
        i = 1
        s = ""
        while len(temp) > 0:
            surname = temp.popleft()[1]
            s += f"{i}. {surname}\n"
            i += 1
        return s

    def delete(self, name: str):                  #Удалить человека по фамилии
        for elem in self.queue:
            if elem[1] == name:
                self.queue.remove(elem)
                return True
        return False
    
    def del_obj(self, to_del):
        if not to_del in self.queue:
            return False
        self.queue.remove(to_del)
        return True
        
class Subject:

    def __init__(self, name: str):
        self.name = name
        self.ListOfDate = []

    def add_obj(self, to_add: QueueInDay):        #Добавить объект QueueInDay
        temp = to_add.date
        for elem in self.ListOfDate:
            if elem.date == temp:
                return False
        self.ListOfDate.append(to_add)
        return True 

    def add_str(self, to_add: str):              #Создать объект QueueInDay и добавить его
        try:
            datetime.strptime(to_add, "%d.%m.%Y")
        except ValueError:
            return False
        for elem in self.ListOfDate:
            if elem.date == to_add:
                return False
        self.ListOfDate.append(QueueInDay(to_add))
        self.ListOfDate = sorted(self.ListOfDate, key=lambda x: datetime.strptime(x.date, "%d.%m.%Y"))
        return True

    def delete(self, day: QueueInDay):
        if day in self.ListOfDate:
            self.ListOfDate.remove(day)
            return True
        return False
     
class user_info:                #Пользовательский контекст
    def __init__(self, status, current_subject, current_date):
        self.status = status    #Определяет на каком именно месте диалога находится пользователь
        self.current_subject = current_subject
        self.current_date = current_date

@dp.message_handler(commands="start")  #Обработчик /start
async def cmd_start(message: types.Message):
    global regs
    global users
    
    id = message.from_user.id
    if id in regs:
        del regs[id]
    if id in users:
        status = 0
    else:
        status = -1
    regs.update({id: user_info(status, None, None)})
     
    if status == -1:
        await message.answer("Представьтесь, пожалуйста (Фамилия Имя):")
    else:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(types.KeyboardButton("Приступить к работе"))
        keyboard.add(types.KeyboardButton("Что умеет бот?"))
        await message.answer("Нажмите на кнопку, чтобы начать", reply_markup=keyboard)

@dp.message_handler(commands="админ") #Обработчик /админ
async def admin(message: types.Message): 
    id = message.from_user.id
    if id in admins: 
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True) 
        keyboard.add(types.KeyboardButton("Загрузить данные"))
        keyboard.add(types.KeyboardButton("Редактировать предмет"))
        keyboard.add(types.KeyboardButton("Добавить предмет"))
        keyboard.add(types.KeyboardButton("Удалить предмет"))
        keyboard.add(types.KeyboardButton("Сохранить данные"))
        await message.answer("Добрый день, товарищ администратор", reply_markup=keyboard)  
        if id in regs:
            del regs[id]
        regs.update({id: user_info(11, None, None)}) 
    else:
        await message.answer("Вы не администратор. Напишите /start, чтобы начать")

@dp.message_handler() #Обработчик диалога
async def dialog(message: types.Message):
    global regs
    global users
    global surname

    id = message.from_user.id
    if id in regs:
        struct = regs.get(id)
        del regs[id]
    else:
        await message.answer("Напишите /start, чтобы начать диалог")
        return
    
    status = struct.status
    current_subject = struct.current_subject
    current_date = struct.current_date

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    one_more = False

    if status == -1:
        users.update({id: message.text})
        await message.answer("Регистрация прошла успешно")
        await cmd_start(message)
        return
    elif status == 0:
        if message.text == "Что умеет бот?":
            try:
                with open("rules.txt", "r", encoding="utf-8") as file:
                    rules_text = file.read()
            except:
                rules_text = "Ошибка открытия файла с правилами. Правил нет - делайте что хотите"
            await message.answer(rules_text)
        elif message.text == "Приступить к работе":
            if len(subjects) > 0:
                for subject in subjects:
                    keyboard.add(types.KeyboardButton(subject.name))
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Выберите предмет", reply_markup=keyboard)
                status = 1
            else:
                await message.answer("Список предметов пуст")
        elif message.text != "Назад":
            await message.answer("Вас не понял. Нажимайте на кнопки")  
        if status != 1:
            await cmd_start(message)
            return
    elif status == 1:
        if message.text == "Назад":
            current_subject = None
            current_date = None
            await cmd_start(message)
            return
        else:
            if current_subject == None:
                for temp in subjects:
                    if temp.name == message.text:
                        current_subject = temp
            if current_subject != None:      
                if len(current_subject.ListOfDate) > 0: 
                    for temp in current_subject.ListOfDate:
                        keyboard.add(types.KeyboardButton(temp.date))
                    keyboard.add(types.KeyboardButton("Назад"))    
                    await message.answer("Выберите дату", reply_markup=keyboard)
                    current_date = None
                    status = 2
                else:
                    await message.answer("Список дат пуст")    
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
                status = 0
                message.text = "Приступить к работе"
                one_more = True
    elif status == 2:
        if current_date == None:
            for temp in current_subject.ListOfDate:
                if temp.date == message.text:
                    current_date = temp
        if current_date != None:
            keyboard.add(types.KeyboardButton("Просмотреть очередь"))
            keyboard.add(types.KeyboardButton("Записаться в очередь"))
            keyboard.add(types.KeyboardButton("Выписаться из очереди"))
            keyboard.add(types.KeyboardButton("Назад"))
            status = 3
            await message.answer("Выберите, что хотите сделать", reply_markup=keyboard)
        elif message.text == "Назад":
            status = 0
            message.text = "Приступить к работе"
            one_more = True
            current_subject = None
        else:
            await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)  
            status = 1
            one_more = True
    elif status == 3:
        if message.text == "Назад":
            message.text=""
            status = 1
            current_date = None
        else:
            if message.text == "Просмотреть очередь":
                await message.answer(f"Очередь на {current_subject.name}  {current_date.date}:")
                await message.answer(current_date.get())
            elif message.text == "Записаться в очередь":
                if current_date.add((id, users.get(id))):
                    await message.answer("Добавлены в очередь успешно")
                else:
                    await message.answer("Ошибка: вы уже записаны")                  
            elif message.text == "Выписаться из очереди":
                if current_date.del_obj((id, users.get(id))):
                    await message.answer("Вы удалены успешно")
                else:
                    await message.answer("Ошибка: вы не были записаны")
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
            status = 2
        one_more = True
    elif status == 10:
        keyboard.add(types.KeyboardButton("Загрузить данные"))
        keyboard.add(types.KeyboardButton("Добавить предмет"))
        keyboard.add(types.KeyboardButton("Редактировать предмет"))
        keyboard.add(types.KeyboardButton("Удалить предмет"))
        keyboard.add(types.KeyboardButton("Сохранить данные"))
        await message.answer("Выберите пункт меню:", reply_markup=keyboard)   
        status = 11
    elif status == 11:
        if message.text == "Загрузить данные":
            if load_from_db():
                await message.answer("Данные успешно загружены")
            else:
                await message.answer("Ошибка загрузки данных")
            status = 10
            one_more = True
        elif message.text == "Редактировать предмет":
            if len(subjects)>0:
                for temp in subjects:
                    keyboard.add(types.KeyboardButton(temp.name))
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Выберите предмет:", reply_markup=keyboard)
                status = 12
            else:
                await message.answer("Список предметов пуст")
                status = 10
                one_more = True
        elif message.text == "Добавить предмет":
            await message.answer("Введите название предмета:")    
            status = 30
        elif message.text == "Удалить предмет":
            if len(subjects)>0:
                for temp in subjects:
                    keyboard.add(types.KeyboardButton(temp.name))    
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Выберите предмет", reply_markup=keyboard)
                status = 31
            else:
                await message.answer("Список предметов пуст")
                status = 10
                one_more = True
        elif message.text == "Сохранить данные":
            save_to_db()
            await message.answer("Данные успешно сохранены")
            status = 10
            one_more = True
        else:
            await message.answer("Вас не понял. Нажимайте на кнопки")
            status = 10
            one_more = True          
    elif status == 12:
        if message.text == "Назад":
            status = 10
            one_more = True
        else:
            if current_subject == None:
                for temp in subjects:
                    if temp.name == message.text:
                        current_subject = temp
            if current_subject != None:
                keyboard.add(types.KeyboardButton("Добавить дату"))
                keyboard.add(types.KeyboardButton("Редактировать дату"))
                keyboard.add(types.KeyboardButton("Удалить дату"))
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Выберите пункт меню:", reply_markup=keyboard)
                status = 13
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
    elif status == 13:
        if message.text == "Добавить дату":
            await message.answer("Введите дату (дд.мм.гггг):")
            status = 14
        elif message.text == "Редактировать дату":
            status = 15
            one_more = True
        elif message.text == "Удалить дату":
            status = 28
            one_more = True
        elif message.text == "Назад":
            status = 10
            current_subject = None
            one_more = True
        else:
            await message.answer("Вас не понял. Нажимайте на кнопки")
            status = 12
    elif status == 14:
        if current_subject.add_str(message.text):
            await message.answer("Дата успешно добавлена")
        else:
            await message.answer("Ошибка ввода либо дата была добавлена ранее")
        status = 12
        one_more = True
    elif status == 15:
        if len(current_subject.ListOfDate) > 0: 
            for temp in current_subject.ListOfDate:
                keyboard.add(types.KeyboardButton(temp.date))
            keyboard.add(types.KeyboardButton("Назад"))
            await message.answer("Выберите дату для редактирования", reply_markup=keyboard)
            status = 16
        else:
            await message.answer("Список дат пуст")
            status = 12
            one_more = True
    elif status == 16:
        if message.text == "Назад":
            message.text = ""
            one_more = True
            status = 12
        else:
            for temp in current_subject.ListOfDate:
                if temp.date == message.text:
                    current_date = temp
            if current_date != None:
                keyboard.add(types.KeyboardButton("Вставить"))
                keyboard.add(types.KeyboardButton("Удалить по фамилии"))
                keyboard.add(types.KeyboardButton("Удалить первые n людей"))
                keyboard.add(types.KeyboardButton("Назад"))
                status = 17
                await message.answer("Выберите, что хотите сделать", reply_markup=keyboard)
            else:
                await message.answer("Дата не найдена", reply_markup=keyboard)
                message.text = ""
                one_more = True
                status = 12 
    elif status == 17:
        if message.text == "Назад":
            current_date = None
            status = 12
            one_more = True
        elif message.text == "Вставить":
            await message.answer("Введите фамилию:")
            status = 18
        elif message.text == "Удалить по фамилии":
            await message.answer("Введите фамилию:")
            status = 20
        elif message.text == "Удалить первые n людей":
            await message.answer("Введите n:")
            status = 21
        else:
            await message.answer("Вас не понял. Нажимайте на кнопки")
    elif status == 18:
        surname = message.text
        await message.answer("Введите номер для вставки")
        status = 19
    elif status == 19:
        status = 16
        one_more = True
        try:
            n = int(message.text)
        except:
            await message.answer("Ошибка. Введите число")
            return
        if current_date.insert(surname, n-1):
            await message.answer("Человек вставлен успешно")
        else:
            await message.answer("Неверный индекс или человек уже в очереди")
    elif status == 20:
        surname = message.text
        if current_date.delete(surname):
            await message.answer("Человек удален")
        else:
            await message.answer("Ошибка. Человек не найден")
        status = 16
        one_more = True
    elif status == 21:
        status = 16
        try:
            n = int(message.text)
        except:
            await message.answer("Ошибка. Введите число")
            one_more = True
            return
        if current_date.popn(n):
            await message.answer(f"Первые {n} человек успешно удалены")
        else:
            await message.answer("Ошибка: неверное количество")
    elif status == 28:
        if len(current_subject.ListOfDate) > 0:
            for temp in current_subject.ListOfDate:
                keyboard.add(types.KeyboardButton(temp.date))
            keyboard.add(types.KeyboardButton("Назад"))
            await message.answer("Выберите дату для удаления", reply_markup=keyboard)
            status = 29
        else:
            await message.answer("Список дат пуст")
            status = 12
            one_more = True
    elif status == 29:
        if message.text != "Назад":
            current_date == None
            for temp in current_subject.ListOfDate:
                if temp.date == message.text:
                    current_date = temp
            if current_date == None:
                await message.answer("Дата не найдена")
            else:
                current_subject.ListOfDate.remove(current_date)
                await message.answer("Дата успешно удалена")
        status = 12
        one_more = True
    elif status == 30:
        isfound = False
        for temp in subjects:
            if message.text == temp.name:
                isfound = True
        if isfound:
            await message.answer("Предмет уже существует")
        else:
            temp = Subject(message.text)
            subjects.append(temp)
            await message.answer("Предмет добавлен")
        status = 10
        one_more = True
    elif status == 31:
        if message.text == "Назад":
            status = 12
        else:
            exist = False
            for temp in subjects:
                if message.text == temp.name:
                    subjects.remove(temp)
                    exist = True
            if exist:
                await message.answer("Предмет удалён")
            else:
                await message.answer("Предмет не найден")
            status = 10
        one_more = True   

    struct.status = status
    struct.current_subject = current_subject
    struct.current_date = current_date
    regs.update({id: struct})
    if one_more:
        await dialog(message)

admins = [681262766, 861344257]
executor.start_polling(dp, skip_updates=True)
