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
import time

# разрешение 640 х 480

# time.sleep(20)


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
# массив сохраняющий путь пройденный роботом

black_objects_roi = []
color_objects_central = []
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
        if norm_x > 0.15:
            corect_flag = 1

    Kp = 1.0
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

# прописать функции!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


def recognize_shape(id_matrix):

    dead_end = ['1111111111110111101111011', '1111111111111111111111111', '1111111111111111110111001', '1111111111111111101111011', '1111111111111111011110111', '1111111111111011110111101', '1111111111101111011110111', '1111111111111111110111101']

    platform = ['1111111011100111001111011', '1111010111000111001110111', '1111111011100111000111011', '1111111001110011100111101', '1111010011000111001110111', '1111111011100011001111011', '1111010011100111001110111', '1111111011100011000111011', '1111000110001110011110111', '1111010011100111001111111', '1111111101110001100011101', '1111000110000111011110111', '1111111011100011101111011', '1111111111100111001110011', '1111111011110011100111011', '1111010010000111011110111', '1111111001110011100111001', '1111111001110011100111011', '1111111011100011100111011', '1111111001100011100111011', '1111111111100111001111011', '1111110011100111001111011', '1111000110001111011110111', '1111000110000100011110111', '1111110011100111101111011', '1111010110000110011110111', '1111110011100011101111011', '1111110011100111001111111', '1111111001100011101111011', '1111010011100111001111011', '1111111101110011100111101', '1111111001110011100111011', '1111111001110001100011101', '1111111001110011100111101', '1111111101110001100011101', '1111111101110001110011101', '1111111001110011100111101', '1111111001100011101111011', 0, '1111111001110011100111011', '1111111011100011100111011', '1111111011110011000111011', '1111010011100111001111011', '1111111011100011001111011', '1111111011100011000111011', '1111111011100011101111011', '1111111001100011100111011', '1111111001110011100011101', '1111111001110001100011101', '1111010011100111001111111']

    left_turn = ['1111111111001111101110011', '1111111111001111011110111', '1111111111000111111111001', '1111100111110011101111011', '1111100111110011100111001', '1111111111001111001110011', '1111110111000111101111011', '1111100011110011110111001', '1111100111000111101111011', '1111111111000111101110011', '1111111111100011110111101', '1111111111001111011110011', '1111100111110011110111001', '1111100111100111101111011', '1111101111100011110111101', '1111111111000111101111011', '1111100011110111101111011', '1111111111001111101111011', '1111111111000111110111001', '1111011111001111011110111', '1111100111110111101111011']
    
    right_turn = ['1111111111110001111111011', '1111111100110101101111011', '1111111000110101101111011', '0111111111111001110111101', '1111111111111001110111101', '0000001100110001101011000', '0111111111111001100111001', '1111111111110001111110011', '1111111100111001101111011', '0111101111111001110111101', '1111111000110001101110011', '0111111111110001101111011', '0111111100111001110111001', '1111111000110101011110111', '1111111111110001011110111', '1111111110100001011110111', '1111111111110001101110011', '0111111100111001110111101', '1111111111111001101111011', '1111111000110111101111011', '1111111000110111101110011', '1111111101110101101111011', '0111111100111001100111001', '1111111111110001101111011', '0111111111111001101111011', '1111111100110001101111011', '1111111111110001111110111', '1111111111100001011110111', '1111111111110001011110011', '1111111100110111101111011', '1111111110110001101111011', '0111111111111001110111001', '1111111000110101011110011']


    right_E_crossroad = ['1011110111100001011110111', '1011110100100001011110111', '1101111111110001111110011', '1111111000110001101111011', '1101111011110001111110111', '1011111000110001101110011', '1011110110101111011110111', '1011111111110001101111011', '1011111111110001111110111', '1101111000110011101111011', '1111111111110001011110111', '1101111111110001011110111', '1101111011110001011110111', '1101111011110001111110011', '1101111011110001101111011', '1101111011110001101110111', '1101111000110001101111011', '1011110110100001011110111', '1011110100101111011110111', '1111111011110001101111011', '1011111111110001011110111', '1101111010110001101111011', '1101111111110001111110111', '1111111111110001101111011', '1101111011110001101110011', '1011111000110001101111011', '1110111011110001101111011', '1111111011100001011110111', '1011111011110001011110011', '1011110100100111011110111', '1011110110100011011110111', '1101111011110001101011011']

    left_E_crossroad = ['1110111101000011110111101', '1110111101000111111111001', '1001111011000111101111011', '1101100011010111101111011', '1110111101100111111111011', '1001110111001111101111011', '1011111111001111101111011', '1110111011000111101111011', '1101110111001111111110111', '1100111001000111101111011', '1110111111000111101111011', '1101111011000111111110011', '1011111011000111101111011', '1001111111001111111110011', '1001100011000111101111011', '1101111011000111101111011', '1001111111001111111111011', '1011110111001111011110011', '1011110111001111101111011', '1110101001100111101111011', '1011110111001111011110111', '1100101011100111101111011', '1100111011000111111111001', '1101111011000111101110011', '1101101011100111101111011', '1110111101100011111111011', '1001110011000111101110011', '1101111011010111101111011', '1011111111000111101111011', '1001110111001111011110111', '1110111101000111111111011', '1100111011000111101111011', '1001110011001111101110011', '1011110111001111111110011', '1001110111001111011110011', '1011110111001111111111011', '1100111111000111101111011', '1101110011000111101111011', '1101100011110111101111011', '1101111111001111011110111', '1001110011000111101111011', '1001110111000111101111011', '1110101011100111101111011', '1001110011001111111110011', '1110111101000111101111011', '1100111111000111111111001', '1101111011100111101111011', '1101110011001111111110111', '1101111011001111101111011', '1101111011000111111111011', '1101111011001111111111011', '1100111111000111111111011', '1100111011000111101111001']

    T_crossroad = ['1111111100000011101111011', '1111100111110001101110111', '1111101111100001111110111', '1111111000000111011110111', '1111111111100001110111001', '1111111111000001101111011', '1111111100000111111111011', '1111101111100001110111011', '1111111111000001110111001', '1111111000000111011111011', '1111111000001111011110111', '1111101111110001101111011', '1111111100000001111111011', '1111111110000001101111011', '1111111111100001101111011', '1111111111000001111111011', '1111111110000001011110111', '1111101111100001101111011', '1111100111100001101110111', '1111111111000001111110111', '1111111100000001101111011', '1111111100000111101111011', '1111111110000001111111011', '1111101111100001101110111', '1111101111100001101011011', '1111101111000001101111011', '1111111111000001011110111', '1111100111110001101111011', '1111101111100001110111001', '1111111111000001111111001', '1111111000000111111111011', '1111111111000001101110111', '1111111100000011011110111']

    X_crossroad = ['1101111010000111101111011', '1110111101000011100011011', '1111111111000001111111011', '1101101011110001101111011', '1101111011000001111111001', '1101111111000001101111011', '1011110111000001111111011', '1110111101000001110111001', '1110111011000011101011011', '1110111101000001100011011', '1110111101000001111111011', '1110111111000001111111011', '1101111011000001110111101', '1101111011000011101011011', '1011111111000001111111011', '1110111101000011110011101', '1101111010000011101111011', '1101111011000001101011011', '1110111111000011101011011', '1011110000000111101111011', '1110111111000001100011011', '1110111101100001111111011', '1110111101100001110111001', '1110111111000001111111001', '1101111011000001111111111', '1011111111000001011110111', '1101111011000001111110111', '1110101101100001110111101', '1101111111000001111111111', '1101111011110001101111011', '1110111101100001110111101', '1101111011100001101111011', '1101111111000001111111011', '1110111101000001110111101', '1101111011000001111111011', '1101111011000001101111011', '1101111010000001101111011', '1110111101000011110011011', '1011111000000111101111011', '1111111111000001011110111', '1111111111000001111111111', '1101111111000001111110111', '1110111111000001101111011', '1011110111000001011110111', '1101111011000001111111101', '1111111111000001101111011', '1011111111000001111110111', '1101110000010111101111011']

 
    shape = 'unknown'

    for i in dead_end:
        if id_matrix == i:
            shape = 'dead_end'

    for i in platform:
        if id_matrix == i:
            shape = 'platform'

    for i in right_E_crossroad:
        if id_matrix == i:
            shape = 'right_E_crossroad'

    for i in left_E_crossroad:
        if id_matrix == i:
            shape = 'left_E_crossroad'

    for i in T_crossroad:
        if id_matrix == i:
            shape = 'T_crossroad'

    for i in X_crossroad:
        if id_matrix == i:
            shape = 'X_crossroad'

    for i in right_turn:
        if id_matrix == i:
            shape = 'right_turn'

    for i in left_turn:
        if id_matrix == i:
            shape = 'left_turn'

    return shape
 


