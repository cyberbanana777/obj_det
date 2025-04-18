/*
Передача информации производится через DMA (direct memory access)

Через DMA отправляется:
 - Матрица
 - Информация о чёрных контурах ROI
 - Информация о чёрных контурах на кадре
 - Информация о цветных контурах на кадре

Версия: 3.2
*/

#include <opencv2/opencv.hpp>
#include <iostream>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <chrono>
#include <wiringPi.h>
#include <thread>
#include <cstring>
#include <sys/mman.h>


using namespace cv;
using namespace std;

/// Настройки для roi
int X_START = 0;
int Y_START = 470;
int WIDTH_ROI = 640;
int HEIGHT_ROI = 10;

// Настройка матриц
int DEMENTION = 9;

// Настройка видео
const bool SHOW_VIDEO_WINDOWS = false;

const int BUFFER_SIZE = 512;

// Структура для хранения диапазонов цветов
struct ColorRange
{
    Scalar lower;
    Scalar upper;
};

// Структура для хранения информации о контуре и его цвете
struct ContourInfo
{
    vector<Point> contour;
    string color;
};

void drawCrosshair(Mat &frame, Point center)
{
    // Горизонтальная линия на всю ширину кадра
    line(frame, Point(0, center.y), Point(frame.cols, center.y), Scalar(255, 255, 0), 1);
    // Вертикальная линия на всю высоту кадра
    line(frame, Point(center.x, 0), Point(center.x, frame.rows), Scalar(255, 255, 0), 1);
}

// Функция для вывода диапазонов цветов
void printColorRanges(const ColorRange &red1, const ColorRange &red2,
                      const ColorRange &green, const ColorRange &blue,
                      const ColorRange &black)
{
    cout << "Red Color Ranges:\n"
         << "Lower Red1: " << red1.lower << "\n"
         << "Upper Red1: " << red1.upper << "\n"
         << "Lower Red2: " << red2.lower << "\n"
         << "Upper Red2: " << red2.upper << "\n\n"
         << "Green Color Ranges:\n"
         << "Lower Green: " << green.lower << "\n"
         << "Upper Green: " << green.upper << "\n\n"
         << "Blue Color Ranges:\n"
         << "Lower Blue: " << blue.lower << "\n"
         << "Upper Blue: " << blue.upper << "\n\n"
         << "Black Color Ranges:\n"
         << "Lower Black: " << black.lower << "\n"
         << "Upper Black: " << black.upper << endl
         << endl;
}

vector<vector<int>> processFrame(Mat &frame)
{
    // Преобразуем кадр в чёрно-белый
    Mat gray;
    cvtColor(frame, gray, COLOR_BGR2GRAY);

    // Размеры кадра
    int height = gray.rows;
    int width = gray.cols;

    // Размеры каждой части
    int partHeight = height / DEMENTION;
    int partWidth = width / DEMENTION;

    // Создаем пустую матрицу 5x5 для хранения бинарных значений
    vector<vector<int>> binaryMatrix(DEMENTION, vector<int>(DEMENTION, 0));

    // Проходим по каждой части кадра
    for (int i = 0; i < DEMENTION; i++)
    {
        for (int j = 0; j < DEMENTION; j++)
        {
            // Вырезаем часть кадра
            Rect roi(j * partWidth, i * partHeight, partWidth, partHeight);
            Mat part = gray(roi);

            // Определяем, каких пикселей больше - чёрных или белых
            Scalar meanValue = mean(part);
            if (meanValue[0] > 125)
            {
                binaryMatrix[i][j] = 1;
            }
            else
            {
                binaryMatrix[i][j] = 0;
            }
        }
    }

    return binaryMatrix;
}

