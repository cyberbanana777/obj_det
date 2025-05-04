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

# выбор логики прохлждеия лабиринта
flag_right_turn_logic = 0
flag_case_logic = 1

function_to_move = 0
function_to_grab = 0  # 1 - схватить, 2 - переставить, 3 - переставить с грузом на борту
correction_speed_to_right_wheels = 0
correction_speed_to_left_wheels = 0
# на каком расстояни роботот должен остановиться, что бы схватить цилиндр с небольшим допуском, поменять!
max_distance_for_color_obj = 40
# Для ПДа
pred_norm_x = 0
# обновляющиеся массивы объектов
black_objects_roi = []
color_objects = []
black_objects = []
matrix = []
id_matrix = ''
DEMENTION = 15
WAIT_TIME = 4
pred_shape = 0

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
    if norm_x > 0.05:
        corect_flag = 1

    Kp = 1.8
    Kd = 0.2
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


def corection_way_center(demention, max_sum_row, matrix):
    global function_to_move
    global wait_flag
    full_row = -1
    central_row = demention//2

    for i in range(demention):
        count = 0
        for el in range(demention):
            count += matrix[i][el]
        print(count)
        if count <= max_sum_row:
            full_row = i

    print('DEBAG 122 full_row:', full_row)

    if full_row >= 0 and full_row != central_row:
        if full_row > central_row:
            function_to_move = 13
        elif full_row < central_row:
            function_to_move = 14

        correction_speed_to_right_wheels = 0
        correction_speed_to_left_wheels = 0
        function_to_grab = 0

        data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
            str(correction_speed_to_right_wheels) + ";" + \
            str(correction_speed_to_left_wheels) + ";#"

        ser.write(data_to_arduino.encode('utf-8'))
        wait_flag = 1
        print(f'Message sent to serial: {data_to_arduino}')
        return 1
    elif full_row == -1 or full_row == central_row:
        return 0
    else:
        return 0


def corection_way():
    global pred_norm_x_roi
    global wait_flag
    limit = 0.05

    if color == 'Green':
        objects = color_objects
        limit = 0.02
    else:
        objects = black_objects_roi

    if objects != []:

        if len(objects) == 1:
            x_cor = objects[0][5]
        elif len(objects) > 1:
            obj = min(objects, key=lambda x: (x[3])**2 + (x[4])**2)
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
            wait_flag = 1
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
        wait_flag = 1
        print(f'Message sent to serial: {data_to_arduino}')
        return 1


def find_isolated_regions(matrix, demention):
    if not matrix or len(matrix) != demention or any(len(row) != demention for row in matrix):
        return 0

    rows, cols = demention, demention
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
    max_sum_middle_line = 3

    if flag_simple_logic == 1:

        if line_recognize_flag == 0:
            return 'unknown'

        if width < line_width and height == 480:
            return 'line'
        elif width <= line_width and height < 280 and -50 < x < 50:
            return 'dead_end'

        # for i in platform:
        #     if id_matrix == i:
        #         return 'platform'

        found_regions = find_isolated_regions(matrix, DEMENTION)

        print('DEBAG 216: found_regions', matrix, found_regions)

        if line_width < width <= platform_max_widht and height <= platform_max_height and -displaced_platform < x < displaced_platform and -90 < y < -20:
            return 'platform'
        if 640 > width > line_width and 480 > height > 300 and found_regions == 1:
            return 'platform'

        sum_4_line_matrix = 0
        sum_3_line_matrix = 0
        line_matrix = True
        # for el in matrix[3]:
        #    sum_4_line_matrix += el
        # print('DEBAG: sum_4_line', sum_4_line_matrix)
        # for el in matrix[4]:
        #    sum_3_line_matrix += el
        # print('DEBAG: sum_3_line', sum_3_line_matrix)
        # if sum_3_line_matrix < 4 or sum_4_line_matrix < 4:
        #    line_matrix = True

        if width > line_width and x < -displaced_x and line_matrix == True:
            print('letf')
            if found_regions == 2 and height < 480:
                return 'left_turn'
            elif found_regions == 3:
                return 'left_E_crossroad'
            else:
                return 'unknown'
        elif width > line_width and x > displaced_x and line_matrix == True:
            print('right')
            if found_regions == 2 and height < 480:
                return 'right_turn'
            elif found_regions == 3:
                return 'right_E_crossroad'
            else:
                return 'unknown'
        elif line_matrix == True and width > line_width:
            print('center')
            if found_regions == 3 and height < 480:
                return 'T_crossroad'
            if found_regions == 4:
                return 'X_crossroad'
            else:
                return 'unknow'
        else:
            return 'unknown'