def way_function(shape, color, do_color):
    function_to_move = 0
    function_to_grab = 0
    if color == 'Green' and do_color:
        # function_to_grab = 1
        pass
    elif color == 'Blue' and do_color:
        # function_to_grab = 2
        pass
    elif color == 'Red' and shape == 'dead_end':
        function_to_move = 3
    elif color == 'Red' and shape == 'right_turn':
        function_to_move = 5
    elif color == 'Red' and shape == 'left_turn':
        function_to_move = 6
    elif color == 'Red' and shape == 'right_T_crossroad':
        function_to_move = 1
    elif shape == 'platform' and color != 'Green':
        function_to_move = 7
    elif shape == 'dead_end':
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


def read_fifo():
    global id_matrix

    lines = fifo.readlines()
    if len(lines) > 1:
        line = lines[-1]
    else:
        line = []

    if len(line) != 0:
        now = line.split(";")
        now.pop()
        l = 0
        k_roi = 0
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
            else:
                color_objects.append([first] + [float(j) for j in obj])
                color_objects[l][4] = -color_objects[l][4] + 240
                color_objects[l][3] = color_objects[l][3] - 320
                l += 1


fifo_path = 'fifo'
fifo = open(fifo_path, 'r')

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

shape = 0
time_send_messege = 0

