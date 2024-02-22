import logging
from collections import deque
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime, timedelta


logging.basicConfig(level=logging.INFO)
bot = Bot(token="5973966334:AAHjG4FY4yj__zJ0NxXLFkmSVem550Hb238")
dp = Dispatcher(bot)

'''
Структура: 
Subjects - массив предметов
Subject - класс (Название предмета, массив дат с очередями)
QueueInDay - класс очередь в текущий день
Класс очередь - очередь из строк + строка в формате дд.мм.гггг
'''

Subjects = []
interval = 10 #Ограничение частоты записи (в минутах)
regs = {}

db_path = None

def load_from_db():
    global Subjects
    return True

def save_to_db():
    global Subjects
    return False
        
class QueueInDay:
    def __init__(self, date: str):
        self.date = date
        self.queue = deque()
        
    def add(self, name: str)-> bool:
        if name in self.queue:
            return False
        self.queue.append(name)
        return True
        
    def insert(self, name: str, index: int)->bool:  #Вставить в очередь фамилию по индексу
        if name in self.queue:
            return False
        if (index < 0) or (index > len(self.queue)):
            return False
        self.queue.insert(index, name)
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
            s = s + str(i) + ". " + temp.popleft() + '\n'
            i += 1
        return s

    def delete(self, name: str):                  #Удалить человека по фамилии
        if name in self.queue:
            self.queue.remove(name)
            return True
        return False
        
class Subject:

    def __init__(self, name):
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

    def delete(self, DayOfQueue):
        self.ListOfDate.remove(DayOfQueue)

    def print(self):
        s = "".join(self.ListOfDate)
        return s
     
class user_info:                #Пользовательский контекст
    def __init__(self, status, current_subject, current_date, last_reg, surname):
        self.status = status    #Определяет на каком именно месте диалога находится пользователь
        self.current_subject = current_subject
        self.current_date = current_date
        self.last_reg = last_reg  #Время последней регистрации
        self.surname = surname    #Фамилия человека (нужно только для старосты)
        
    def print_data(self):
        print("Status = ", self.status)
        if self.current_subject != None:
            print("Current_subject = ", self.current_subject.name)
        if self.current_date != None:
            print("Current date = ", self.current_date.date)
        print("Last registration = ", self.last_reg)
        print("Surname = ", self.surname)

@dp.message_handler(commands="start")  #Обработчик /start
async def cmd_start(message: types.Message):
    global regs
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True) 
    keyboard.add(types.KeyboardButton("Приступить к работе"))
    keyboard.add(types.KeyboardButton("Что умеет бот?"))
    await message.answer("Добрый день. Нажмите на кнопку, чтобы начать", reply_markup=keyboard)
    id = message.from_user.id
    if id in regs:
        del regs[id]
    regs.update({id: user_info(0, None, None, None, None)})

@dp.message_handler(commands="админ") #Обработчик /админ
async def admin(message: types.Message): 
    global status
    global current_subject
    global current_date
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True) 
    keyboard.add(types.KeyboardButton("Редактировать предмет"))
    keyboard.add(types.KeyboardButton("Добавить предмет"))
    keyboard.add(types.KeyboardButton("Удалить предмет"))
    keyboard.add(types.KeyboardButton("Назад"))
    await message.answer("Добрый день, товарищ администратор", reply_markup=keyboard)  
    id = message.from_user.id
    if id in regs:
        del regs[id]
    regs.update({id: user_info(11, None, None, None, None)}) 

