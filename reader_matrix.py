import os

fifo_path = 'fifo'

# Открытие именованного канала для чтения
while True:
    with open(fifo_path, 'r') as fifo:
        while True:
            line = fifo.readline().split(";")
            matrix = line.split(",")
            if not line:
                break
            for string in matrix:
                print(string) 
