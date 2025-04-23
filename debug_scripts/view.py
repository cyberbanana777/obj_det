import cv2
import numpy as np

def process_frame(frame):
    # Преобразуем кадр в чёрно-белый
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Размеры кадра
    height, width = gray.shape
    
    # Размеры каждой части
    part_height = height // 5
    part_width = width // 5
    
    # Создаем пустую матрицу 5x5 для хранения бинарных значений
    binary_matrix = np.zeros((5, 5), dtype=int)
    
    # Проходим по каждой части кадра
    for i in range(5):
        for j in range(5):
            # Вырезаем часть кадра
            part = gray[i * part_height:(i + 1) * part_height, j * part_width:(j + 1) * part_width]
            
            # Определяем, каких пикселей больше - чёрных или белых
            mean_value = np.mean(part)
            if mean_value > 127:
                binary_matrix[i, j] = 0
            else:
                binary_matrix[i, j] = 1
    
    return binary_matrix

def main():
    # Открываем видеопоток с камеры
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)



    if not cap.isOpened():
        print("Ошибка: Не удалось открыть камеру.")
        return
    
    while True:
        # Получаем кадр с камеры
        ret, frame = cap.read()
        
        if not ret:
            print("Ошибка: Не удалось получить кадр.")
            break
        
        # Обрабатываем кадр
        binary_matrix = process_frame(frame)
        
        # Выводим бинарную матрицу в командную строку
        print(binary_matrix)
        
        # Отображаем кадр
        cv2.imshow('Frame', frame)
        
        # Выход по нажатию клавиши 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Освобождаем ресурсы
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

