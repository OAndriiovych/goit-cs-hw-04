import time
import itertools
from collections import defaultdict
from pathlib import Path
from multiprocessing import Queue, Process


folders = []
q = Queue()


def get_folders(path: Path):
    for file in path.iterdir():
        if file.is_dir():
            folders.append(file)
            get_folders(file)


# Перевіряємо чи існує наданий шлях і формуємо список файлів
def file_list(input_path, list):
    path = Path(input_path)
    if Path(path).exists():
        for file in path.iterdir():
            if file.is_dir():
                folders.append(file)
                file_list(file, list)
            elif file.is_file():
                list.append(file)
    else:
        print("Введений каталог не існує")
        return -1
    return list


# Повертаємо вміст файла
def read_file(filename):
    with open(filename, 'r', encoding='cp1251') as f:
        return f.read()


# Використовуємо алгоритм пошуку підрядка Боєра-Мура
def build_shift_table(pattern):
    # Створюємо таблицю зсувів для алгоритму Боєра-Мура.
    table = {}
    length = len(pattern)
    for index, char in enumerate(pattern[:-1]):
        table[char] = length - index - 1
    table.setdefault(pattern[-1], length)
    return table


def bm_search(file, patterns_list):
    # Створюємо таблицю зсувів для патерну (підрядка)
    text = read_file(file)
    result_dict = defaultdict(list)
    for pattern in patterns_list:
        shift_table = build_shift_table(pattern)
        i = 0
        # Проходимо по основному тексту, порівнюючи з підрядком
        while i <= len(text) - len(pattern):
            j = len(pattern) - 1
            while j >= 0 and text[i + j] == pattern[j]:
                j -= 1
            if j < 0:
                # Підрядок знайдено
                result_dict[pattern].append(str(file))
                break
            i += shift_table.get(text[i + len(pattern) - 1], len(pattern))
    # Повертаємо отриманий словник результатів
    return result_dict


# Створемо функцію воркера для процесів і передаємо до неї чергу
def worker(files, patterns_list, q):
    result_dict = dict()
    for file in files:
        result = None
        result = bm_search(file, patterns_list)
        if result:
            for pattern in patterns_list:
                if result.get(pattern):
                    try:
                        result_dict[pattern].append(result.get(pattern))
                    except KeyError:
                        result_dict[pattern] = [result.get(pattern)]
    # Повертаємо результат пошуку за допомогою черги
    q.put(result_dict)


# Функція розподілу списку файлів для процесів і обробки резульатів їх виклику
def multi_threads(files, patterns):
    start_time = time.time()
    patterns_list = patterns.split(", ")
    result_dict = dict()
    files1 = []
    files2 = []
    files3 = []
    i = 1
    for file in files:
        if i % 3 == 1:
            files1.append(file)
        elif i % 3 == 2:
            files2.append(file)
        else:
            files3.append(file)
        i += 1

    file_list = (files1, files2, files3)
    p1 = Process(target=worker, args=(file_list[0], patterns_list, q))

    p2 = Process(target=worker, args=(files2, patterns_list, q))

    p3 = Process(target=worker, args=(files3, patterns_list, q))

    p1.start()
    p2.start()
    p3.start()

    p1.join()
    p2.join()
    p3.join()

    value1 = q.get()
    value2 = q.get()
    value3 = q.get()

    for pattern in patterns_list:
        try:
            if value1.get(pattern):
                value = list(itertools.chain(*value1.get(pattern)))
            if value2.get(pattern):
                value = value + list(itertools.chain(*value2.get(pattern)))
            if value3.get(pattern):
                value = value + list(itertools.chain(*value3.get(pattern)))
            if value:
                try:
                    result_dict[pattern].append(value)
                except KeyError:
                    result_dict[pattern] = value
        except UnboundLocalError:
            print("За запитом нічого не знайдено")
    finish_time = time.time()
    delta_time = finish_time - start_time
    print(f"Час виконання пошуку дорівнює {delta_time}")
    if result_dict:
        print(f"Результати пошуку {result_dict}")


def main():
    while True:
        try:
            print("Введіть каталог з файлами для пошуку або 'exit' для виходу")
            command = input()
            if command.lower() == 'exit':
                print("Вихід із програми.")
                break
            else:
                print("Введіть через кому слова для пошуку")
                patterns = input()
                list = []
                files = file_list(command, list)
                if files != -1:
                    multi_threads(files, patterns)
        except Exception as e:
            print(e)


if __name__ == '__main__':
    main()
