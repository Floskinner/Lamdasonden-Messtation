import random
from datetime import datetime
from datetime import timedelta

from database import db_connection


def generate_temp_data():
    for i in range(60):
        temp = random.randint(300, 1000)
        timestamp = datetime.now() - timedelta(minutes=60 - i)
        timestamp_str = timestamp.isoformat()
        db_connection.execute("INSERT INTO temps VALUES (?, ?)", (timestamp_str, temp))


if __name__ == "__main__":
    generate_temp_data()
