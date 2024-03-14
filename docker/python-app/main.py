import calendar

print('Добро пожаловать в календарь')

year = int(input("Enter year: "))
month = int(input("Enter month: "))
print(calendar.month(year, month))

