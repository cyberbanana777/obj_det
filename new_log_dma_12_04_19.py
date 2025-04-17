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
# 1 - правый поворот,
# 2 - левый поворот,
# 3 - объезд,
# 4 - разворот,
# 5 - поворот с объездом справа,
# 6 - поворот с объездом слева,
# 7 - проехать и остановиться
# 8 - схватить
# 9 - переставить
# 10 - переставить с грузом на борту
# 11 - корректировка маленькими поворотами
# 12 - корректировка большими поворотами

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
    limit = 0.03
    if black_objects_roi != []:

        if len(black_objects_roi) == 1:
            x_cor = black_objects_roi[0][5]
        elif len(black_objects_roi) > 1:
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
        function_to_move = 12
        function_to_grab = 0

        data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
            str(correction_speed_to_right_wheels) + ";" + \
            str(correction_speed_to_left_wheels) + ";#"

        ser.write(data_to_arduino.encode('utf-8'))
        print(f'Message sent to serial: {data_to_arduino}')
        return 1

def find_isolated_regions(matrix):
    if not matrix or len(matrix) != 11 or any(len(row) != 11 for row in matrix):
        return 0

    rows, cols = 11, 11
    count = 0
    # Создаем копию матрицы для визуализации
    visualization = [row.copy() for row in matrix]

    def dfs(i, j, marker):
        if i < 0 or i >= rows or j < 0 or j >= cols or visualization[i][j] != 1:
            return 0
        visualization[i][j] = marker  # Помечаем текущую компоненту
        size = 1  # Текущий элемент
        # 4-направленная проверка и суммируем размер
        size += dfs(i + 1, j, marker)
        size += dfs(i - 1, j, marker)
        size += dfs(i, j + 1, marker)
        size += dfs(i, j - 1, marker)
        return size

    for i in range(rows):
        for j in range(cols):
            if visualization[i][j] == 1:
                size = dfs(i, j, marker=count + 2)  # Маркеры: 2, 3, 4...
                if size > 4:
                    count += 1
    return count

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

 # если линия, то просто едем
    line_width = 200
    displaced_x = 20
    displaced_platform = 30
    platform_max_widht = 400  # поменять!!!!!
    platform_max_height = 400  # поменять!!!!
    max_sum_middle_line = 8

    if flag_simple_logic == 1:

        if line_recognize_flag == 0:
            return 'unknown'

        if width < line_width and height == 480:
            return 'line'
        elif width <= line_width and height < 260 and -50 < x < 50:
            return 'dead_end'

        # for i in platform:
        #     if id_matrix == i:
        #         return 'platform'

        found_regions = find_isolated_regions(matrix)
        
        print('DEBAG 216: found_regions',matrix, found_regions)

        if width <= platform_max_widht and height <= platform_max_height and -displaced_platform < x < displaced_platform and -90 < y < -20:
            return 'platform'
        if -displaced_platform < x < displaced_platform and -90 < y < -20 and width > line_width and found_regions == 1:
            return 'platform'

        sum_middle_line_matrix = 0
        for el in matrix[3]:
            sum_middle_line_matrix += el
        print('DEBAG: sum_middle_line', sum_middle_line_matrix)

        if width > line_width and x < -displaced_x and sum_middle_line_matrix < max_sum_middle_line:
            if found_regions == 2:
                return 'left_turn'
            elif found_regions == 3:
                return 'left_E_crossroad'
            else:
                return 'left_turn'
        elif width > line_width and x > displaced_x and sum_middle_line_matrix < max_sum_middle_line:
            if found_regions == 2:
                return 'right_turn'
            elif found_regions == 3:
                return 'right_E_crossroad'
            else:
                return 'right_turn'
        elif sum_middle_line_matrix <= max_sum_middle_line and width > line_width:
            if found_regions == 3:
                return 'T_crossroad'
            if found_regions == 4:
                return 'X_crossroad'
            else:
                return 'right_turn'
        else:
            return 'unknown'

def way_function(shape, color, do_color):
    function_to_move = 0
    function_to_grab = 0
    # if color == 'Green' and do_color:
    #     # function_to_move = 8
    #     pass
    # elif ciolor == 'Blue' and do_color:
    #     # function_to_move = 9
    #     pass
    # elif color == 'Red' and shape == 'dead_end':
    #     function_to_move = 3
    # elif color == 'Red' and shape == 'right_turn':
    #     function_to_move = 5
    # elif color == 'Red' and shape == 'left_turn':
    #     function_to_move = 6
    # elif color == 'Red' and shape == 'right_T_crossroad':
    #     function_to_move = 1
    if shape == 'platform' and color != 'Green':
        function_to_move = 7
        platform_flag = 1
    elif shape == 'dead_end':
        function_to_move = 4
    elif shape == 'right_turn':
        function_to_move = 1
    elif shape == 'left_turn':
        function_to_move = 2
    elif shape == 'right_E_crossroad':
        function_to_move = 1
    elif shape == 'left_E_crossroad':
        function_to_move = 2
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

    # print("DEBAG: data from dma:", line)

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
platform_flag = 0

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
            platform_flag = 0
            print('Ожидание сигнала...\n')

        if input_state == GPIO.HIGH and state_flag == 0 and platform_flag == 0:
            while True:

                start_time = time.time()

                input_state = GPIO.input(17)
                if input_state == GPIO.LOW or platform_flag == 1:
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

                        if test_flag == 1:
                            corect_flag = 0  # change with debug
                            mess_flag = 0  # change with debug

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

                if test_flag == 1:
                    time.sleep(1)
                else:
                    time.sleep(0.05)  # 0.05

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
