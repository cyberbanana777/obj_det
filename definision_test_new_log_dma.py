'''
АННОТАЦИЯ

Последний актуальный скрипт.

Описание:
    На ардуино отсылается то, что должно. Всё остальное работает в штатном режиме, добавлены все константы

Задачи:
    Добавить нечеткую логику
    сделать так, что бы он выводил еще массив значений который не встречал ранее
    нужно ли распозновать все возможные формы кроме линии и корректировать после этого или корректироваться только если распознали что-то
'''


import serial
import time
import RPi.GPIO as GPIO
import mmap
import os

# разрешение 640 х 480

# time.sleep(20)
flag_matrix_layuot = 0
flag_simple_logic = 1

port = '/dev/Buzina_Nano'  # поменять
baudrate = 115200  # поменять
# 1 - правый поворот, 2 - левый поворот, 3 - объезд, 4 - разворот, 5 - поворот с объездом справа, 6 - поворот с объездом слева, 7 - проехать и остановиться
function_to_move = 0
function_to_grab = 0  # 1 - схватить, 2 - переставить, 3 - переставить с грузом на борту
correction_speed_to_right_wheels = 0
correction_speed_to_left_wheels = 0
# на каком расстояни роботот должен остановиться, что бы схватить цилиндр с небольшим допуском, поменять!
max_distance_for_color_obj = 31
# Для ПДа
pred_norm_x = 0
# обновляющиеся массивы объектов
black_objects_roi = []
color_objects_central = []
black_objects = []
matrix = []
id_matrix = ''


# считывает скорость для моторов


def go_to_line(black_objects_roi):
    global pred_norm_x, corect_flag
    correction_speed_to_right_wheels = 0
    correction_speed_to_left_wheels = 0
    if len(black_objects_roi) == 1:
        x = black_objects_roi[0][3]
        width = black_objects_roi[0][1]
        norm_x = black_objects_roi[0][5]
    else:
        obj = min(black_objects_roi, key=lambda x: (x[3])**2 + (x[4])**2)
        x = obj[3]
        norm_x = obj[5]
        width = obj[1]
        if norm_x > 0.1:
            corect_flag = 1

    Kp = 1.3
    Kd = 0.3
    if width < 150:
        if (norm_x > 0 and pred_norm_x < 0) or (norm_x < 0 and pred_norm_x > 0):
            pred_norm_x = 0

        if x > 0:
            correction_speed_to_left_wheels = round(
                norm_x * Kp - (pred_norm_x - norm_x) * Kd, 3)
        if x < 0:
            n_norm_x = abs(norm_x)
            pred_norm_x = abs(pred_norm_x)
            correction_speed_to_right_wheels = round(
                n_norm_x * Kp - (pred_norm_x - norm_x) * Kd, 3)

    pred_norm_x = norm_x
    return correction_speed_to_right_wheels, correction_speed_to_left_wheels


pred_norm_x_roi = 0


def corection_way():
    global pred_norm_x_roi
    limit = 0.04
    if black_objects_roi != []:

        if len(black_objects_roi) == 1:
            x_cor = black_objects_roi[0][5]
        elif len(black_objects_roi) > 1:
            print('FOR MISTAKE:', black_objects_roi, len(black_objects_roi))
            obj = min(black_objects_roi, key=lambda x: (x[3])**2 + (x[4])**2)
            x_cor = obj[5]

        if -limit <= x_cor <= limit:
            return 0

        else:
            correction_speed_to_right_wheels = x_cor
            correction_speed_to_left_wheels = 0
            function_to_move = 11
            function_to_grab = 0

            data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
                str(correction_speed_to_right_wheels) + ";" + \
                str(correction_speed_to_left_wheels) + ";#"

            ser.write(data_to_arduino.encode('utf-8'))
            print(f'Message sent to serial: {data_to_arduino}')

            pred_norm_x_roi = x_cor

            return 1
    else:
        if pred_norm_x_roi != 0:
            correction_speed_to_right_wheels = pred_norm_x_roi
        else:
            correction_speed_to_right_wheels = -1
        correction_speed_to_left_wheels = 0
        function_to_move = 11
        function_to_grab = 0

        data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
            str(correction_speed_to_right_wheels) + ";" + \
            str(correction_speed_to_left_wheels) + ";#"

        ser.write(data_to_arduino.encode('utf-8'))
        print(f'Message sent to serial: {data_to_arduino}')
        return 1


