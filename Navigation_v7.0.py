'''
АННОТАЦИЯ

Последний актуальный скрипт.

Описание:
    На ардуино отсылается то, что должно. Всё остальное работает в штатном режиме, добавлены все константы

Настроить:
    Коэффициенты  "PID'a"

Осталось:
    Добавить цикл, связанный с gpio
    Событие достижения конца пути

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
black_objects = []
black_objects_roi = []
color_objects_central = []
main_way = []

# считывает скорость для моторов


def go_to_line(black_objects_roi):
    global pred_norm_x, correction_speed_to_left_wheels, correction_speed_to_right_wheels
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

    Kp = 1.0
    Kd = 0.3
    if width < 150:
        if (norm_x > 0 and pred_norm_x < 0) or (norm_x < 0 and pred_norm_x > 0):
            pred_norm_x = 0

        if x > 0:
            correction_speed_to_left_wheels = round(norm_x * Kp - (pred_norm_x - norm_x) * Kd, 3)
        if x < 0:
            n_norm_x = abs(norm_x)
            pred_norm_x = abs(pred_norm_x)
            correction_speed_to_right_wheels = round(n_norm_x * Kp - (pred_norm_x - norm_x) * Kd, 3)

    pred_norm_x = norm_x

# распознавание элемента лабиринта


def recognize_shape(black_objects, black_objects_central):

    if len(black_objects) == 1:
        width = black_objects[0][1]
        height = black_objects[0][2]
        x = black_objects[0][3]
        y = black_objects[0][4]
        x_norm = black_objects[0][5]
    else:
        obj = min(black_objects, key=lambda x: (x[3])**2 + (x[4])**2)
        width = obj[1]
        height = obj[2]
        x = obj[3]
        y = obj[4]
        x_norm = obj[5]

    if len(black_objects_central) > 0:

        if len(black_objects_central) == 1:
            width_central = black_objects_central[0][1]
            height_central = black_objects_central[0][2]
            x_central = black_objects_central[0][3]
            y_central = black_objects_central[0][4]
        else:
            obj_central = min(black_objects_central, key=lambda x: (x[3])**2 + (x[4])**2)
            width_central = obj_central[1]
            height_central = obj_central[2]
            x_central = obj_central[3]
            y_central = obj_central[4]
    else:
        width_central = 0 

# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    corect = 30

    max_width_dead_end = 127 + corect  # максимальная ширина тупика!
    max_height_dead_end = 254 + corect  # максимальная высота тупика!
    x_dead_end = 0
    y_dead_end = -115

    max_width_line = 127 + corect  # максимальная ширина линии! продолжается
    max_height_line = 480  # максимальная высота линии! продолжается
    x_line = 0
    y_line = 0

    max_width_platform = 465 + corect  # максимальная ширина платформы!
    max_height_platform = 425 + corect  # максимальная высота платформы!
    x_platform = 0
    y_platform = -30  

    max_width_turn = 400 + corect  # максимальная ширина поворота!
    max_height_turn = 325 + corect  # максимальная высота поворота!
    x_right_turn = 125
    y_right_turn = -87
    x_left_turn = -130
    y_left_turn = -87

    # максимальная ширина Е-образного перекрестка! продолжается
    max_width_E_crossroad = 390 + corect
    max_height_E_crossroad = 480 + corect # максимальная высота Е-образного перекрестка! продолжается
    x_right_E_crossroad = 125
    y_right_E_crossroad = 0
    x_left_E_crossroad = -130
    y_left_E_crossroad = 0

    max_width_T_crossroad = 640  # максимальная ширина Т-образного перекрестка!
    max_height_T_crossroad = 305 + corect  #
    x_T_crossroad = 0
    y_T_crossroad = -90

    max_width_X_crossroad = 640  # максимальная ширина перекрестка! продолжается
    max_height_X_crossroad = 480  # максимальная высота перекрестка! продолжается
    x_X_crossroad = 0
    y_X_crossroad = 0
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    mistake_x = 60  # число 10 - эксперементальное, изменить!
    mistake = 30
   
    if 100 < width <= max_width_dead_end and 100 < height <= max_height_dead_end:
        # тупик - разворот
        if (x_dead_end + mistake_x > x > x_dead_end - mistake_x and y_dead_end + mistake > y > y_dead_end - mistake) or width_central == 0:
            return 'dead_end', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_line and height == 480:
        # линия - выравнивание
        if y_line + mistake > y > y_line - mistake:
            return 'line', ['Black', width, height, x, y, x_norm]
    elif width < 640 and height < 480 and width_central > max_width_line and width_central != 0:      
        # поворот
        # x < 0 - поворот налево
        # x > 0 - поврот направо
        if x > 0:
            #if x_right_turn + mistake_x > x > x_right_turn - mistake_x and y_right_turn + mistake > y > y_right_turn - mistake:
            return 'right_turn', ['Black', width, height, x, y, x_norm]
        elif x < 0:
            #if x_left_turn + mistake_x > x > x_left_turn - mistake_x and y_left_turn + mistake > y > y_left_turn - mistake:
            return 'left_turn', ['Black', width, height, x, y, x_norm]
    elif 300 < width < max_width_platform and height < max_height_platform and width_central > max_width_turn:
        # платформа
        # + зеленый цилиндр - схватить
        # доехать до середины и развернуться
        if x_platform + mistake_x > x > x_platform - mistake_x and y_platform + mistake > y > y_platform - mistake:
            return 'platform', ['Black', width, height, x, y, x_norm]
    elif width < 640 and height == 480 and width_central > max_width_line and width_central != 0:
        # Е-образный перекресток
        # x < 0 - перекресток налево
        # x > 0 - перекресток направо
        if x > 0:
           # if x_right_E_crossroad + mistake_x > x > x_right_E_crossroad - mistake_x and y_right_E_crossroad + mistake > y > y_right_E_crossroad - mistake:
            return 'right_E_crossroad', ['Black', width, height, x, y, x_norm]
        elif x < 0:
            #if x_left_E_crossroad + mistake_x > x > x_left_E_crossroad - mistake_x and y_left_E_crossroad + mistake > y > y_left_E_crossroad - mistake:
            return 'left_E_crossroad', ['Black', width, height, x, y, x_norm]
    elif width == 640 and height < 480 and width_central > max_width_turn and width_central != 0:
        # Т-образный перекресток
        #if x_T_crossroad + mistake_x > x > x_T_crossroad - mistake_x and y_T_crossroad + mistake > y > y_T_crossroad - mistake:
        return 'T_crossroad', ['Black', width, height, x, y, x_norm]
    elif width == 640 and height == 480 and width_central > max_width_turn and width_central != 0:
        # перекресток
        if x_X_crossroad + mistake_x > x > x_X_crossroad - mistake_x and y_X_crossroad + mistake > y > y_X_crossroad - mistake:
            return 'X_crossroad', ['Black', width, height, x, y, x_norm]
    return 'unknown', 'unknown'

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
    lines = fifo.readlines()
    if len(lines) > 1:
        line = lines[-1]
    else:
        line = []

    if len(line) != 0:

        now = line.split(";")
        now.pop()
        l = 0
        k = 0
        k_roi = 0
        k_central = 0
        for i in now:
            obj = i.split(",")
            first = obj.pop(0)
            if first == 'Black':
                black_objects.append([first] + [float(j) for j in obj])
                black_objects[k][4] = -black_objects[k][4] + 240
                black_objects[k][3] = black_objects[k][3] - 320
                k += 1
            elif first == 'Black_roi':
                black_objects_roi.append(
                    [first] + [float(j) for j in obj])
                black_objects_roi[k_roi][4] = - \
                    black_objects_roi[k_roi][4] + 240
                black_objects_roi[k_roi][3] = black_objects_roi[k_roi][3] - 320
                k_roi += 1
            elif first == 'Black_central':
                black_objects_central.append([first] + [float(j) for j in obj])
                black_objects_central[k_central][4] = -black_objects_central[k_central][4] + 240
                black_objects_central[k_central][3] = black_objects_central[k_central][3] - 320
                k_central += 1
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

mes_time = 0
mes_delay = 0

count_crosses = 0
count_E_crosses = 0
count_T_crosses = 0
count_X_crosses = 0

flag_back = 0
pred_shape = 0

state_flag = 0
count = 0

corect_flag = 0

stop_timer = time.time()

pred_move = 0

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
                black_objects = []
                black_objects_roi = []
                black_objects_central = []  
                color_objects = []

                # получение данных с камеры
                read_fifo()
                print('Color_object:', color_objects)
                print('Black_object:', black_objects)
                print('Black_object_roi:', black_objects_roi)
                print('Black_object_central:', black_objects_central)
                time.sleep(0.07)

                # получение сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
                if ser.in_waiting > 0:
                    data_from_arduino = ser.readline()
                    data_from_arduino = data_from_arduino.decode(
                        'utf-8').strip()
                    print(f'Message get from serial: {data_from_arduino}')

                else:
                    print('No data from Arduino')
                    data_from_arduino = 10000

                serilal_data = 0

                if ser.in_waiting > 0:
                    serial_data = ser.in_waiting
                    print('Were still data', serial_data)
                    r = ser.read_all()

                # конец блок получения сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬

                # блок логики ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
                
                if black_objects_roi != []:
                    go_to_line(black_objects_roi)

                if black_objects != []:
                    shape, discription = recognize_shape(black_objects, black_objects_central)
                else:
                    shape = 0
                print(f'Shape: {shape}')

                if color_objects != []:
                    color = recognize_color(color_objects)
                else:
                    color = 0
                print(f'Color: {color}')

                if black_objects != [] or color_objects != []:

                    try:
                        if 0 < float(data_from_arduino) <= max_distance_for_color_obj:
                            do_color = 1
                        else:
                            do_color = 0
                    except ValueError:
                        print('Uncorrect messege')

        # Логика под кейс

                    if color == 'Green' and do_color:
                        function_to_grab = 1
                        flag_back = 1
                        count_E_crosses = 0
                        count_T_crosses = 0
                        count_X_crosses = 0
                    elif color == 'Blue' and do_color:
                        if flag_back == 0:
                            function_to_grab = 2
                        if flag_back == 1:
                            function_to_grab = 3
                    elif color == 'Red' and (shape == 'dead_end' or shape == 'line'):
                        function_to_move = 3
                    elif shape == 'platform' and color != 'Green':
                        function_to_move = 7
                        state_flag = 1
                        count = 1
                        break
                    elif shape == 'dead_end':
                        function_to_move = 4
                    elif shape == 'right_turn':
                        function_to_move = 1
                    elif shape == 'left_turn':
                        function_to_move = 2
                    elif shape == 'right_E_crossroad':
                        if pred_shape != 'right_E_crossroad':
                            count_E_crosses += 1
                        if flag_back == 0 and count_E_crosses == 2:
                            function_to_move = 1
                    elif shape == 'left_E_crossroad':
                        pass
                    elif shape == 'T_crossroad':
                        if pred_shape != 'T_crossroad':
                            count_T_crosses += 1
                        if flag_back == 1 and count_T_crosses == 1:
                            function_to_move = 1
                        elif flag_back == 1 and count_T_crosses == 2:
                            function_to_move = 2
                    elif shape == 'X_crossroad':
                        if pred_shape != 'X_crossroad':
                            count_X_crosses += 1
                        if flag_back == 1 and count_X_crosses == 1:
                            function_to_move = 2

                    print('pred_move', pred_move)

                    pred_shape = shape
                    if (pred_move == 1 or pred_move == 2) and black_objects == []:
                        function_to_move = pred_move * 10
                        corect_flag = 0

                    if function_to_move != 0 and function_to_move != 11:
                        pred_move = function_to_move    
                    
                    
                        

        # Универсальная логика
                    # if color == 'Green' and do_color:
                    #     function_to_grab = 1
                    # elif color == 'Blue' and do_color:
                    #     function_to_grab = 2
                    # elif color == 'Red' and shape == 'dead_end':
                    #     function_to_move = 3
                    #     main_way.append(3)
                    # elif color == 'Red' and shape == 'right_turn':
                    #     function_to_move = 5
                    #     main_way.append(5)
                    # elif color == 'Red' and shape == 'left_turn':
                    #     function_to_move = 6
                    #     main_way.append(6)
                    # elif color == 'Red' and shape == 'right_T_crossroad':
                    #     function_to_move = 1
                    #     main_way.append(1)
                    # elif shape == 'platform' and color != 'Green':
                    #     function_to_move = 7
                    #     main_way.append(7)
                    # elif shape == 'dead_end':
                    #     function_to_move = 4
                    #     main_way.append(4)
                    # elif shape == 'right_turn':
                    #     function_to_move = 1
                    #     main_way.append(1)
                    # elif shape == 'left_turn':
                    #     function_to_move = 2
                    #     main_way.append(2)
                    # elif shape == 'right_E_crossroad':
                    #     function_to_move = 1
                    #     main_way.append(1)
                    # elif shape == 'left_E_crossroad':
                    #     pass
                    # elif shape == 'T_crossroad':
                    #     function_to_move = 1
                    #     main_way.append(1)
                    # elif shape == 'X_crossroad':
                    #     function_to_move = 1
                    #     main_way.append(1)

                # конец блока логики ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬

                # отправка на ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
                limit = 0.04
                print('correction_flag:', corect_flag)

                if time.time() - mes_time < mes_delay:
                    function_to_move = 0
                    function_to_grab = 0
                    correction_speed_to_left_wheels = 0
                    correction_speed_to_right_wheels = 0

                    data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))
                    print(f'Message sent to serial: {data_to_arduino}')
                elif corect_flag == 1:
                    if black_objects_roi != []:
                        if len(black_objects_roi) == 1:
                            x_cor = black_objects_roi[0][5]
                        elif len(black_objects_roi) > 1:
                            print('FOR MISTAKE:', black_objects_roi, len(black_objects_roi))
                            obj = min(black_objects_roi, key=lambda x: (x[3])**2 + (x[4])**2)
                            x_cor = obj[5]

                        if  -limit <= x_cor <= limit:
                            corect_flag = 0
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
                        if -limit <= x_cor <= limit:
                            corect_flag = 0

                    else:
                        #corect_flag = 0
                        #if shape != 0 and shape != 'unknown' and shape != 'line':
                         #   corect_flag = 0
                        data_to_arduino = '$0;0;0;0;#'
                        ser.write(data_to_arduino.encode('utf-8'))
                            

                if corect_flag == 0:
                    
                    data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
                        str(correction_speed_to_right_wheels) + ";" + \
                        str(correction_speed_to_left_wheels) + ";#"
                    ser.write(data_to_arduino.encode('utf-8'))
                    
                    time.sleep(0.005)
                    
                    #ser.write(data_to_arduino.encode('utf-8'))
                    print(f'Message sent to serial: {data_to_arduino}')                                         

                if (function_to_move != 0 or function_to_grab != 0) and function_to_move != 11:
                    mes_delay = 2
                    mes_time = time.time()
                    corect_flag = 1

                time.sleep(0.07)

                end_time = time.time()

                code_time = end_time - start_time
                print(f'Time: {code_time:.6f} second\n')
                # конец блока отправки на ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬


except KeyboardInterrupt:
    print("Прерывание программы. Закрытие порта...")

# except Exception as e:
#    print(f'Error: {str(e)}')

finally:
    if 'ser' in locals() and ser.is_open:  # закрытие COM-port
        ser.close()
        print("Соединение закрыто.")

    fifo.close()  # Закрываем FIFO
    GPIO.cleanup()  # Очистка настроек GPIO

