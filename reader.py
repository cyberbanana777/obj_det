import os

fifo_path = 'fifo'

# Открытие именованного канала для чтения
while True:
    with open(fifo_path, 'r') as fifo:
        while True:
            line = fifo.readline()
            if not line:
                break
            print(f"Получено: {line.strip()}")
