import logging
from collections import deque
from aiogram import Bot, Dispatcher, executor, types
import datetime 

logging.basicConfig(level=logging.INFO)
bot = Bot(token="5973966334:AAHjG4FY4yj__zJ0NxXLFkmSVem550Hb238")
dp = Dispatcher(bot)

status = 0
current_subject = None
current_date = None

class Date:

    def is_valid_date(date_string):
        try:
            datetime.datetime.strptime(date_string, "%d.%m.%Y")
            return True
        except ValueError:
            return False
    
    def compare(date_str1, date_str2):
        date_format = "%d.%m.%Y"
        date1 = datetime.datetime.strptime(date_str1, date_format).date()
        date2 = datetime.datetime.strptime(date_str2, date_format).date()
        return date1 > date2
    
class QueueInDay:

    def __init__(self, DateToCheck):
        self.DateOfQueue = DateToCheck
        self.queue = deque()
        
    def add(self, Name):
        self.queue.append(Name)

    def isEmpty(self):
        return (len(self.queue) == 0) 

    def get_data(self):
        s = ''
        temp = self.queue.copy()
        if self.isEmpty():
            s = "Очередь пуста"
        else:
            while (not self.isEmpty()):
                s = s + self.queue.popleft() + '\n'
            self.queue = temp
        return s

    def delete_item(self, Name):
        return self.queue.remove(Name)
        
class Subject:

    def __init__(self, NameOfSubject):
        self.Name = NameOfSubject
        self.ListOfDate = []

    def add_date(self, DayOfQueue):
        if not (DayOfQueue in self.ListOfDate):
            self.ListOfDate.append(DayOfQueue)
            self.date_sort()

    def del_date(self, DayOfQueue):
        self.ListOfDate.remove(DayOfQueue)

    def print_dates(self):
        s = ''
        for element in self.ListOfDate:
            s = s + element.Date + '\n'
        return s

    def date_sort(self):
        for i in range(len(self.ListOfDate)):
            for j in range(len(self.ListOfDate) - 1 - i):
                if Date.compare(self.ListOfDate[j].DateOfQueue, self.ListOfDate[j+1].DateOfQueue):
                    self.ListOfDate[j], self.ListOfDate[j+1] = self.ListOfDate[j+1], self.ListOfDate[j]
     

@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    global status
    global current_subject
    global current_date
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True) 
    keyboard.add(types.KeyboardButton("Приступить к работе"))
    keyboard.add(types.KeyboardButton("Что умеет бот?"))
    await message.answer("Добрый день. Нажмите на кнопку, чтобы начать", reply_markup=keyboard)
    status = 0
    current_subject = None
    current_date = None



@dp.message_handler(commands="settings")
async def add_info(message: types.Message): 
    await message.answer()   

@dp.message_handler()
async def dialog(message: types.Message):
    global status
    global current_subject
    global current_date
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) 
    if message.text == 'Выйти в главное меню':
        await cmd_start(message)        
    else:
        if status == 0:
            if message.text == 'Что умеет бот?':
                keyboard.clean()
                keyboard.add(types.KeyboardButton('Назад'))
                await message.answer('Ну тут что то расписать надо жестко', reply_markup=keyboard)
            elif message.text == 'Приступить к работе':
                for i in Subjects:
                    keyboard.add(types.KeyboardButton(i.Name))
                await message.answer("Выберите предмет", reply_markup=keyboard)
                status = 1
            elif message.text == "Назад":
                await cmd_start(message)
            else:
                await message.answer("Я вас не понял. Нажимайте на кнопки")    
        elif status == 1:
            if current_subject == None:
                for temp in Subjects:
                    if temp.Name == message.text:
                        current_subject = temp
            if not (current_subject == None):
                for temp in current_subject.ListOfDate:
                    keyboard.add(types.KeyboardButton(temp.DateOfQueue))
                keyboard.add(types.KeyboardButton("Выйти в главное меню"))           
                await message.answer("Выберите дату", reply_markup=keyboard)
                current_date = None
                status = 2
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
        elif status == 2:
            if current_date == None:
                for temp in current_subject.ListOfDate:
                    if temp.DateOfQueue == message.text:
                        current_date = temp
            if current_date == None:
                    for temp in current_subject.ListOfDate:
                        keyboard.add(types.KeyboardButton(temp.DateOfQueue))
                    keyboard.add(types.KeyboardButton("Выйти в главное меню"))
                    await message.answer("Вас не понял, нажимайте на кнопки", reply_markup=keyboard)    
            else:
                keyboard.add(types.KeyboardButton("Просмотреть очередь"))
                keyboard.add(types.KeyboardButton("Записаться в очередь"))
                keyboard.add(types.KeyboardButton("Выйти в главное меню"))
                status = 3
                await message.answer("Выберите, что хотите сделать", reply_markup=keyboard)
        elif status == 3:
            if message.text == "Просмотреть очередь":
                keyboard.add(types.KeyboardButton("Назад"))
                await message.answer("Очередь на " + current_subject.Name + " " + current_date.DateOfQueue + ":")
                await message.answer(current_date.get_data(), reply_markup=keyboard)
            elif message.text == "Записаться в очередь":
                await message.answer("Ваша фамилия")
                status = 4
            elif message.text == "Назад":
                status = 2
                await dialog(message)
            else:
                await message.answer("Вас не понял. Нажимайте на кнопки", reply_markup=keyboard)
        elif status == 4:
            current_date.add(message.text)
            status = 2
            await dialog(message)
    print("status = ", status, "    message.text = ", message.text)
    if not (current_subject == None):
        print("Предмет = ", current_subject.Name)
    if not (current_date == None):
        print("Дата = ", current_date.DateOfQueue)
    print('\n')

            


if __name__ == "__main__":
    Subjects = []
    Sub1 = Subject("ОАиП")
    Subjects.append(Sub1)
    TempQueue = QueueInDay("12.12.2012")
    TempQueue.add("Поитов")
    TempQueue.add("Катя")
    TempQueue.add("Коля")
    TempQueue.add("Хомячим")
    Sub1.add_date(TempQueue)
    Sub1.add_date(QueueInDay("16.02.2025"))
    Sub2 = Subject("КПО")
    Subjects.append(Sub2)
    Sub2.add_date(QueueInDay("13.12.2024"))
    Sub2.add_date(QueueInDay("15.02.2023"))
    executor.start_polling(dp, skip_updates=True)
