title: Ceburasko API

Ceburasko --- система группировки сообщений об ошибках. В версии 1 группировка производится по хэшу конкатенированной последовательности имен функций в стеке вызовов, приведших к ошибке.

# Методы

## Загрузка сообщения об ошибке

URL: `CEBURASKO_URL/project-<id>/upload-crash/`

Сообщение об ошибке кодируется с помощью YAML в теле запроса, формат `CrashReport`.

Формат (все поля не обязательны):

    Frame {
        string fn;   // функция
        string file; // имя файла, в котором живет функция
        int line;    // строка в файле
    }

    CrashReport {
        string version;    // версия приложения, в которой случилась ошибка
        string kind;       // тип ошибки
        string component;  // компонент, в котором случилась ошибка
        Frame stack[];     // стек вызовов, приведший к ошибке
        string annotation; // сопроводительный комментарий об ошибке 
    }

Пример запроса:

    GET /project-1/upload-crash/ HTTP/1.1
    Host: crashes.cn.ru

    version: 1.2.3
    component: bytefog-node
    kind: unhandled_exception
    stack:
    - fn: generate_exception()
      file: main.cpp
      line: 10
    - fn: main()
      file: main.cpp
      line: 20
    - fn: start

Пример ответа:

    HTTP/1.1 200 OK

    issue id 14859, fixed: False