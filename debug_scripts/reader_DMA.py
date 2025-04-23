import mmap
import os
import time

def main():
    time_control = [] 

    # Проверить, существует ли общая область памяти
    if not os.path.exists("/dev/shm/shared_mem"):
        print("Общая область памяти не существует.")
        return

    # Открыть общую область памяти
    with open("/dev/shm/shared_mem", "rb") as f:
        while True:
            try:
                start_time = time.time()

                shm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

                # Прочитать данные из общей памяти
                data = shm.read()
                print(f"Получено: {data.decode('utf-8')}")

                end_time = time.time()
                execution_time = (end_time - start_time) * 1000
                time_control.append(execution_time)
                print(f"Время выполнения: {execution_time:.2f} милисекунд")

            except:
        
                # Закрыть отображение памяти
                shm.close()
                print(sum(time_control)/len(time_control), max(time_control), min(time_control))
                break

if __name__ == "__main__":
    main()