int main()
{
    // Инициализация библиотеки WiringPi
    wiringPiSetup();   // Использует стандартную нумерацию пинов
    pinMode(0, INPUT); // Установка пина 0 (GPIO 17) как вход

    // Создать общую область памяти
    int shm_fd = shm_open("/shared_mem", O_CREAT | O_RDWR, 0666);
    if (shm_fd < 0)
    {
        cerr << "Ошибка создания общей памяти" << endl;
        return 1;
    }

    // Установить размер области
    ftruncate(shm_fd, BUFFER_SIZE);

    // Отобразить область в память
    void *ptr = mmap(NULL, BUFFER_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (ptr == MAP_FAILED)
    {
        cerr << "Ошибка отображения памяти" << endl;
        return 1;
    }

    // Инициализация камеры
#ifdef _WIN32
    VideoCapture cap(0, cv::CAP_DSHOW); // Windows
#else
    VideoCapture cap(0, cv::CAP_V4L2); // Linux

    if (!cap.isOpened())
    {
        cerr << "Ошибка: Не удалось открыть стандартную камеру!" << endl;

        // Попробуйте открыть конкретное устройство (например, /dev/video1)
        int index = 1;

        for (int i = 1; i <= index + 5; ++i)
        {
            cap.open(i);

            if (cap.isOpened())
            {
                cout << "Камера найдена под индексом: " << i << endl;
                break;
            }
            else
            {
                cout << "Не удалось открыть камеру под индексом: " << i << endl;
            }
        }
    }
#endif

    if (!cap.isOpened())
    {
        cerr << "Ошибка: Не удалось открыть камеру!" << endl;
        return -1;
    }

    cap.set(CAP_PROP_FRAME_WIDTH, 640);
    cap.set(CAP_PROP_FRAME_HEIGHT, 480);

    // Определение диапазонов цветов в HSV
    ColorRange red1 = {Scalar(0, 50, 50), Scalar(10, 255, 255)};
    ColorRange red2 = {Scalar(160, 50, 50), Scalar(180, 255, 255)};
    ColorRange green = {Scalar(56, 159, 97), Scalar(71, 255, 255)};
    ColorRange blue = {Scalar(75, 168, 33), Scalar(104, 255, 210)};
    ColorRange black = {Scalar(0, 0, 0), Scalar(180, 255, 88)};

    // Вывод диапазонов цветов в консоль
    printColorRanges(red1, red2, green, blue, black);

    while (true)
    {

        int state = digitalRead(0);

        if (state == 0)
        {
        }

        else
        {
            auto start = std::chrono::steady_clock::now();

            Mat frame;
            cap >> frame; // Чтение кадра с камеры

            if (frame.empty())
            {
                cerr << "Ошибка: Пустой кадр!" << endl;
            }

            else
            {

                Rect roi_rect(X_START, Y_START, WIDTH_ROI, HEIGHT_ROI);
                Mat roi(frame, roi_rect);

                // Преобразование изображения в HSV цветовое пространство

                Mat hsv;
                Mat hsv_roi;
                cvtColor(frame, hsv, COLOR_BGR2HSV);
                cvtColor(roi, hsv_roi, COLOR_BGR2HSV);

                // Создание масок для каждого цвета
                Mat mask_red1, mask_red2, mask_green, mask_blue;
                Mat mask_black, mask_black_roi;

                inRange(hsv, red1.lower, red1.upper, mask_red1);
                inRange(hsv, red2.lower, red2.upper, mask_red2);
                inRange(hsv, green.lower, green.upper, mask_green);
                inRange(hsv, blue.lower, blue.upper, mask_blue);

                // Черная маска
                inRange(hsv, black.lower, black.upper, mask_black);
                inRange(hsv_roi, black.lower, black.upper, mask_black_roi);

                // Объединение масок красного цвета
                Mat mask_red = mask_red1 | mask_red2;
			
		// Уменьшение шума (размытие)
		int size = 15;
    		GaussianBlur(mask_black, mask_black, Size(size, size), 0);

    		// Морфологическое закрытие (объединение разрывов)
    		Mat kernel = getStructuringElement(MORPH_RECT, Size(10, 10));
    		morphologyEx(mask_black, mask_black, MORPH_CLOSE, kernel, Point(-1, -1), 2);

                // Нахождение контуров в масках
                vector<vector<Point>> contours_red;
                vector<vector<Point>> contours_green;
                vector<vector<Point>> contours_blue;
                vector<vector<Point>> contours_black;
                vector<vector<Point>> contours_black_roi;

                findContours(mask_red, contours_red, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);
                findContours(mask_green, contours_green, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);
                findContours(mask_blue, contours_blue, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);
                findContours(mask_black, contours_black, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);
                findContours(mask_black_roi, contours_black_roi, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);
                // Объединение всех контуров в один вектор с идентификатором цвета
                vector<ContourInfo> all_contours;

                for (const auto &contour : contours_red)
                {
                    all_contours.push_back({contour, "Red"});
                }
                for (const auto &contour : contours_green)
                {
                    all_contours.push_back({contour, "Green"});
                }
                for (const auto &contour : contours_blue)
                {
                    all_contours.push_back({contour, "Blue"});
                }
                for (const auto &contour : contours_black)
                {
                    all_contours.push_back({contour, "Black"});
                }
                for (const auto &contour : contours_black_roi)
                {
                    all_contours.push_back({contour, "Black_roi"});
                }

                // Собираем данные о всех обнаруженных объектах в одну строку
                stringstream ss;

                Point frameCenter(frame.cols / 2, frame.rows / 2); // Центр кадра
                double minDistance = std::numeric_limits<double>::max();
                ContourInfo closestContour;

                for (const auto &contourInfo : all_contours)
                {
                    Rect boundingBox = boundingRect(contourInfo.contour);
                    int width = boundingBox.width;
                    int height = boundingBox.height;

                    string color_detected = contourInfo.color; // Используем идентификатор цвета
                    // Условие для игнорирования контуров с маленькими размерами
                    if ((width >= 70 && height >= 70 && contourArea(contourInfo.contour) > 5000) || (color_detected == "Black_roi" && contourArea(contourInfo.contour) > 30))
			    
                    {
                        int y_buff = 0;
                        if (color_detected == "Black_roi")
                        {
                            y_buff = Y_START;
                        }

                        Mat path = frame;

                        Point center(boundingBox.x + width / 2,
                                     boundingBox.y + height / 2 + y_buff);
                        drawCrosshair(path, center);

                        if (SHOW_VIDEO_WINDOWS)
                        {
                            double distance = norm(center - frameCenter); // Расстояние до центра
                            if (distance < minDistance)
                            {
                                minDistance = distance;
                                closestContour = contourInfo; // Сохраняем ближайший контур
                            }
                        }

                        ss << color_detected << ","
                           << width << ","
                           << height << ","
                           << center.x
                           << ","
                           << center.y
                           << ","
                           << ((float)center.x - frame.cols / 2) / (frame.cols / 2)
                           << ";";

                        if (SHOW_VIDEO_WINDOWS)
                        {
                            // Рисуем прямоугольник вокруг объекта и выводим его цвет и координаты центра
                            rectangle(path, boundingBox.tl(), boundingBox.br(), Scalar(0, 255, 0), 2);
                            putText(path,
                                    color_detected + " Center: (" + to_string(center.x) + ", " + to_string(center.y) + ")",
                                    Point(boundingBox.x + 5, boundingBox.y - 10),
                                    FONT_HERSHEY_SIMPLEX,
                                    0.5,
                                    Scalar(255, 255, 255),
                                    1);
                        }
                    }
                }

                if (SHOW_VIDEO_WINDOWS)
                {
                    // Рисуем ближайший контур красным цветом
                    if (!closestContour.contour.empty())
                    {
                        Rect closestBoundingBox = boundingRect(closestContour.contour);
                        Mat path = frame; // По умолчанию используем основной кадр
                        if (closestContour.color == "Black_roi")
                        {
                            path = roi;
                        }
                        rectangle(path,
                                  closestBoundingBox.tl(),
                                  closestBoundingBox.br(),
                                  Scalar(0, 0, 255), // Красный цвет для ближайшего контура
                                  2);
                    }
                }
                ss << "Matrix,";
                vector<vector<int>> binaryMatrix = processFrame(frame);
                for (int i = 0; i < DEMENTION; i++)
                {
                    for (int j = 0; j < DEMENTION; j++)
                    {
                        ss << binaryMatrix[i][j];
                    }
                    if (i != DEMENTION - 1)
                    {
                        ss << ",";
                    }
                }
                ss << ";#";


                // Копировать данные в общую память
                string message = ss.str();

		message.resize(BUFFER_SIZE, '_');
		char buffer[message.size()];
		message.copy(buffer, message.size());
		buffer[message.size()] = '\0';
		cout << buffer <<endl;
                memcpy(ptr, buffer, strlen(buffer) + 1);

                if (SHOW_VIDEO_WINDOWS)
                {
                    // Показать результат
                    imshow("Color Detection", frame);

                    imshow("ROI_part", roi);
                    // Отображение масок в отдельных окнах с указанием цвета
                    imshow("Black Mask", mask_black);
                    imshow("Red Mask", mask_red);
                    imshow("Blue Mask", mask_blue);
                    imshow("Green Mask", mask_green);
                }
            }

            // Выход из цикла при нажатии клавиши 'q'
            if (waitKey(1) == 'q')
            {
                break;
            }

            auto end = std::chrono::steady_clock::now();
            auto elapsed_ms = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
            cout << "Time taken: " << elapsed_ms.count() << " ms\n";
        }
    }

    // Освобождение ресурсов
    cap.release();
    destroyAllWindows();

    // Закрыть файловый дескриптор
    close(shm_fd);

    munmap(ptr, BUFFER_SIZE);      // Освободить отображение
    shm_unlink("/shared_mem"); // Удалить объект


    return 0;
}