def recognize_shape(id_matrix, black_objects, matrix):
    line_recognize_flag = 1

    if len(black_objects) == 1:
        width = black_objects[0][1]
        height = black_objects[0][2]
        x = black_objects[0][3]
        y = black_objects[0][4]
    elif len(black_objects) == 0:
        line_recognize_flag = 0
    else:
        obj = min(black_objects, key=lambda x: (x[3])**2 + (x[4])**2)
        width = obj[1]
        height = obj[2]
        x = obj[3]
        y = obj[4]

    # dead_end = ['1111011111110111100111011', '1111011111111111001110011', '1111111111101111011110111', '1111111111111111110111101', '1111111111111111111011100', '1111111111111111100111001', '1111111111111111001110011', '1111111111111111111011110', '1111011111111111100111001', '1111111111111111110011101', '1111111111110111101111011', '1111011111110111101111011', '1111011111101111011110111', '1111111111111111101111011', '1111111111111111110011100', '1111111111111011110111101', '0011110100000001011110111', '0111100100000010011110111', '1011110110000001011110011', '1111000110100001111011101', '1110000100000001110011101', '1100111001000001110111101', '1110001100000001110011101', '1111000010100001111011110', '1101111011000000101111011', '0011100100000000011110111', '1001110011000001101111011', '0111101000000010011110111',
    #             '1101111011000001101111011', '1111000110100001111011110', '1101111010000001101111011', '0111100100000000011110111', '1111001110000001110011101', '1011110000000001001110011', '0111101000000010111100111', '0011110100000000011110111', '0111101000000010111101111', '1111110010110001111011110', '1110111001000001110111101', '0111101100000010011110111', '1101111011000000100111011', '1111000110000001110011100', '1111010010100001111011110', '1011110100000001011110111', '1110111101000001110111101', '1111000110000001111011100', '0111101000000110111101111', '1100111001000001100111001', '1101111000000001101111011', '1001110011000001001111011', '1101111011000001100111011', '1101111001000001101111011', '1011110110000001011110111', '1111000100000001110011100', '1110101101000001110111101', '1111010010110001111011110']

    platform = ['1101100011000110000110111', '1111110000100001000011001', '1111110001000010000110011', '1101110001100011000111011', '1110110001100011000111011', '1101100011000010000110011', '1101100011000110001110111', '1111110001100011000111011', '1000110001100011000011011', '1111111000110001100011100', '1101111000110001100011100', '1110110001100011000111011', '1101110000100001000011000', '1111110001100001000011001', '1101100001000010000110011', '1111111000110001000011100', '1100110001100011000011011', '1000110001100001000011011', '1111100111000110001100111',
                '1000110001100011000111011', '1100110001100011000111011', '1000110001100011000011001', '1101100011000010000100011', '1101100011000110000100011', '1111110001100011000111001', '1111100011000110001100111', '1101111000110001000011000', '1111110000100001000011001', '1111100001000010000110011', '1101110001000010000110011', '1111111100110001100011100', '1111110001100011000011001', '1111110001100011000111011', '1111110001100010000110011', '1111110001000010000110011', '1111110001100011000110001', '1101100011000110001100111', '1000110000100001100111011', '1111111000110001000011000']

    # left_turn = ['1111111111001110011100111', '1111101111000011110111001', '1111111111000011100111001', '1111101111000011100111001', '1111111111001110011110011', '1111111111000111001110011', '1111111111000110001111011', '1111111111000111001111011', '1111111111001110001110011',
    #              '1111100111000011110111101', '1111100111000011100111001', '1111111111011110111100111', '1111111111001110011110111', '1111111111011110111101111', '1111111111011110011100111', '1111100111000011110111001', '1111111111000110001110011', '1111111111000111101111011', '1111111111001111001110011']
    # right_turn = ['1111111111100001001110011', '1111111111111001110011101', '1111111111110001000111011', '1111111111110001100111011', '1111111111111001100011001', '1111111111110001000010011',
    #               '1111111111110001100011011', '1111111111100001011110111', '1111111111111001110011001', '1111111111111001110011100', '1111111111110001000110011', '1111111111110001100011001', '1111111111100001001110111']
    # right_E_crossroad = ['0111101000000110111100111', '1101111011110001101111011', '1110111101111001100111001', '1101111011110001101111001', '1111011100111001110011101', '0111101000000110111101111', '1110111001110001100111001', '1011110000100001011110011', '0111100000100111011110111', '1110111101111001110111001', '1011110100100001011110111', '1111011110111101111001110', '1101111011110001100111011', '1110011100111001110011101', '0111110000100011011110111', '0111101000000110011110111', '1100111001110001100111001', '1101111001110001100111001', '1011110100100011011110111', '0111101000000110011100111', '1101111011110001100011011', '1111110000100011011110111', '1101111000110001101110011',
    #                      '1111011110111101110011100', '1111010000001110111101111', '1111111110111101111011110', '1101111000110001001110011', '0111101000000111011110111', '1011110000100001001110011', '1111111111111101111001110', '1110010001001111111101111', '1110111101111001110011101', '0111101000100111011110111', '1011110000100011011110111', '1111111111111111111011110', '1111011110111101111011110', '1111111111111111111001110', '0111100000000110011100111', '0111001000000110111101111', '1111011110111101111011100', '0111100000100011011110111', '1111010001001110111101111', '1111000000001110111101111', '1101111000110001101111011', '1101111010110001101111011', '1110111101111001110111101', '1011110000100001011110111']

    # left_E_crossroad = ['1001111011000111001111011', '1011110111001110011110111', '1101111011000111100111001', '1110001100000001110111101', '0111101111001110011100111', '1101111011000111101111011', '1100111001000011100111001', '1011110111000111001110011', '0111101111011110011100111', '1011110111001111001110011', '1110111001000011100111001', '1110000100100001110011100', '1001110011100110001110011', '1101111011110110001111011', '1011110111001110001110011', '1001110011000110001111011', '1011110111001111011110011', '1101111011000110001111011', '1001110011000111101111011', '1111000100100001110011100',
    #                     '1111000110100001110011100', '0111101111001110011110111', '0011110111001110011110111', '1001110011000111001111011', '0111101111011110111100111', '1011110011000111001110011', '1011110011001110001110011', '1001110011000111001110011', '1110001100000001110011101', '1110000100000001110011101', '1101111011000111001111011', '1101111011100110001111011', '1001110011100110001111011', '1101111001000111001111011', '0011100111001110011110111', '1011110111001111011110111', '1110111101000011110111101', '1110001100000011110111101', '1101110011100110001111011', '1101110011000110001110011', '1001110011000110001110011']
    # T_crossroad = ['1111110000000110111101111', '1111100111000001110111101', '1111100111100001110011100', '1111101111000001100111001', '0010000001111001111011111', '1111111111000001110111101', '1111010000000110111101111', '1111111000000001011110111', '0011100001110001111011110', '1111111110000001101111011', '1111101111000001110111101', '1111111110000001001110011', '1111100011100001111011100', '1111111111000001100111001', '1111111100000001001110011', '0111100011100001111011100', '1111110000000001101111011', '1111100011110001111011110', '1111111100000001101111011', '1111111000000110011100111', '1111100111000001100111001', '1111111100000001001111011',
    #                '1111111111000001001111011', '1111100111100001110011101', '1111111111000001101111011', '1111100011100001110011101', '1111111000000001101111011', '1111100000000001101111011', '1111100011100001110011100', '0011100001111001111011111', '1111100011000001110111101', '1111111000000010011110111', '1111011000000110111101111', '0011100001111001111011110', '0111100011110001111011110', '0111100001100001111011100', '0011000001111001111011111', '1111111000000011011110111', '1111100011100001111011110', '1111111000000110011110111', '1111111000000001001110011', '1111111100000001011110011', '0111100001110001111011110', '1111111000000110111100111']

    # X_crossroad = ['0011110100000001011110111', '0111100100000010011110111', '1011110110000001011110011', '1111000110100001111011101', '1110000100000001110011101', '1100111001000001110111101', '1110001100000001110011101', '1111000010100001111011110', '1101111011000000101111011', '0011100100000000011110111', '1001110011000001101111011', '0111101000000010011110111', '1101111011000001101111011', '1111000110100001111011110', '1101111010000001101111011', '0111100100000000011110111', '1111001110000001110011101', '1011110000000001001110011', '0111101000000010111100111', '0011110100000000011110111',
    #                '0111101000000010111101111', '1111110010110001111011110', '1110111001000001110111101', '0111101100000010011110111', '1101111011000000100111011', '1111000110000001110011100', '1111010010100001111011110', '1011110100000001011110111', '1110111101000001110111101', '1111000110000001111011100', '0111101000000110111101111', '1100111001000001100111001', '1101111000000001101111011', '1001110011000001001111011', '1101111011000001100111011', '1101111001000001101111011', '1011110110000001011110111', '1111000100000001110011100', '1110101101000001110111101', '1111010010110001111011110']

    dead_end_layuot = [
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  1,  2,  3,  1,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  1,  9, 15, 12,  5,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  1,  5, 30, 52, 34, 12,  3,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1,  8, 36, 59, 39, 20,  6,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1,  9, 40, 60, 42, 20,  5,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 10, 40, 60, 42, 22,  5,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 13, 41, 60, 44, 20,  5,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 14, 44, 62, 43, 21,  6,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 14, 45, 62, 44, 21,  5,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 15, 47, 62, 47, 22,  6,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 17, 49, 65, 48, 23,  6,  1,  0,  0,  0,  0]]
    mean_for_1_dead_end_layuot = 20.950617283950617

    platform_layuot = [
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  4,  7, 13, 17, 14, 14,  6,  5,  2,  0,  0,  0,  0],
        [1,  5,  7, 15, 20, 24, 25, 24, 25, 22, 15,  9,  7,  4,  1,  0],
        [1,  7, 16, 27, 41, 51, 53, 55, 51, 37, 26, 19, 15,  9,  1,  0],
        [3, 10, 22, 35, 48, 61, 64, 64, 67, 54, 39, 30, 23, 13,  2,  1],
        [4, 12, 23, 35, 48, 63, 73, 80, 77, 67, 53, 39, 28, 16,  2,  1],
        [4, 12, 25, 35, 50, 64, 74, 83, 80, 68, 53, 41, 29, 15,  1,  1],
        [5, 12, 22, 32, 51, 66, 73, 84, 78, 67, 52, 40, 28, 15,  1,  1],
        [5, 11, 21, 30, 46, 56, 66, 69, 65, 61, 53, 38, 27, 14,  1,  1],
        [3,  8, 17, 26, 42, 52, 60, 64, 59, 56, 50, 34, 22, 12,  1,  1],
        [2,  9, 13, 20, 36, 47, 58, 57, 51, 49, 44, 27, 18, 10,  1,  0],
        [2,  3,  5, 13, 26, 34, 42, 39, 37, 43, 35, 18, 13,  5,  0,  0],
        [1,  2,  1, 10, 21, 32, 40, 37, 33, 35, 28, 13,  7,  4,  0,  4],
        [0,  0,  2,  9, 20, 26, 35, 34, 28, 29, 24, 12,  4,  2,  0,  4],
        [0,  0,  2, 11, 20, 29, 36, 34, 31, 26, 18,  7,  0,  0,  0,  2]]
    mean_for_1_platform_layuot = 27.857142857142858

    left_turn_layuot = [
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0, 0, 0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [30, 30, 30, 30, 30, 30, 30, 30, 30,  30,  30,  30,  0,  0,  0,  0],
        [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 30, 0, 0, 0, 0],
        [80, 80, 80, 80, 80, 80, 80, 80, 80, 80, 50, 30, 0, 0, 0, 0],
        [100, 100, 100, 100, 100, 100, 100, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [100, 100, 100, 100, 100, 100, 100, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [80, 80, 80, 80, 80, 80, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [30, 30, 30, 30, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0]
    ]

    # left_turn_layuot = [
    #     [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    #     [1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    #     [15, 11, 10,  9,  2,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    #     [46, 44, 41, 36, 32, 28, 21, 17, 11,  4,  0,  0,  0,  0,  0,  0],
    #     [62, 64, 68, 71, 72, 79, 71, 64, 44, 22,  4,  0,  0,  0,  0,  0],
    #     [47, 48, 52, 55, 62, 65, 63, 69, 61, 28,  7,  2,  1,  0,  0,  0],
    #     [17, 17, 17, 17, 16, 20, 32, 51, 55, 28,  7,  2,  1,  0,  0,  0],
    #     [1,  1,  1,  1,  2, 12, 26, 51, 53, 24,  6,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 13, 27, 53, 52, 23,  5,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 13, 29, 59, 56, 20,  5,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 13, 31, 63, 57, 20,  4,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 13, 32, 63, 61, 20,  4,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 15, 32, 63, 62, 20,  4,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 15, 36, 65, 62, 20,  4,  2,  0,  0,  0,  0],
    #     [0,  0,  0,  0,  2, 16, 40, 66, 60, 21,  5,  1,  0,  0,  0,  0]
    # ]
    mean_for_1_platform_layuot = 27.58677685950413

    right_turn_layuot = [
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1],
        [0,  0,  0,  0,  0,  0,  3, 11, 15, 16, 15, 14, 13, 13, 13, 13],
        [0,  0,  0,  0,  2,  5, 20, 60, 78, 84, 78, 72, 68, 61, 52, 46],
        [0,  0,  0,  0,  2,  5, 26, 65, 82, 81, 75, 75, 74, 77, 74, 68],
        [0,  0,  0,  0,  1,  5, 24, 60, 57, 33, 18, 25, 32, 36, 41, 46],
        [0,  0,  0,  0,  1,  6, 30, 61, 55, 23,  2,  1,  4,  4,  7, 12],
        [0,  0,  0,  0,  1,  7, 31, 65, 55, 23,  2,  0,  0,  0,  1,  1],
        [0,  0,  0,  0,  1,  7, 34, 66, 56, 20,  1,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  1,  8, 39, 70, 57, 20,  1,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  1,  8, 41, 72, 56, 18,  1,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  1,  8, 44, 76, 56, 16,  1,  0,  0,  0,  0,  0],
        [0,  0,  0,  0,  1, 10, 47, 78, 54, 16,  1,  0,  0,  0,  0,  0]
    ]
    mean_for_1_right_turn_layuot = 30.91346153846154

    left_E_crossroad_layuot = [
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [30, 30, 30, 30, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [80, 80, 80, 80, 80, 80, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [100, 100, 100, 100, 100, 100, 100, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [100, 100, 100, 100, 100, 100, 100, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [80, 80, 80, 80, 80, 80, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [30, 30, 30, 30, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0],
        [0, 0, 0, 0, 30, 50, 80, 100, 100, 80, 50, 30, 0, 0, 0, 0]
    ]

    # left_E_crossroad_layuot = [
    #     [3,  2,  4,  6,  9,  9, 21, 23, 17, 15, 15, 10,  6,  7,  1,  3],
    #     [4,  2,  5,  8,  9, 10, 21, 22, 16, 15, 16, 10,  6,  7,  1,  2],
    #     [6,  5,  4,  9, 12, 13, 24, 23, 16, 15, 15, 10,  6,  7,  1,  2],
    #     [16, 16, 10, 13, 14, 17, 27, 26, 17, 15, 18,  9,  7,  6,  2,  2],
    #     [33, 32, 33, 36, 36, 38, 42, 34, 23, 18, 19,  8,  8,  6,  2,  2],
    #     [36, 43, 48, 49, 51, 55, 55, 44, 32, 29, 23,  7,  8,  5,  2,  1],
    #     [36, 39, 39, 44, 46, 46, 50, 43, 37, 26, 24, 11, 10,  6,  2,  1],
    #     [32, 31, 27, 34, 39, 38, 46, 40, 34, 24, 21,  8,  9,  5,  2,  0],
    #     [20, 21, 23, 27, 32, 34, 37, 38, 29, 26, 19,  9,  7,  3,  2,  0],
    #     [9, 10, 11, 16, 24, 27, 26, 30, 27, 22, 16, 11,  7,  3,  2,  0],
    #     [0,  1,  2,  6, 18, 24, 21, 30, 29, 20, 14, 12,  8,  3,  1,  0],
    #     [0,  1,  2,  6, 20, 25, 23, 33, 30, 19, 16, 12,  8,  3,  1,  0],
    #     [0,  1,  2,  6, 20, 25, 22, 34, 29, 18, 18, 13,  8,  3,  0,  0],
    #     [0,  1,  2,  6, 22, 27, 24, 34, 28, 19, 18, 12,  6,  3,  0,  1],
    #     [0,  1,  2,  6, 22, 27, 24, 35, 29, 18, 18, 13,  6,  2,  0,  0],
    #     [0,  1,  2,  6, 24, 26, 26, 36, 28, 16, 19, 15,  5,  2,  1,  1]
    # ]

    mean_for_1_left_E_crossroad_layuot = 17.354166666666668

    right_E_crossroad_layuot = [
        [0,  0,  0,  1,  1,  6, 21, 32, 34, 21,  9,  2,  6,  0,  1,  0],
        [0,  0,  0,  1,  1,  5, 21, 37, 35, 20, 10,  3,  5,  0,  1,  0],
        [0,  0,  0,  1,  1,  4, 21, 40, 37, 18,  8,  3,  5,  0,  1,  0],
        [0,  0,  0,  1,  1,  4, 23, 48, 37, 20,  8,  4,  6,  1,  1,  2],
        [0,  0,  0,  1,  2,  4, 24, 52, 41, 28, 15, 12, 17, 14, 14, 14],
        [0,  0,  0,  1,  2,  4, 24, 62, 55, 48, 39, 32, 35, 32, 32, 32],
        [0,  0,  0,  1,  2,  5, 28, 69, 70, 65, 54, 49, 52, 46, 41, 36],
        [0,  0,  0,  1,  2,  5, 32, 67, 60, 57, 56, 56, 57, 51, 51, 47],
        [0,  0,  0,  1,  2,  4, 33, 64, 45, 37, 33, 35, 38, 37, 41, 40],
        [0,  0,  0,  1,  2,  5, 36, 65, 40, 24,  9, 11, 16, 12, 16, 17],
        [0,  0,  0,  1,  2,  5, 41, 67, 36, 16,  5,  6,  7,  2,  3,  4],
        [0,  0,  0,  1,  1,  5, 45, 70, 34, 16,  3,  5,  5,  0,  0,  2],
        [0,  0,  0,  1,  1,  5, 51, 71, 37, 16,  3,  5,  5,  0,  0,  0],
        [0,  0,  0,  0,  1,  7, 54, 74, 37, 14,  4,  5,  5,  0,  0,  0],
        [0,  0,  0,  0,  1, 11, 57, 75, 38, 14,  4,  5,  4,  0,  0,  0],
        [0,  0,  0,  0,  1, 13, 58, 74, 37, 15,  4,  5,  0,  0,  0,  0]
    ]
    mean_for_1_right_E_crossroad_layuot = 22.402173913043477

    T_crossroad_layuot = [
        [0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0],
        [2,  1,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  1,  1],
        [8,  5,  4,  4,  4,  4,  2,  0,  0,  0,  0,  1,  1,  7,  7,  8],
        [11, 10, 10, 12, 10, 12, 14, 13, 13, 14, 14, 14, 12, 11, 11, 11],
        [29, 27, 26, 27, 25, 25, 24, 26, 27, 27, 22, 18, 19, 18, 16, 17],
        [42, 37, 33, 28, 31, 35, 34, 32, 30, 29, 28, 26, 25, 27, 27, 29],
        [37, 37, 42, 44, 47, 46, 47, 46, 52, 50, 48, 41, 42, 41, 35, 35],
        [33, 38, 42, 48, 49, 55, 56, 58, 52, 50, 48, 39, 37, 38, 35, 36],
        [21, 22, 22, 28, 33, 39, 42, 49, 50, 37, 38, 30, 27, 27, 29, 26],
        [8,  8,  8, 11, 15, 16, 24, 38, 44, 30, 28, 21, 21, 20, 22, 19],
        [4,  3,  1,  7, 14, 17, 19, 34, 39, 24, 17, 10,  6,  7,  9, 11],
        [0,  1,  2,  7, 14, 18, 24, 34, 38, 23, 17, 10,  3,  1,  2,  4],
        [0,  1,  2,  7, 15, 18, 26, 36, 38, 25, 17, 10,  3,  1,  0,  0],
        [0,  1,  2,  7, 16, 19, 27, 38, 38, 26, 17, 10,  3,  1,  0,  0],
        [0,  1,  2,  7, 16, 21, 28, 40, 42, 27, 16, 11,  3,  2,  2,  7],
        [0,  1,  2,  8, 17, 22, 29, 40, 42, 26, 15, 11,  3,  1,  1, 20]
    ]
    mean_for_1_T_crossroad_layuot = 21.683720930232557

    X_crossroad_layuot = [
        [0,  0,  0,  0,  3,  9, 16, 34, 43, 28,  5,  6,  1,  0,  0,  0],
        [0,  0,  0,  0,  3,  9, 16, 35, 44, 28,  7,  6,  1,  0,  0,  0],
        [1,  0,  0,  0,  3,  9, 16, 37, 50, 27,  7,  6,  0,  0,  0,  0],
        [3,  2,  1,  1,  2,  9, 17, 39, 51, 26,  8,  6,  0,  0,  0,  0],
        [9,  7,  6,  4,  5, 11, 20, 41, 51, 24,  9,  6,  0,  2,  3,  4],
        [33, 32, 31, 28, 29, 30, 36, 60, 61, 32, 19, 15,  9,  9, 11, 12],
        [56, 58, 60, 63, 64, 68, 71, 86, 83, 66, 60, 54, 46, 43, 37, 36],
        [57, 57, 59, 63, 66, 67, 71, 78, 84, 74, 73, 72, 71, 63, 62, 59],
        [30, 30, 31, 31, 33, 40, 49, 65, 72, 55, 50, 46, 45, 50, 51, 53],
        [8,  8,  8,  7,  7, 13, 28, 57, 58, 31, 22, 17, 18, 24, 26, 27],
        [0,  0,  0,  0,  2,  9, 28, 58, 55, 21, 10,  3,  0,  2,  4,  4],
        [0,  0,  0,  0,  2,  9, 30, 62, 57, 21,  9,  2,  0,  0,  0,  0],
        [0,  0,  0,  0,  2, 11, 30, 62, 57, 23, 10,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  2, 12, 30, 62, 58, 24, 10,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  2, 12, 32, 63, 58, 26, 10,  1,  0,  0,  0,  0],
        [0,  0,  0,  0,  2, 13, 32, 62, 59, 25,  9,  1,  0,  0,  0,  1]
    ]
    mean_for_1_X_crossroad_layuot = 29.956989247311828

 # если линия, то просто едем
    line_width = 200
    displaced_x = 20

    if flag_simple_logic == 1:

        if line_recognize_flag == 0:
            return 'unknown'

        if width < line_width and height == 480:
            return 'line'
        elif width <= line_width and height < 260 and -50 < x < 50:
            return 'dead_end'
        
        for i in platform:
                if id_matrix == i:
                    return 'platform'
           
        sum_middle_line_matrix = 0   
        for el in matrix[2]:
            sum_middle_line_matrix += el

        if width > line_width and x < -displaced_x and sum_middle_line_matrix <= 2:
            return 'left_turn'
        elif width > line_width and x > displaced_x and sum_middle_line_matrix <= 2:
            return 'right_turn'
        elif sum_middle_line_matrix <= 2:
            return 'right_turn'

    if flag_matrix_layuot == 1:
        shape = 'unknown'
        shape_presumably = 0

        layouts = [[dead_end_layuot, mean_for_1_dead_end_layuot, 'dead_end'],
                   [platform_layuot, mean_for_1_platform_layuot, 'platform'],
                   [left_turn_layuot, mean_for_1_platform_layuot, 'left_turn'],
                   [right_turn_layuot, mean_for_1_right_turn_layuot, 'right_turn'],
                   [left_E_crossroad_layuot, mean_for_1_left_E_crossroad_layuot,
                       'left_E_crossroad'],
                   [right_E_crossroad_layuot, mean_for_1_right_E_crossroad_layuot,
                       'right_E_crossroad'],
                   [T_crossroad_layuot, mean_for_1_T_crossroad_layuot,
                       'T_crossroad'],
                   [X_crossroad_layuot, mean_for_1_X_crossroad_layuot,
                       'X_crossroad']
                   ]

        if line_recognize_flag == 1 and width < line_width and height == 480:  # add with debag
            return 'line'

        max_sum_weight = 0
        posible_mus = []

        for layout in layouts:
            sum_weight = 0

            for i in range(16):
                for j in range(16):
                    if j in [6, 7, 8, 9] or i in [6, 7, 8, 9]:  # add with debug
                        scaller = 1
                    else:
                        scaller = 1
                    if matrix[i][j] == 1:
                        sum_weight += (100 - layout[0][i][j]) * scaller
                    if matrix[i][j] == 0:
                        sum_weight += layout[0][i][j] * scaller
            posible_mus.append([layout[2], sum_weight / 25600])
            if sum_weight > max_sum_weight:
                max_sum_weight = sum_weight
                shape_presumably = layout[2]

        print('POSIBLE_MUS:  ', posible_mus)  # add with debag
        print("shape_presumably:", shape_presumably,
              "weight:", max_sum_weight / 25600)

        if (max_sum_weight / 25600) > 0.15:  # add with debag
            shape = shape_presumably

        return shape

        # for i in dead_end:
        #     if id_matrix == i:
        #         shape = 'dead_end'

        # for i in right_E_crossroad:
        #     if id_matrix == i:
        #         shape = 'right_E_crossroad'

        # for i in left_E_crossroad:
        #     if id_matrix == i:
        #         shape = 'left_E_crossroad'

        # for i in T_crossroad:
        #     if id_matrix == i:
        #         shape = 'T_crossroad'

        # for i in X_crossroad:
        #     if id_matrix == i:
        #         shape = 'X_crossroad'

        # for i in right_turn:
        #     if id_matrix == i:
        #         shape = 'right_turn'

        # for i in left_turn:
        #     if id_matrix == i:
        #         shape = 'left_turn'


def way_function(shape, color, do_color):
    function_to_move = 0
    function_to_grab = 0
    # if color == 'Green' and do_color:
    #     # function_to_grab = 1
    #     pass
    # elif color == 'Blue' and do_color:
    #     # function_to_grab = 2
    #     pass
    # elif color == 'Red' and shape == 'dead_end':
    #     function_to_move = 3
    # elif color == 'Red' and shape == 'right_turn':
    #     function_to_move = 5
    # elif color == 'Red' and shape == 'left_turn':
    #     function_to_move = 6
    # elif color == 'Red' and shape == 'right_T_crossroad':
    #     function_to_move = 1
    # elif shape == 'platform' and color != 'Green':
    #     function_to_move = 7
    if shape == 'dead_end':
        function_to_move = 4
    elif shape == 'right_turn':
        function_to_move = 1
    elif shape == 'left_turn':
        function_to_move = 2
    elif shape == 'right_E_crossroad':
        function_to_move = 1
    elif shape == 'left_E_crossroad':
        pass
    elif shape == 'T_crossroad':
        function_to_move = 2
    elif shape == 'X_crossroad':
        function_to_move = 2
    elif shape == 'platform':  # было добавлено
        function_to_move = 7

    return function_to_move, function_to_grab


def recognize_color(color_objects):
    cylinder = min(color_objects, key=lambda x: (x[3])**2 + (x[4])**2)
    color = cylinder[0]
    if color == 'Green':
        return 'Green'
    elif color == 'Blue':
        return 'Blue'
    elif color == 'Red':
        return 'Red'


def read_dma():
    global id_matrix
    global black_objects_roi
    global black_objects
    global color_objects

    # Прочитать данные из общей памяти
    data = shm.read()
    shm.seek(0)
    line = data.decode('utf-8')

        
    #print("DEBAG: data from dma:", line)    


    if len(line) != 0:
        now = line.split(";")
        now.pop()
        l = 0
        k_roi = 0
        k_black = 0
        for i in now:
            obj = i.split(",")
            first = obj.pop(0)
            if first == 'Black_roi':
                black_objects_roi.append(
                    [first] + [float(j) for j in obj])
                black_objects_roi[k_roi][4] = - \
                    black_objects_roi[k_roi][4] + 240
                black_objects_roi[k_roi][3] = black_objects_roi[k_roi][3] - 320
                k_roi += 1
            elif first == 'Matrix':
                id_matrix = "".join(obj)
                for j in obj:
                    stroka = []
                    for a in j:
                        a_int = int(a)
                        stroka.append(a_int)
                    matrix.append(stroka)
            elif first == 'Black':
                print("DEBUG", 'black_objects:', black_objects, "k_black:",
                      k_black, 'new_el:', [first] + [float(j) for j in obj])
                black_objects.append(
                    [first] + [float(j) for j in obj])
                black_objects[k_black][4] = - \
                    black_objects[k_black][4] + 240
                black_objects[k_black][3] = black_objects[k_black][3] - 320
                k_black += 1
            else:
                color_objects.append([first] + [float(j) for j in obj])
                color_objects[l][4] = -color_objects[l][4] + 240
                color_objects[l][3] = color_objects[l][3] - 320
                l += 1


try:
    dma = open("/dev/shm/shared_mem", "rb")
    shm = mmap.mmap(dma.fileno(), 0, access=mmap.ACCESS_READ)
    time.sleep(2)
except Exception as e:
    print('Error:', e)


GPIO.setmode(GPIO.BCM)  # Используем BCM нумерацию
# Устанавливаем GPIO 17 как вход
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
set_mus = set()
mes_time = 0
mes_delay = 0

count_crosses = 0
count_E_crosses = 0
count_T_crosses = 0
count_X_crosses = 0

flag_back = 0
state_flag = 0
count = 0

corect_flag = 0
wait_flag = 0
mess_flag = 0
test_flag = 0  # !!!!!!!!!!!!!!!!!!!!! TEST !!!!!!!!!!!!!!!!!!!!

shape = 0
time_send_messege = 0

start_time = 0
count_print = 0
try:
    # Открываем COM-порт
    ser = serial.Serial(port, baudrate)
    print("Соединение с Arduino установлено.")
    time.sleep(2)

    # Небольшая задержка для установления соединения
    time.sleep(2)

    while True:
        input_state = GPIO.input(17)  # Читаем состояние GPIO 17

        if input_state == GPIO.LOW and count == 1:
            state_flag = 0
            count = 0
            print('Ожидание сигнала...\n')

        if input_state == GPIO.HIGH and state_flag == 0:
            while True:

                start_time = time.time()

                input_state = GPIO.input(17)
                if input_state == GPIO.LOW:
                    state_flag = 1
                    count = 1
                    break

                function_to_move = 0
                function_to_grab = 0
                correction_speed_to_right_wheels = 0
                correction_speed_to_left_wheels = 0
                black_objects_roi = []
                color_objects = []
                black_objects = []
                matrix = []
                id_matrix = 0
                color = 0
                shape = 0

                print('Corect_flag:', corect_flag)
                print('Wait_flag:', wait_flag)

                # получение данных с камеры
                read_dma()
                print('Black_objects_roi:', black_objects_roi)
                print('Black_objects:', black_objects)
                print('Color_objects:', color_objects)

                print('Id_matrix:', id_matrix)
                count_print += 1

                
                print('Matrix:')
                for h in matrix:
                    print(h)

                set_mus.add(id_matrix)

                # получение сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
                if ser.in_waiting > 0:
                    data_from_arduino = ser.readline()
                    data_from_arduino = data_from_arduino.decode(
                        'utf-8').strip()
                    print(f'Message get from serial: {data_from_arduino}')
                else:
                    print('No data from Arduino')
                    data_from_arduino = 0

                serial_data = ser.in_waiting
                if serial_data > 0:
                    print('Were still data', serial_data)
                    r = ser.read_all()

                try:
                    if 0 < float(data_from_arduino) <= max_distance_for_color_obj:
                        do_color = 1
                    else:
                        do_color = 0
                except ValueError:
                    print('Uncorrect messege or text messege')

                # конец блок получения сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬

                # блок логики ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬

                # Распознование формы и цвета
                if corect_flag == 0 and wait_flag == 0:
                    if color_objects != []:
                        color = recognize_color(color_objects)
                    print(f'Color: {color}')

                    if id_matrix != 0:
                        shape = recognize_shape(
                            id_matrix, black_objects, matrix)

                    
                    print(f'Shape: {shape}')

                    if (shape != 0 and shape != 'unknown' and shape != 'line') or (color != 0 and do_color == 1):
                        corect_flag = 1  # change with debug
                        mess_flag = 1  # change with debug

                # корректировка положения макленькими поворотами
                if corect_flag == 1 and wait_flag == 0 and test_flag == 0:
                    corect_flag = corection_way()

                # отправка сообщения на ардуино
                if corect_flag == 0 and wait_flag == 0 and mess_flag == 1 and test_flag == 0:

                    shape = recognize_shape(id_matrix, black_objects, matrix)
                    function_to_move, function_to_grab = way_function(
                        shape, color, do_color)

                    data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))

                    print(f'Message sent to serial: {data_to_arduino}')
                    time.sleep(0.05)

                    time_send_messege = time.time()
                    wait_flag = 1
                    mess_flag = 0
                elif corect_flag == 0 and wait_flag == 0 and mess_flag == 0 and test_flag == 0:

                    # ПДи
                    if black_objects_roi != []:
                        correction_speed_to_right_wheels, correction_speed_to_left_wheels = go_to_line(
                            black_objects_roi)

                    data_to_arduino = "$" + str(0) + ";" + str(0) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))
                    print(f'Message sent to serial: {data_to_arduino}')

                if (data_from_arduino == 'OK' or time.time() - time_send_messege > 8) and wait_flag == 1 and test_flag == 0:
                    corect_flag = 1
                    wait_flag = 0

                time.sleep(0.05) # 0.05
                print('Time:', time.time() - start_time)
                print('')

                # конец блока логики ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬


except KeyboardInterrupt:
    print("Прерывание программы. Закрытие порта...")
    # print(list(set_mus))

# except Exception as e:
#    print(f'Error: {str(e)}')

finally:
    if 'ser' in locals() and ser.is_open:  # закрытие COM-port
        ser.close()
        print("Соединение закрыто.")

    shm.close()  # Закрываем DMA
    GPIO.cleanup()  # Очистка настроек GPIO