@dp.message_handler() #Обработчик диалога
async def dialog(message: types.Message):
    global regs
    id = message.from_user.id
    if id in regs:
        struct = regs.get(id)
        del regs[id]
    else:
        await message.answer("Напишите ""/start"", чтобы начать диалог")
        return
    
    status = struct.status
    current_subject = struct.current_subject
    current_date = struct.current_date
    last_reg = struct.last_reg
    surname = struct.surname

    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
    one_more = False
    if message.text == "Выйти в главное меню":
        await cmd_start(message)        
    else:
        if status == 0:
            if message.text == "Что умеет бот?":
                await message.answer("Ну тут что то расписать надо жестко", reply_markup=keyboard)
                await cmd_start(message)
            elif message.text == "Приступить к работе":
                for i in Subjects:
                    keyboard.add(types.KeyboardButton(i.name))
                keyboard.add(types.KeyboardButton("Назад"))
                if len(Subjects) > 0:
                    await message.answer("Выберите предмет", reply_markup=keyboard)
                    status = 1
                else:
                    await message.answer("Список предметов пуст")
            elif message.text == "Назад":
                await cmd_start(message)
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки")    
        elif status == 1:
            if message.text == "Назад":
                status = 0
                await cmd_start(message)
            else:
                for temp in Subjects:
                    if temp.name == message.text:
                        current_subject = temp
                if current_subject != None:
                    for temp in current_subject.ListOfDate:
                        keyboard.add(types.KeyboardButton(temp.date))
                    keyboard.add(types.KeyboardButton("Назад"))       
                    if len(current_subject.ListOfDate) > 0:    
                        await message.answer("Выберите дату", reply_markup=keyboard)
                        current_date = None
                        status = 2
                    else:
                        await message.answer("Список дат пуст")
                        status = 0
                        message.text = "Приступить к работе"
                        one_more = True
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
                keyboard.add(types.KeyboardButton("Назад"))
                status = 3
                await message.answer("Выберите, что хотите сделать", reply_markup=keyboard)
            elif message.text == "Назад":
                status = 0
                message.text = "Приступить к работе"
                one_more = True
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)  
        elif status == 3:
            if message.text == "Просмотреть очередь":
                await message.answer("Очередь на " + current_subject.name + " " + current_date.date + ":")
                await message.answer(current_date.get(), reply_markup=keyboard)
                status = 2
                one_more = True 
            elif message.text == "Записаться в очередь":
                current_time = datetime.now()  #Проверка на интервал между регистрациями
                if last_reg == None or (current_time - last_reg >= timedelta(minutes=10)):
                    await message.answer("Ваша фамилия:")
                    status = 4
                else:
                    time_to_wait = timedelta(minutes = 10) + last_reg - current_time
                    await message.answer(f"Вы уже зарегистрировались. Пожалуйста, подождите {time_to_wait.seconds // 60} мин {time_to_wait.seconds % 60} сек.")
                    status = 2
                    one_more = True
            elif message.text == "Назад":
                status = 1
                message.text = current_subject.name
                one_more = True
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
        elif status == 4:
            if current_date.add(message.text):
                last_reg = datetime.now()
            else:
                await message.answer("Ошибка. Человек с таким именем уже есть в очереди")
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
                await message.answer("Данные успешно загружены")
                '''
                Здесь идет подключение к БД

                '''
                status = 10
                one_more = True
            elif message.text == "Редактировать предмет":
                if len(Subjects)>0:
                    for temp in Subjects:
                        keyboard.add(types.KeyboardButton(temp.name))    
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
                if len(Subjects)>0:
                    for temp in Subjects:
                        keyboard.add(types.KeyboardButton(temp.name))    
                    keyboard.add(types.KeyboardButton("Назад"))
                    await message.answer("Выберите предмет", reply_markup=keyboard)
                    status = 31
                else:
                    await message.answer("Список предметов пуст")
                    status = 10
                    one_more = True
            elif message.text == "Сохранить данные":
                await message.answer("Данные успешно сохранены")

                '''
                Подключение к БД и сохранение

                '''

                status = 10
                one_more = True
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки")
                status = 10
                one_more = True          
        elif status == 12:
            if current_subject == None:
                for temp in Subjects:
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
                await message.answer("Вас не понял. Нажимайте на кнопки")
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
            for temp in Subjects:
                if message.text == temp.name:
                    isfound = True
            if isfound:
                await message.answer("Предмет уже существует")
            else:
                temp = Subject(message.text)
                Subjects.append(temp)
                await message.answer("Предмет добавлен")
            status = 10
            one_more = True
        elif status == 31:
            if message.text == "Назад":
                status = 12
                one_more = True       
            exist = False
            for temp in Subjects:
                if message.text == temp.name:
                    Subjects.remove(temp)
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
    struct.last_reg = last_reg
    struct.surname = surname
    struct.print_data()
    regs.update({id: struct})
    if one_more:
        await dialog(message)

if __name__ == "__main__":
    Sub1 = Subject("ОАиП")
    Subjects.append(Sub1)
    TempQueue = QueueInDay("12.12.2012")
    TempQueue.add("Поитов")
    TempQueue.add("Коля")
    TempQueue.add("Хомячим")
    Sub1.add_obj(TempQueue)
    Sub1.add_obj(QueueInDay("16.02.2025"))
    Sub2 = Subject("КПО")
    Subjects.append(Sub2)
    Sub2.add_obj(QueueInDay("13.12.2024"))
    Sub2.add_obj(QueueInDay("15.02.2023"))
    executor.start_polling(dp, skip_updates=True)
