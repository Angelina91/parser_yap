import re
import logging
from pathlib import Path
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    # Вместо константы WHATS_NEW_URL, используйте переменную whats_new_url.
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    if __name__ == '__main__':
        # Загрузка веб-страницы с кешированием.
        response = get_response(session, whats_new_url)
        if response is None:
        # Если основная страница не загрузится, программа закончит работу.
             return
        # Создание "супа".
        soup = BeautifulSoup(response.text, features='lxml')

        # Шаг 1-й: поиск в "супе" тега section с нужным id. Парсеру нужен только 
        # первый элемент, поэтому используется метод find().
        main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})

        # Шаг 2-й: поиск внутри main_div следующего тега div с классом toctree-wrapper.
        # Здесь тоже нужен только первый элемент, используется метод find().
        div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})

        # Шаг 3-й: поиск внутри div_with_ul всех элементов списка li с классом toctree-l1.
        # Нужны все теги, поэтому используется метод find_all().
        sections_by_python = div_with_ul.find_all(
            'li',
            attrs={'class': 'toctree-l1'}
        )

        # Печать первого найденного элемента.
        results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
        for section in tqdm(sections_by_python):
            version_a_tag = section.find('a')
            href = version_a_tag['href']
            version_link = urljoin(whats_new_url, href)
        # Здесь начинается новый код!
            response = get_response(session, version_link)
            if response is None:
            # Если страница не загрузится, программа перейдёт к следующей ссылке.
                continue
            soup = BeautifulSoup(response.text, 'lxml')  # Сварите "супчик".
            h1 = find_tag(soup, 'h1')  # Найдите в "супе" тег h1.
            dl = find_tag(soup, 'dl')  # Найдите в "супе" тег dl.
            dl_text = dl.text.replace('\n', ' ')
    # На печать теперь выводится переменная dl_text — без пустых строчек.
            results.append(
                (version_link, h1.text, dl_text)
            )

    return results


def latest_versions(session):
    if __name__ == '__main__':
        response = get_response(session, MAIN_DOC_URL)
        if response is None:
            return
        soup = BeautifulSoup(response.text, features='lxml')
        sidebar = find_tag(soup, 'div', class_='sphinxsidebarwrapper')
        ul_tags = sidebar.find_all('ul')
        # Перебор в цикле всех найденных списков.
        for ul in ul_tags:
        # Проверка, есть ли искомый текст в содержимом тега.
            if 'All versions' in ul.text:
            # Если текст найден, ищутся все теги <a> в этом списке.
                a_tags = ul.find_all('a')
            # Остановка перебора списков.
                break
    # Если нужный список не нашёлся,
    # вызывается исключение и выполнение программы прерывается.
        else:
            raise Exception('Ничего не нашлось')

        # Список для хранения результатов.
        results = [('Ссылка на документацию', 'Версия', 'Статус')]
        # Шаблон для поиска версии и статуса:
        pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
        # Цикл для перебора тегов <a>, полученных ранее.
        for a_tag in a_tags:
            # Напишите новый код, ориентируясь на план.
            link = a_tag['href']
            text_match = re.search(pattern, a_tag.text)
            if text_match is not None:
                version, status = text_match.groups()
            else:
                version, status = a_tag.text, ''
            results.append(
                (link, version, status)
            )
        return results


def download(session):
    # Вместо константы DOWNLOADS_URL, используйте переменную downloads_url.
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    if __name__ == '__main__':

        response = get_response(session, downloads_url)
        if response is None:
            return
        soup = BeautifulSoup(response.text, features='lxml')
        table_tag = find_tag(soup, 'table', {'class': 'docutils'})
        pdf_a4_tag = find_tag(table_tag, 'a',
                                    {'href': re.compile(r'.+pdf-a4\.zip$')}
                                    )
        pdf_a4_link = pdf_a4_tag['href']
        archive_url = urljoin(downloads_url, pdf_a4_link)
        filename = archive_url.split('/')[-1]
        # Сформируйте путь до директории downloads.
        downloads_dir = BASE_DIR / 'downloads'
        # Создайте директорию.
        downloads_dir.mkdir(exist_ok=True)
        # Получите путь до архива, объединив имя файла с директорией.
        archive_path = downloads_dir / filename

        # Загрузка архива по ссылке.
        response = session.get(archive_url)

        # В бинарном режиме открывается файл на запись по указанному пути.
        with open(archive_path, 'wb') as file:
            # Полученный ответ записывается в файл.
            file.write(response.content)
        logging.info(f'Архив был загружен и сохранён: {archive_path}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
}


def main():
    # Запускаем функцию с конфигурацией логов.
    configure_logging()
    # Отмечаем в логах момент запуска программы.
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    # Логируем переданные аргументы командной строки.
    logging.info(f'Аргументы командной строки: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()

    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    # Если из функции вернулись какие-то результаты,
    if results is not None:
        # передаём их в функцию вывода вместе с аргументами командной строки.
        control_output(results, args)
    # Логируем завершение работы парсера.
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
