import datetime

from generator import Generator

date = datetime.datetime(2023, 10, 25)
while date < datetime.datetime.today() - datetime.timedelta(days=1):
    print(date)
    g = Generator()
    g.generate(date)
    date = date + datetime.timedelta(days=1)