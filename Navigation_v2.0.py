import serial
import time

# разрешение 640 х 480

port = '/dev/ttyUSB0'  # поменять
baudrate = 115200  # поменять
# 1 - правый поворот, 2 - левый поворот, 3 - объезд, 4 - разворот, 5 - поворот с объездом справа, 6 - поворот с объездом слева, 7 - проехать и остановиться
function_to_move = 0
function_to_grab = 0  # 1 - схватить, 2 - переставить, 3 - переставить с грузом на борту
correction_speed_to_right_wheels = 0
correction_speed_to_left_wheels = 0
# на каком расстояни роботот должен остановиться, что бы схватить цилиндр с небольшим допуском, поменять!
max_distance_for_color_obj = 0
# Для ПДа
pred_norm_x = 0
# массив сохраняющий путь пройденный роботом
black_objects = []
color_objects = []
main_way = []

# считатет скорость для моторов


def go_to_line(object_type, object_description):
    global pred_norm_x, correction_speed_to_left_wheels, correction_speed_to_right_wheels

    Kp = 0.5           # 0.01 - эксперементальное, изменить!
    Kd = 0.5
    # 0.01 - эксперементальное, изменить!
    x = object_description[3]
    norm_x = object_description[5]
    if (norm_x > 0 and pred_norm_x < 0) or (norm_x < 0 and pred_norm_x > 0):
        pred_norm_x = 0

    if object_type == 'line' or object_type == 'dead_end' or object_type == 'platform':
        if x > 0:
            correction_speed_to_left_wheels = round(
                norm_x * Kp - (pred_norm_x - norm_x) * Kd, 3)
        if x < 0:
            n_norm_x = abs(norm_x)
            pred_norm_x = abs(pred_norm_x)
            correction_speed_to_right_wheels = round(
                n_norm_x * Kp - (pred_norm_x - norm_x) * Kd, 3)

        pred_norm_x = norm_x


#max_width = 0
#max_height = 0

# распознавание элемента лабиринта


def recognize_shape(black_objects):
    global max_width, max_height
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

    #if width > max_width:
    #    max_width = width
    #if height > max_height:
    #    max_height = height
    #print('Max_width:', max_width)
    #print('Max_height:', max_height)

# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    corect = 15

    max_width_dead_end = 80 + corect  # максимальная ширина тупика!
    max_height_dead_end = 305 + corect  # максимальная высота тупика!
    x_dead_end = 0
    y_dead_end = -90  # 328

    max_width_line = 80 + corect  # максимальная ширина линии! продолжается
    # max_height_line = 480  # максимальная высота линии! продолжается
    x_line = 0
    y_line = 0

    max_width_platform = 230 + corect  # максимальная ширина платформы!
    max_height_platform = 370 + corect  # максимальная высота платформы!
    x_platform = 0
    y_platform = -55  # -54

    max_width_turn = 325 + corect  # максимальная ширина поворота!
    max_height_turn = 320 + corect  # максимальная высота поворота!
    x_right_turn = 125
    y_right_turn = -80
    x_left_turn = -125
    y_left_turn = -80

    # максимальная ширина Е-образного перекрестка! продолжается
    max_width_E_crossroad = 360 + corect
    # max_height_E_crossroad = 460 + corect # максимальная высота Е-образного перекрестка! продолжается
    x_right_E_crossroad = 125
    y_right_E_crossroad = -10
    x_left_E_crossroad = -125
    y_left_E_crossroad = -10

    max_width_T_crossroad = 640  # максимальная ширина Т-образного перекрестка!
    max_height_T_crossroad = 320 + corect  #
    x_T_crossroad = 0
    y_T_crossroad = -80

    max_width_X_crossroad = 640  # максимальная ширина перекрестка! продолжается
    max_height_X_crossroad = 480  # максимальная высота перекрестка! продолжается
    x_X_crossroad = 0
    y_X_crossroad = 0
# ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
    mistake = 30  # число 10 - эксперементальное, изменить!
    if width <= max_width_dead_end and height <= max_height_dead_end:
        # тупик - разворот
        if x_dead_end + mistake > x > x_dead_end - mistake and y_dead_end + mistake > y > y_dead_end - mistake:
            return 'dead_end', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_line and height > max_height_dead_end:
        # линия - выравнивание
        if y_line + mistake > y > y_line - mistake and x_line + mistake > x > x_line - mistake:
            return 'line', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_platform and height <= max_height_platform:
        # платформа
        # + зеленый цилиндр - схватить
        # доехать до середины и развернуться
        if x_platform + mistake > x > x_platform - mistake and y_platform + mistake > y > y_platform - mistake:
            return 'platform', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_turn and height <= max_height_turn:
        # поворот
        # x < 0 - поворот налево
        # x > 0 - поврот направо
        if x > 0:
            if x_right_turn + mistake > x > x_right_turn - mistake and y_right_turn + mistake > y > y_right_turn - mistake:
                return 'right_turn', ['Black', width, height, x, y, x_norm]
        elif x < 0:
            if x_left_turn + mistake > x > x_left_turn - mistake and y_left_turn + mistake > y > y_left_turn - mistake:
                return 'left_turn', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_E_crossroad and height > max_height_turn:
        # Е-образный перекресток
        # x < 0 - перекресток налево
        # x > 0 - перекресток направо
        if x > 0:
            if x_right_E_crossroad + mistake > x > x_right_E_crossroad - mistake and y_right_E_crossroad + mistake > y > y_right_E_crossroad - mistake:
                return 'right_E_crossroad', ['Black', width, height, x, y, x_norm]
        elif x < 0:
            if x_left_E_crossroad + mistake > x > x_left_E_crossroad - mistake and y_left_E_crossroad + mistake > y > y_left_E_crossroad - mistake:
                return 'left_E_crossroad', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_T_crossroad and height <= max_height_T_crossroad:
        # Т-образный перекресток
        if x_T_crossroad + mistake > x > x_T_crossroad - mistake and y_T_crossroad + mistake > y > y_T_crossroad - mistake:
            return 'T_crossroad', ['Black', width, height, x, y, x_norm]
    elif width <= max_width_X_crossroad and height <= max_height_X_crossroad:
        # перекресток
        if x_X_crossroad + mistake > x > x_X_crossroad - mistake and y_X_crossroad + mistake > y > y_X_crossroad - mistake:
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
        for i in now:
            obj = i.split(",")
            first = obj.pop(0)
            if first == 'Black':
                black_objects.append([first] + [float(k) for k in obj])
                black_objects[k][4] = -black_objects[k][4] + 240
                black_objects[k][3] = black_objects[k][3] - 320
                k += 1
            else:
                color_objects.append([first] + [float(k) for k in obj])
                color_objects[l][4] = -color_objects[l][4] + 240
                color_objects[l][3] = color_objects[l][3] - 320
                l += 1


fifo_path = 'color_detection_fifo'
fifo = open(fifo_path, 'r')
count_crosses = 0
count_E_crosses = 0
count_T_crosses = 0
count_X_crosses = 0

flag_back = 0
way_to = [2, 2, 3, 3, 0, 1, 1, 0, 0, 2, 3, 4, 1, 1, 0, 2, 3, 1,]
way_back = [1, 1, 1, 2, 0, 2, 4, 2, 2, 2, 1, 1, 7]
pred_shape = 0
try:
    # Открываем COM-порт
    ser = serial.Serial(port, baudrate)
    print("Соединение с Arduino установлено.")

    # Небольшая задержка для установления соединения
    time.sleep(2)

    while True:
        start_time = time.time()

        function_to_move = 0
        function_to_grab = 0
        correction_speed_to_right_wheels = 0
        correction_speed_to_left_wheels = 0
        black_objects = []
        color_objects = []

        # получение данных с камеры
        read_fifo()
        print('Color_object:', color_objects)
        print('Black_object:', black_objects)

        time.sleep(0.05)

        # получение сообщения с ардуино ¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬¬
        if ser.in_waiting > 0:
            data_from_arduino = ser.readline()
            data_from_arduino = data_from_arduino.decode('utf-8').strip()
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

        if black_objects != []:
            shape, discription = recognize_shape(black_objects)
            if shape != 'unknown':
                go_to_line(shape, discription)
        else:
            shape = 0
        print(f'Shape: {shape}')

        if color_objects != []:
            color = recognize_color(color_objects)
        else:
            color = 0
        print(f'Color: {color}')

        if black_objects != [] or color_objects != []:

            if float(data_from_arduino) <= max_distance_for_color_obj:
                do_color = 1
            else:
                do_color = 0

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

            pred_shape = shape


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

        data_to_arduino = "$" + str(function_to_move) + ";" + str(function_to_grab) + ";" + \
            str(correction_speed_to_right_wheels) + ";" + \
            str(correction_speed_to_left_wheels) + ";#"

        ser.write(data_to_arduino.encode('utf-8'))
        print(f'Message sent to serial: {data_to_arduino}')
        print('')
        time.sleep(0.2)

        end_time = time.time()

        code_time = end_time - start_time
        print(f'Time: {code_time:.6f} second')
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