count_right_E_crossroad = 0


def way_function(shape, color, do_color):
    global platform_flag
    global flag_way_to_finish
    global flag_way_with_green
    global count_right_E_crossroad
    global flag_way_with_green
    global pred_shape
    function_to_move = 0
    function_to_grab = 0

    if flag_right_turn_logic == 1:

        if color == 'Green':
            function_to_move = 8
        #     pass
        # elif ciolor == 'Blue' and do_color:
        #     # function_to_move = 9
        #     pass
        elif color == 'Red':
            function_to_move = 5
        # elif color == 'Red' and shape == 'right_turn':
        #     function_to_move = 5
        # elif color == 'Red' and shape == 'left_turn':
        #     function_to_move = 6
        # elif color == 'Red' and shape == 'right_T_crossroad':
        #     function_to_move = 1
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
            # pass
        elif shape == 'left_E_crossroad':
            function_to_move = 2
            #pass
        elif shape == 'T_crossroad':
            function_to_move = 1
        elif shape == 'X_crossroad':
            # function_to_move = 1
            pass

    if flag_case_logic == 1:
        print('Flag_to_finish:', flag_way_to_finish)
        print('Flag_with_green:', flag_way_with_green)


        if color == 'Green':
            function_to_move = 8
            flag_way_to_finish = 0
            flag_way_with_green = 1
            count_right_E_crossroad = 0
        elif color == 'Red':
            if flag_way_to_finish == 1:
                function_to_move = 6
            if flag_way_with_green == 1:
                function_to_move = 5
            pass
        elif shape == 'platform' and color != 'Green':
            function_to_move = 7
        elif shape == 'dead_end':
            function_to_move = 4
        elif shape == 'right_turn':
            function_to_move = 1
        elif shape == 'left_turn':
            function_to_move = 2
        elif shape == 'right_E_crossroad':
            if flag_way_to_finish == 1:
                print('Pred_shape:', pred_shape)
                print('^^^Count_right_E_crossroad:', count_right_E_crossroad)
                
                if pred_shape != 'right_E_crossroad':
                    count_right_E_crossroad += 1
                if count_right_E_crossroad == 2:
                    function_to_move = 1
        
            if flag_way_with_green == 1:
                function_to_move = 1
            pass
        elif shape == 'left_E_crossroad':
            if flag_way_with_green == 1:
                function_to_move = 2
            pass
        elif shape == 'T_crossroad':
            if flag_way_with_green == 1:
                function_to_move = 2
            pass
        elif shape == 'X_crossroad':
            # function_to_move = 1
            pass

    return function_to_move, function_to_grab


def recognize_color(color_objects):
    if len(color_objects) == 0:
        return 0
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
                k_black, 'new_el:', [first] + [float(j) for j in obj]
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
# set_mus = set()
mes_time = 0
mes_delay = 0
wait_time = WAIT_TIME

count_crosses = 0
count_E_crosses = 0
count_T_crosses = 0
count_X_crosses = 0

flag_back = 0
state_flag = 0
count = 0
platform_flag = 0
platform_pred_flag = 0

corect_flag = 0
corect_flag_center = 0
wait_flag = 0
mess_flag = 0
test_flag = 0  # !!!!!!!!!!!!!!!!!!!!! TEST !!!!!!!!!!!!!!!!!!!!

shape = 0
time_send_messege = 0
min_time = 0.5

start_time = 0
count_print = 0

