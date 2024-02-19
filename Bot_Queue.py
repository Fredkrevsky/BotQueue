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


'''

status = 0
current_subject = None  
current_date = None
Subjects = []
interval = 10 #Ограничение частоты записи (в минутах)
lastRegistration = None #Время последней регистрации
        
class QueueInDay:
    def __init__(self, date):
        self.date = date
        self.queue = deque()
        
    def add(self, name):
        if name in self.queue:
            return False
        else:
            self.queue.append(name)
            return True

    def isEmpty(self):
        return len(self.queue) == 0

    def get(self):  #Получить строку с фимилиями и порядковым номером в очереди
        s = ''
        temp = self.queue.copy()
        if self.isEmpty():
            s = "Очередь пуста"
        else:
            i = 1
            while (len(self.queue) > 0):
                s = s + str(i) + ". " + self.queue.popleft() + '\n'
                i += 1
            self.queue = temp
        return s

    def delete(self, Name):
        return self.queue.remove(Name)
        
class Subject:

    def __init__(self, name):
        self.name = name
        self.ListOfDate = []

    def add(self, DayOfQueue):
        if not (DayOfQueue in self.ListOfDate):
            self.ListOfDate.append(DayOfQueue)
            self.sort()

    def delete(self, DayOfQueue):
        self.ListOfDate.remove(DayOfQueue)

    def print(self):
        s = "".join(self.ListOfDate)
        return s

    def sort(self):
        self.ListOfDate = sorted(self.ListOfDate, key=lambda x: datetime.strptime(x.date, "%d.%m.%Y")) #Сортируем очереди внутри предмета по дате
     
@dp.message_handler(commands="start")  #Обработчик /start
async def cmd_start(message: types.Message):
    global status
    global current_subject
    global current_date
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True) 
    keyboard.add(types.KeyboardButton("Приступить к работе"))
    keyboard.add(types.KeyboardButton("Что умеет бот?"))
    await message.answer("Добрый день. Нажмите на кнопку, чтобы начать", reply_markup=keyboard)
    status = 0
    current_subject = None
    current_date = None

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
    status = 11
    current_subject = None
    current_date = None

@dp.message_handler() #Обработчик диалога
async def dialog(message: types.Message):
    global status
    global current_subject
    global current_date
    global lastRegistration
    #Кнопка "Назад" уменьшает статус на 2 (но это не всегда)
    keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)

    print("message =", message.text, "status =", status)
    if (current_subject):
        print(current_subject.name)
    if (current_date):
        print(current_date.date)
    if message.text == "Выйти в главное меню":
        await cmd_start(message)        
    else:
        if status == 0:
            if message.text == "Что умеет бот?":
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Ну тут что то расписать надо жестко", reply_markup=keyboard)
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
                        await dialog(message)
                else:
                    await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
                    status = 0
                    message.text = "Приступить к работе"
                    await dialog(message)
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
                await dialog(message)
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)  
        elif status == 3:
            if message.text == "Просмотреть очередь":
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Очередь на " + current_subject.name + " " + current_date.date + ":")
                await message.answer(current_date.get(), reply_markup=keyboard)
            elif message.text == "Записаться в очередь":
                current_time = datetime.now()  #Проверка на интервал между регистрациями
                if lastRegistration == None or (current_time - lastRegistration >= timedelta(minutes=10)):
                    await message.answer("Ваша фамилия:")
                    status = 4
                else:
                    time_to_wait = timedelta(minutes = 10) + lastRegistration - current_time
                    await message.answer(f"Вы уже зарегистрировались. Пожалуйста, подождите {time_to_wait.seconds // 60} мин {time_to_wait.seconds % 60} сек.")

                
            elif message.text == "Назад":
                status = 1
                message.text = current_subject.name
                await dialog(message)
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
        elif status == 4:
            if message.text.find("\n") > 0:
                await message.answer("Нельзя записывать более одного человека за раз")
            else:
                if current_date.add(message.text.capitalize()):
                    lastRegistration = datetime.now()
                else:
                    await message.answer("Ошибка. Человек с таким именем уже есть в очереди")
            status = 2
            await dialog(message)

        elif status == 10:
            keyboard.add(types.KeyboardButton("Добавить предмет"))
            keyboard.add(types.KeyboardButton("Редактировать предмет"))
            keyboard.add(types.KeyboardButton("Удалить предмет"))
            keyboard.add(types.KeyboardButton("Назад"))
            await message.answer("Выберите пункт меню:", reply_markup=keyboard)   
            status = 11
        elif status == 11:
            if message.text == "Редактировать предмет":
                if len(Subjects)>0:
                    for temp in Subjects:
                        keyboard.add(types.KeyboardButton(temp.name))    
                    await message.answer("Выберите предмет:", reply_markup=keyboard)
                    status = 12
                else:
                    await message.answer("Список предметов пуст")
                    status = 10
                    await dialog(message)
            elif message.text == "Добавить предмет":
                await message.answer("Введите название предмета:")    
                status = 20
            elif message.text == "Удалить предмет":
                if len(Subjects)>0:
                    for temp in Subjects:
                        keyboard.add(types.KeyboardButton(temp.name))    
                    await message.answer("Выберите предмет", reply_markup=keyboard)
                    status = 21
                else:
                    await message.answer("Список предметов пуст")
                    status = 10
                    await dialog(message)
            elif message.text == "Назад":
                status = 0
                await cmd_start(message)
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки")
                status = 10
                await dialog(message)          
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
                status = 13
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки")
        elif status == 13:
            if message.text == "Добавить дату":
                await message.answer("Введите дату (дд.мм.гггг):")
                status = 14
            elif message.text == "Редактировать дату":
                status = 15
            elif message.text == "Удалить дату":
                status = 18
            elif message.text == "Назад":
                status = 10
                current_subject = None
                await dialog(message)
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки")
                status = 12

        elif status == 14:
            isCorrect = True
            try:
                datetime.strptime(message.text, "%d.%m.%Y")
            except ValueError:
                isCorrect = False
            if isCorrect:
                current_subject.add(message.text)
                await message.answer("Дата успешно добавлена")
            else:
                await message.answer("Неверный формат ввода")
            status = 12
        elif status == 15:
            for temp in current_subject.ListOfDate:
                keyboard.append(types.KeyboardButton(temp.date))
            keyboard.append(types.KeyboardButton("Назад"))

        elif status == 18:
            if len(current_subject.ListOfDate) > 0:
                await message.answer("Выберите дату для удаления")
                for temp in current_subject.ListOfDate:
                    keyboard.add(types.KeyboardButton(temp.date))
                keyboard.add(types.KeyboardButton("Назад"))
                status = 19
            else:
                await message.answer("Список дат пуст")
                status = 12
        elif status == 19:
            for temp in current_subject.ListOfDate:
                if temp.date == message.text:
                    current_date = temp
            if current_date == None:
                await message.answer("Дата не найдена")
            else:
                current_subject.ListOfDate.remove(current_date)
                await message.answer("Дата успешно удалена")
            status = 12
        elif status == 20:
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
            await dialog(message)
        elif status == 21:
            exsit = False
            for temp in Subjects:
                if message.text == temp.name:
                    Subjects.remove(temp)
                    exist = True
            if exist:
                await message.answer("Предмет удалён")
            else:
                await message.answer("Предмет не найден")
            status = 10
            await dialog(message)

            
if __name__ == "__main__":
    Sub1 = Subject("ОАиП")
    Subjects.append(Sub1)
    TempQueue = QueueInDay("12.12.2012")
    TempQueue.add("Поитов")
    TempQueue.add("Коля")
    TempQueue.add("Хомячим")
    Sub1.add(TempQueue)
    Sub1.add(QueueInDay("16.02.2025"))
    Sub2 = Subject("КПО")
    Subjects.append(Sub2)
    Sub2.add(QueueInDay("13.12.2024"))
    Sub2.add(QueueInDay("15.02.2023"))
    executor.start_polling(dp, skip_updates=True)
