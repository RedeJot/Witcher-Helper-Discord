import random
from datetime import datetime

random_days = random.sample(range(1,7), 2)
print(random_days)

current_day = datetime.now().weekday()
print(current_day)