# -*- coding: utf-8 -*-

""" Модуль common.py - сборник функций большинства программ. """

#                Автор: Л.М.Матвеев

pyscr = None

import  sys

#..............................................................................

web_code = 'cp1251'  # или 'utf8' - Кодировка результирующих HTML файлов
# Значение charset для результирующих HTML файлов
web_chr_set = web_code if web_code != 'cp1251' else 'Windows-1251'

# Платформа
win = sys.platform in ('win32', 'win64')

# Кодировка символов в терминале
trm_code = ['utf8', 'cp866'][win]

# Кодировка символов в системе
sys_code = ['utf8', 'cp1251'][win]

# StringTypes, UnicodeType, DictType, TupleType, BooleanType, IntType
# from types import IntType

#------------------------------------------------------------------------------
def printm(s):
    """ Печать Юникод-строк в терминал и скриптер.
        Автоматический перевод строки не производится. """
    sys.stdout.write(s)
#    if pyscr:
#        sys.stdout.write(s)
#    else:
#        sys.stdout.write(s.encode(trm_code))
#..............................................................................
from os.path import split, splitext


#------------------------------------------------------------------------------
def main0(main, n_args=None):  # Любое ненулевое количество
    """ При автономном запуске файла-модуля с параметрами командной строки,
    обрабатывает их и вызывает функцию "main"
    n_args - значение или список допустимого количества аргум ком строки
            если None - то хоть какое-то количество
    """

    import time
    t = time.time()

    if isinstance(n_args, int):
        n_args = [n_args]

    args = ('\n'.join(sys.argv)).split('\n')
    i0 = 1
    if len(args) > 1 and splitext(args[1])[-1].upper() == '.BAT':
        i0 = 2
    args2 = args[i0:]

    #if len(args2) != n_args:
    if n_args is None and not args2:
        printm('\nОшибка! Должны быть аргументы командной строки'
                        ' (имена файлов)\n')
    elif n_args is not None and len(args2) not in n_args:
        tmp = list(map(str, n_args))
        printm('\nОшибка! Количество аргументов командной строки'
                        ' (имен файлов)\n    д.б. не %s' % len(args2) +
                        ', а %s!\n' % ' или '.join([', '.join(p) for p in
                        (tmp[:-1], tmp[-1:]) if p != []]))

    if (n_args is None and not args2 or n_args is not None and
            len(args2) not in n_args) and n_args != [0]:
        form_bat()

    if (n_args is None and args2 or
            n_args is not None and len(args2) in n_args):
        main(args2)

    printm('\n   Запущено :\n')
    if i0 == 2:
        printm(u"%s\n" % args[1])           # Имя батника
    printm(u"%s\n" % args[0])                       # Имя программы
    printm('Выполнялось %s сек\n' % (time.time() - t))
    if len(args2):
        printm('\n    Аргументы командной строки :\n')
        for a in args2:
            printm(u"%s\n" % a)     # Аргументы программы

    if not pyscr:
        printm('\nДля выхода жми "Enter" . . .')
        input()  # Останов для просмотра результатов
#..............................................................................


#------------------------------------------------------------------------------
def form_bat():
    """ Обеспечивает при необходимости формирование BAT-файла,
    для вызова модуля и передачи параметров перетаскиванием
    файлов на данный BAT-файл, если не возможна передача
    перетаскиванием их на сам PY-файл. """
#    from types import UnicodeType
    printm(('''
  Можно перетаскивать файлы мышкой и опускать на файл
программы %s
или специально подготовленный для этого BAT-файл.

  Для формирования такого файла введите "Y" : ''') % split(sys.argv[0])[-1])
    ans = input()
#    if isinstance(ans, UnicodeType):
#        pass
#    else:
#        ans = ans.decode(trm_code)
    if pyscr:
        printm('%s\n' % ans)
    if not ans or ans[0] not in 'YyНн':
        return
    fb = sys.argv[0]
    fd = open(fb + '.bat', 'w')
    fd.write('''@echo off
set PyExe=%s
set ProgPy=%s
IF EXIST %%PyExe%% goto okay0
    echo.
    echo File "%%PyExe%%" not exist
    pause
    goto end
:okay0
IF EXIST %%ProgPy%% goto okay1
    echo.
    echo File "%%ProgPy%%" not exist
    pause
    goto end
:okay1
%%PyExe%% %%ProgPy%% %%0 %%1 %%2 %%3 %%4
IF %%ERRORLEVEL%% LEQ 0 goto okay2
    echo.
    echo %%error level%% = %%ERRORLEVEL%%
    pause
    goto end
:okay2
IF ERRORLEVEL 0 goto end
    echo.
    echo error level = ERRORLEVEL
    pause
:end
'''.encode(sys_code) % (sys.executable.encode(sys_code), fb))
    fd.close()
    printm('  BAT-файл "%s" сформирован.\n' % split(fb + '.bat')[1])
#..............................................................................

#------------------------------------------------------------------------------
#..............................................................................


#------------------------------------------------------------------------------
def main(args):
    """ Получает список файлов, переданных в параметрах командной
    строки. Значение "_n_args" должно соответствовать требуемому
    количеству передаваемых файлов. """
    pass
#..............................................................................


#------------------------------------------------------------------------------
if __name__ == '__main__':
    pyscr = 'pyscripter' in dir()

    _n_args = 2
    main0(main, _n_args)  # Нет необходимости трогать