start_time = 0
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
                matrix = []
                id_matrix = 0
                color = 0
                shape = 0

                print('Corect_flag:', corect_flag)
                print('Wait_flag:', wait_flag)

                # получение данных с камеры
                read_fifo()
                print('Black_objects_roi:', black_objects_roi)
                print('Color_objects:', color_objects)
                time.sleep(0.07)

                print('Id_matrix:', id_matrix)
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
                        shape = recognize_shape(id_matrix)
                    print(f'Shape: {shape}')

                    if (shape != 0 and shape != 'unknown') or color != 0:
                        corect_flag = 1
                        mess_flag = 1

                # корректировка положения макленькими поворотами
                if corect_flag == 1 and wait_flag == 0:
                    corect_flag = corection_way()

                # отправка сообщения на ардуино
                if corect_flag == 0 and wait_flag == 0 and mess_flag == 1:

                    shape = recognize_shape(id_matrix)
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
                elif corect_flag == 0 and wait_flag == 0 and mess_flag == 0:

                    # ПДи
                    if black_objects_roi != []:
                        correction_speed_to_right_wheels, correction_speed_to_left_wheels = go_to_line(
                            black_objects_roi)

                    data_to_arduino = "$" + str(0) + ";" + str(0) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))
                    print(f'Message sent to serial: {data_to_arduino}')

                if (data_from_arduino == 'OK' or time.time() - time_send_messege > 60) and wait_flag == 1:
                    corect_flag = 1
                    wait_flag = 0

                time.sleep(0.05)
                print('Time:', time.time() - start_time)
                print('')

                # конец блока логики ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬


except KeyboardInterrupt:
    print("Прерывание программы. Закрытие порта...")
    print(list(set_mus))

# except Exception as e:
#    print(f'Error: {str(e)}')

finally:
    if 'ser' in locals() and ser.is_open:  # закрытие COM-port
        ser.close()
        print("Соединение закрыто.")

    fifo.close()  # Закрываем FIFO
    GPIO.cleanup()  # Очистка настроек GPIO