flag_way_to_finish = 1
flag_way_with_green = 0
platform_time = 0
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
            platform_pred_flag = 0
            flag_way_to_finish = 1
            flag_way_with_green = 0
            count_right_E_crossroad = 0
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
                print('Mess_flag:', mess_flag)
                print('Corect_flag_center', corect_flag_center)

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

                # set_mus.add(id_matrix)

                # получение сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
                if ser.in_waiting > 0:
                    data_from_arduino = ser.readline()
                    try:
                        data_from_arduino = data_from_arduino.decode(
                        'utf-8').strip()
                        print(f'Message get from serial: {data_from_arduino}')
                    except Exception as e:
                        print('Error arduino messege:', e)    
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

                print("DO_COLOR:", do_color)

                # конец блок получения сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬

                # блок логики ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬

                # Распознование формы и цвета
                if corect_flag == 0 and corect_flag_center == 0 and wait_flag == 0:
                    if color_objects != []:
                        color = recognize_color(color_objects)
                    print(f'Color: {color}')

                    if id_matrix != 0:
                        shape = recognize_shape(
                            id_matrix, black_objects, matrix)

                    print(f'Shape: {shape}')

                    if (shape != 0 and shape != 'unknown' and shape != 'line') or (color != 0):
                        corect_flag = 1
                        corect_flag_center = 1
                        if shape == 'dead_end' or color == 'Green' or color == 'Red':
                            corect_flag_center = 0
                            print('MARCK!')

                        mess_flag = 1

                        if test_flag == 1:
                            corect_flag = 0  # change with debug
                            mess_flag = 0  # change with debug
                            corect_flag_center = 0

                # корректировка положения макленькими шажками
                if corect_flag_center == 1 and wait_flag == 0 and test_flag == 0 and len(matrix) != 0:
                    corect_flag_center = corection_way_center(
                        DEMENTION, DEMENTION//2 + 1, matrix)

                # корректировка положения макленькими поворотами
                if corect_flag == 1 and wait_flag == 0 and test_flag == 0:
                   corect_flag = corection_way()
                

                # отправка сообщения на ардуино
                if corect_flag == 0 and corect_flag_center == 0 and wait_flag == 0 and mess_flag == 1 and test_flag == 0:

                    shape = recognize_shape(id_matrix, black_objects, matrix)
                    print('Shape:', shape)
                    color = recognize_color(color_objects)
                    print('Color:', color)
                    function_to_move, function_to_grab = way_function(shape, color, do_color)
                    
                    pred_shape = shape

                    if do_color == 0 and color != 0:
                        function_to_move = 0

                    

                    data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))

                    print(f'Message sent to serial: {data_to_arduino}')
                    #time.sleep(0.05)

                    time_send_messege = time.time()

                    if function_to_move == 0 and color != 0:
                        wait_time = 0.2
                        min_time = 0.2
                    elif function_to_move == 0:
                        wait_time = 2
                        min_time = 0.5
                    elif function_to_move == 8:
                        wait_time = 15
                    elif function_to_move == 7:
                        platform_pred_flag = 1
                        min_time= 0.5
                        wait_time = 8
                        platform_time = time.time()
                    elif function_to_move == 4:
                        wait_time = 3
                    elif function_to_move == 11 or function_to_move == 12 or function_to_move == 13 or function_to_move == 14:
                        wait_time = 0.5
                    else:
                        min_time = 0.5
                        wait_time = WAIT_TIME

                    wait_flag = 1
                    mess_flag = 0
                elif corect_flag == 0 and corect_flag_center == 0 and wait_flag == 0 and mess_flag == 0 and test_flag == 0:

                    # ПДи
                    if black_objects_roi != []:
                        correction_speed_to_right_wheels, correction_speed_to_left_wheels = go_to_line(
                            black_objects_roi)

                    data_to_arduino = "$" + str(0) + ";" + str(0) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))
                    print(f'Message sent to serial: {data_to_arduino}')

                if ((time.time() - time_send_messege > min_time and data_from_arduino == 'OK') or (time.time() - time_send_messege >= wait_time)) and wait_flag == 1 and test_flag == 0:
                    corect_flag = 1
                    wait_flag = 0

                if test_flag == 1:
                    time.sleep(1)
                else:
                    time.sleep(0.07)  # 0.05

                if time.time() - platform_time >= 10 and platform_pred_flag == 1:
                    platform_flag = 1

                print('###Flag_to_finish:', flag_way_to_finish)
                print('###Flag_with_green:', flag_way_with_green)
                print('Flag_case_logic', flag_case_logic)
                print('Pred_platfom', platform_pred_flag)
                print('Platform_flag', platform_flag)
                print('Time:', time.time() - start_time)
                print('')
                print('Corect_flag:', corect_flag)
                print('Wait_flag:', wait_flag)
                print('WAIT_TIME:', wait_time)
                print('Time_from_messege:', round(
                    time.time() - time_send_messege, 4))
                print('Mess_flag:', mess_flag)
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

