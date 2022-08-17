#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Формирует заготовку сборочного чертежа из PCB-файла.
                Автор: Л.М.Матвеев """

import re
import os, sys
from os import remove, rename, listdir
from os.path import splitext, exists, join, isdir, split
from shutil import copy2
from glob import glob

import common
from  common import printm

PCAD_CODE = 'cp1251'  # Кодировка исходного PCB файла
PCAD_LINESEP = '\r\n'

if splitext(__file__)[0].endswith('_sbor_cu'):
    result_type = 'sbor_cu'
elif splitext(__file__)[0].endswith('_sbor'):
    result_type = 'sbor'
elif splitext(__file__)[0].endswith('_flip'):
    result_type = 'flip'
elif splitext(__file__)[0].endswith('_swap'):
    result_type = 'swap'
elif splitext(__file__)[0].endswith('_clear'):
    result_type = 'clear'
else:
    result_type = 'sbor'
    #result_type = None

FLAG_ASCII_SAVE = True

DOP_RD_PREFIX = '~'

#------------------------------------------------------------------------------
def search_for_files_path(begin_paths, mit_paths,
                            end_path_files, search_depth):
    for i in range(search_depth):
        for begin_path in begin_paths:  # Перебор начал пути
            for mit_path in mit_paths:  # Перебор масок средины пути
                for finde in glob(join(begin_path, mit_path)):
                    # Перебор совпадений пути с маской
                    if not isdir(finde):
                        continue

                    for end_path_file in end_path_files:
                        # Перебор наличия файллов для пути
                        if not exists(join(finde, end_path_file)):
                            break
                    else:  # Все файлы есть
                        return finde

        # Если не нашли на этом уровне вложености, поищем ещё глубже
        # Строим список вложенных папок
        begin_paths2 = []
        for begin_path in begin_paths:
            if not exists(begin_path) or not isdir(begin_path):
                continue
            try:
                sub_paths = listdir(begin_path)
            except WindowsError:
                continue

            for sub_path in sub_paths:
                if not isdir(join(begin_path, sub_path)):
                    continue
                begin_paths2.append(join(begin_path, sub_path))

        begin_paths = begin_paths2

    return ''
#..............................................................................


pcad_path = None

exts = {u"PCB": {'pr_fn': u"PCB", 'pr_name': 'PCB'},
        u"SCH": {'pr_fn': u"SCH", 'pr_name': 'Schematic'},
##        u"LIB": {'pr_fn': u"CMP"},
##        u"LIA": {'pr_fn': u"CMP", 'pr_name': 'Library Executive'},
        }


#------------------------------------------------------------------------------
def complete_exts():
    """ Дополняет словарь расширений ПКАД-файлов
    полными именами соответствующих программ """
    global pcad_path

    begin_paths = ['C:/', 'D:/', 'E:/', 'F:/', '/media', '?']
    mit_paths = ['P?CAD?2006']
    end_path_files = ['%s.EXE' % fn for fn in
                [v['pr_fn'] for v in exts.values()]]
    finde = search_for_files_path(begin_paths, mit_paths, end_path_files, 3)

    if finde != '':
        pcad_path = finde
        printm('\n  ПКАД-exe-файлы найдены в:\n"%s"\n' %
                                pcad_path.replace('/', '\\'))
    else:
        printm('  ПКАД-exe-файлы на дисках НЕ НАЙДЕНЫ.\n')
#..............................................................................
complete_exts()


#------------------------------------------------------------------------------
def read_pcad_file(fpne):
    """ Считывает ПКАД-файл в список. """

    if fpne == '':
        return

    fpn, ext = splitext(fpne)
    ext = ext[1:].upper()

    printm('%s\n' % fpne.replace('/', '\\'))
    printm('  Проверка файла на пригодность\n')

    if not exists(fpne):
        printm('  Ошибка! Файл не cуществует\n')
        return

    if ext not in exts:   # Проверка типа файла по расшир
        printm('  Ошибка! Расширение у файла д.б. %s\n' %
                                                ' или '.join(exts.keys()))
        return

    fh_in = open(fpne, 'rb')   # Возможно обрамить Тру Кечем
    test_accel_ascii = 'ACCEL_ASCII "'
    lines_in_0 = fh_in.read(len(test_accel_ascii)).decode(PCAD_CODE)
    if lines_in_0 == test_accel_ascii:
        # Ура! Это скорей всего файл в ASCII формате
        lines_in_0 += fh_in.read(512).decode(PCAD_CODE)
        fh_in.close()   # Оценка содержимого файла
        lines_in_0 = lines_in_0.split(PCAD_LINESEP)
        if lines_in_0[1] != '':  # Вторая строка д.б. пустая в обоих форматах
            printm(u"  Ошибка! Вторая строка файла не пустая.\n")
            return
        if not (lines_in_0[0].startswith('ACCEL_ASCII "') and
                lines_in_0[5].startswith('  (program "P-CAD 2006 %s" ' %
                                exts[ext]['pr_name'])):
            # Первая и шестая строки должны начинаться так для ASCII формата
            printm('  Ошибка! Нестандартный формат ASCII файла\n')
            return
        fh_in = open(fpne, 'rb')   # Возможно обрамить Тру Кечем
        t = fh_in.read().decode(PCAD_CODE)

    else:  # Это скорей всего файл в бинарном формате
        if ext in {'SCH', 'PCB'}:  # Возможно это схема или плата
            lines_in_0 += fh_in.read(128).decode(PCAD_CODE)
            lines_in_0 = lines_in_0.split(PCAD_LINESEP)
            if len(lines_in_0) < 2:  # Вторая строка д.б. пустая в обоих форматах
                printm(u"  Ошибка! Начало файла не соотв PCAD-файлам.\n")
                return
            if lines_in_0[1] != '':  # Вторая строка д.б. пустая в обоих форматах
                printm(u"  Ошибка! Вторая строка PCAD-файла не пустая.\n")
                return
            if not lines_in_0[3].startswith('P-CAD 2006 %s Binary (Rev ' %
                                    exts[ext]['pr_name']):
                # Четвёртая строка должна начинаться так для бинарного формата
                printm('  Ошибка! Формат файла не соответствует PCAD\n')
                return

        printm('  Исходный файл в "ACCEL BIN" формате.\n')
        printm('  Необходимо преобразование файла в "ACCEL ASCII" формат.\n')
         # Поиск программы для преобразования файла
        pcad_exe = join(pcad_path, exts[ext]['pr_fn'] + '.EXE')
        if not exists(pcad_exe):   # В имени не нужны кавычки
            printm('  Ошибка! Не найдена необходимая '
                            'для этого программа : \n%s\n' %
                                pcad_exe.replace('/', '\\'))
            printm('    %s-файл невозможно преобразовать '
                            'в "ACCEL ASCII" формат.\n' % ext)
            printm('    Пересохраните %s-файл '
                            'в "ACCEL ASCII" формате.\n' % ext)
            return

        pcad_in = r'_b_i_n_.' + ext  # Не любить ПКАД рус букв в ком строке
        copy2(fpne, pcad_in)

        if FLAG_ASCII_SAVE:
            printm('    Что-бы не терять времени, впредь используйте '
                                'файлы в "ACCEL ASCII" формате.\n')

        printm('    (Если автоматичекое преобразование зависнет, закройте\n')
        printm('       программу и произведите преобразование вручную.)\n')
        printm('    Подождите пару минут, производится преобразование ...\n')
        pcad_out = r'_a_s_c_i_i_.' + ext
        bat_t = r'"%s" /A %s %s' % (pcad_exe, pcad_in, pcad_out)

        import subprocess
        import shlex
        args = shlex.split(bat_t)
        p = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        kv = p.communicate()[0]  # код возврата

        remove(pcad_in)

        if kv or not exists(pcad_out):
            printm('  Ошибка! Неудалось преобразовать '
                            'файл в "ACCEL ASCII" формат.\n')
            printm('    Возможно PCAD не 2006 '
                            'или не установлены "Сервис-паки".\n')
            printm('    Пересохраните %s-файл '
                            'в "ACCEL ASCII" формате.\n' % ext)
            return

        fh_in = open(pcad_out, 'rb')  # Возможно обрамить Тру Кечем
        t = fh_in.read().decode(PCAD_CODE)
        fh_in.close()

        if FLAG_ASCII_SAVE:

            # Удаление нулевых символов
            t = t.replace('\x00', '')

            # Удаление layerBias
            t = re.sub(r'(?msu)^    \(layerBias NonSignal\).\n', '', t)

            fh_in = open(pcad_out, 'wb')  # Возможно обрамить Тру Кечем
            fh_in.write(t.encode(PCAD_CODE))
            fh_in.close()

            # Если промежуточный ASCII-файл может пригодиться, сохраним его
            pcad_out2 = '_ASCII'.join(splitext(fpne))
            if exists(pcad_out2):
                remove(pcad_out2)
            rename(pcad_out, pcad_out2)
            printm('  Исходный файл преобразован в "ACCEL ASCII" формат и ' +
                'сохранён с \n  именем:%s\n' % pcad_out2.replace('/', '\\'))
        else:  # Если нам не нужен промежуточный ASCII-файл
            remove(pcad_out)

    del lines_in_0
    fh_in.close()

    if not t:
        printm('  Ошибка! Файл неудалось считать.\n')
        return

    printm('  Файл из %s строк считан.\n' % len(t.split(PCAD_LINESEP)))

    # Удаление нулевых символов
    t = t.replace('\x00', '')

    # Удаление layerBias
    t = re.sub(r'(?msu)^    \(layerBias NonSignal\).\n', '', t)

    return t
#..............................................................................


from decimal import Decimal as Decim

GAP_L = Decim('50.00')
GAP_R = Decim('50.00')
GAP_CL = Decim('40.00')
GAP_CR = Decim('40.00')

inch = Decim('2.54')
cinch = Decim('0.0254')
meases = {'mm': inch, 'Mil': Decim('100.0'), 'mil': Decim('100.0')}
measdef = None
mirror_const = None
shift_const = None

pat_ptx = r'(?P<xvs>-?\d+\.\d+)(?: ?(?P<xms>mm|Mil|mil))?'
pat_pty = r'(?P<yvs>-?\d+\.\d+)(?: ?(?P<yms>mm|Mil|mil))?'

by_min = None   # Положение ... платы
by_max = None   # Положение ... платы
x_b0 = None     # Положение торца платы

#------------------------------------------------------------------------------
def get_pcb_params(t):
    global mirror_const, shift_const, by_min, by_max, x_b0, measdef#

    # Единицы измерения поумолчанию
    measdef = re.search(r'(?msu)^  \(fileUnits ([^)]*)\)', t).group(1)
    # Всё переводим в мм
    # Размер листа
    mo = re.search(r'(?msu)^    \(workspaceSize %s ' % pat_ptx, t)
    page_width = Decim(mo.group('xvs'))
    page_mil = (mo.group('xms') if mo.group('xms') else measdef) != 'mm'
    if page_mil:
        page_width *= cinch

    x_min = Decim('1000000000')
    x_max = Decim('0')
    by_min = Decim('1000000000')
    by_max = Decim('0')

    # Координаты краёв и ширина платы
    re_pt = re.compile(r'(?msu)\(pt %s %s' % (pat_ptx, pat_pty))
    for mo1 in re.finditer(r'(?msu)^  \(layerContents \(layerNumRef'
                            r' (?P<lay>\d+)\).*?^  \)', t):

        #not_board = result_type == 'flip' or mo1.group('lay') != '3'
        not_board = result_type == 'flip' or mo1.group('lay') not in (
                                                            '1', '2', '3')
        ttmp = mo1.group()
        for mo2 in re_pt.finditer(ttmp):

            vd = Decim(mo2.group('xvs'))
            xms = mo2.group('xms')

            if (xms if xms else measdef) != 'mm':
                vd *= cinch
            if x_max < vd:
                x_max = vd
            elif x_min > vd:
                x_min = vd

            if not_board:
                continue

            vd = Decim(mo2.group('yvs'))
            yms = mo2.group('yms')

            if (yms if yms else measdef) != 'mm':
                vd *= cinch
            if by_max < vd:
                by_max = vd
            elif by_min > vd:
                by_min = vd

    board_width = x_max - x_min

    # Тут пусть в милсах, меньше потом переводить
    if result_type == 'flip':
        mirror = int((x_min + x_max) / inch + 2) * Decim('100')
        mirror_const = {'mm': mirror * cinch, 'Mil': mirror, 'mil': mirror}
    else:
        x_b0 = int(round((GAP_L + board_width + GAP_CL) / inch)) * Decim('2.54')#
        shift = int(round((x_min - GAP_L) / inch)) * Decim('100')
        mirror = int(round((GAP_L + board_width + GAP_CL + GAP_CR +
                             board_width + x_min) / inch)) * Decim('100')
        mirror_const = {'mm': mirror * cinch, 'Mil': mirror, 'mil': mirror}
        shift_const = {'mm': shift * cinch, 'Mil': shift, 'mil': shift}

        page_width_min = board_width * 2 + GAP_L + GAP_CL + GAP_CR + GAP_R
        if page_width < page_width_min:
            if page_mil:
                page_width_min /= cinch
            # Размер листа увеличить
            t = re.sub(r'(?msu)(?<=^    \(workspaceSize )-?\d+\.\d+',
                                            str(page_width_min), t)
    return t
#..............................................................................

pat_pte = (r'(?P<beg>\((?:pt|polyPoint) )'     # Зaголовок точки
           r'(?P<xvs>-?\d+\.\d+)(?P<mit>'  # Значение Х точки
           r'(?: ?(?P<xms>mm|Mil|mil))?'   # Размерномть Х точки
           r' -?\d+\.\d+'                  # Значение Y точки
           r'(?: ?(?:mm|Mil|mil))?'        # Размерномть Y точки
           r' ?-?)(?=(?P<deg>\d+)?)')      # возможно пробел или знак угла


#------------------------------------------------------------------------------
def change_pt_flip(mo):
    return change_pte(mo, True)

def change_pt_shift(mo):
    return change_pte(mo, False)

def change_pte(mo, flipen):

    xvd = Decim(mo.group('xvs'))
    xms = mo.group('xms')
    unit = xms if xms else measdef
    if flipen: s = mo.group('beg') + \
                   str(
                       mirror_const[unit] -
                       xvd
                   ) + \
                   mo.group('mit')
    else: s = mo.group('beg'
        ) + str(xvd - shift_const[unit]) + mo.group('mit')

    if mo.group('deg') == '0':
        pass  # Перед 0 знак не менять
    elif s[-1] == '-':
        return s[:-1]
    elif s[-1] == ' ':
        return s + '-'

    return s
#..............................................................................


inf_lays = {}
end_ind = None


#------------------------------------------------------------------------------
def get_inf_lays(t):
    global inf_lays, end_ind

    inf_lays = {'3': {'out': []},
                '1': {'out': [], 'pair': '2'},
                '2': {'out': [], 'pair': '1'},
                '4': {'out': [], 'pair': '5'},
                '5': {'out': [], 'pair': '4'},
                '6': {'out': [], 'pair': '7'},
                '7': {'out': [], 'pair': '6'},
                '8': {'out': [], 'pair': '9'},
                '9': {'out': [], 'pair': '8'},
               '10': {'out': [], 'pair': '11'},
               '11': {'out': [], 'pair': '10'}}

    for mo in re.finditer(  # Получение типов слоёв
                r'(?msu)^    \(layerNum (?P<lay_num>\d+)\).*?'
                r'^    \(layerType (?P<lay_type>[^\)]+)\)', t):
        lay_num = mo.group('lay_num')
        if lay_num not in inf_lays:
            inf_lays[lay_num] = {'out': []}
        inf_lays[lay_num]['type'] = mo.group('lay_type')

    for mo in re.finditer(  # Получение парности дополнительных слоёв
                r'(?msu)^    \(layerPair (\d+) (\d+)\)', t):
        lay_num1 = mo.group(1)
        lay_num2 = mo.group(2)
        inf_lays[lay_num1]['pair'] = lay_num2
        inf_lays[lay_num2]['pair'] = lay_num1

    mo1 = None
    for mo1 in re.finditer(  # Перебираем слои с содержимым
                r'(?msu)^  \(layerContents \(layerNumRef (?P<lay_num>\d+)\)'
                r'.*?(?=^  \()', t):
        lay_num = mo1.group('lay_num')
        inf_lays[lay_num]['mo1'] = mo1
        cur_lay_inf = inf_lays[lay_num]
        cur_pair_lay_num = cur_lay_inf.get('pair')
        if cur_pair_lay_num:
            top_side = int(lay_num) < int(cur_pair_lay_num)
            flip_lay_inf = inf_lays[cur_pair_lay_num]
        else:
            top_side = None
            #flip_lay_inf = None
            flip_lay_inf = cur_lay_inf

        for mo2 in re.finditer(  # Запоминаем элементы слоя
                r'(?msu)^    \((?P<name>\w+) '
                r'.*?(?=^  (?:\)|  \())', mo1.group()):

            # Перебираем и обрабатываем элементы слоя
            try:  # Обработчик по имени элемента
                handler = eval('h_' + mo2.group('name'))
            except NameError:  # Обработчик по умолчанию для остальн элементов
                handler = layer_contents_handler

            handler(mo2, cur_lay_inf, cur_pair_lay_num,
                                    top_side, flip_lay_inf)
    end_ind = mo1.end()

    if result_type != 'flip': inf_lays['3']['out'].append(
        '    (line (pt %s mm %s mm) (pt %s mm %s mm) (width 0.3 mm) )\r\n' %
                (x_b0, by_min, x_b0 + Decim('1.5'), by_min) +
        '    (line (pt %s mm %s mm) (pt %s mm %s mm) (width 0.3 mm) )\r\n' %
                (x_b0, by_max, x_b0 + Decim('1.5'), by_max) +
        '    (line (pt %s mm %s mm) (pt %s mm %s mm) (width 0.3 mm) )\r\n' %
                (x_b0, by_min, x_b0, by_max) +
        '    (line (pt %s mm %s mm) (pt %s mm %s mm) (width 0.3 mm) )\r\n' %
                (x_b0 + Decim('1.5'), by_min, x_b0 + Decim('1.5'), by_max))
#..............................................................................


#------------------------------------------------------------------------------
def layer_contents_handler(mo2, cur_lay_inf, cur_pair_lay_num,
                            top_side, flip_lay_inf):

    if result_type == 'sbor' and cur_lay_inf['type'] == 'Signal':
        return

    t = mo2.group()
    ts = None
    tf = None

    if result_type != 'flip' and (not cur_pair_lay_num or top_side):
        ts = re.sub(pat_pte, change_pt_shift, t)

    if result_type == 'flip' or not cur_pair_lay_num or not top_side:
        tf = re.sub(pat_pte, change_pt_flip, t)
        if mo2.group('name') == 'triplePointArc':
            x = tf.split(') (', 3)
            x[1], x[2] = x[2], x[1]
            tf = ') ('.join(x)

    if result_type != 'flip' and not cur_pair_lay_num:
        cur_lay_inf['out'].append(ts)
        cur_lay_inf['out'].append(tf)
    elif result_type != 'flip' and top_side:
        cur_lay_inf['out'].append(ts)
    else:
        flip_lay_inf['out'].append(tf)
#..............................................................................


#------------------------------------------------------------------------------
#noinspection PyUnusedLocal
def h_text(mo2, cur_lay_inf, cur_pair_lay_num, top_side, flip_lay_inf):

    t = mo2.group()

    if result_type != 'flip':
        ts = re.sub(pat_pte, change_pt_shift, t, 1)
        cur_lay_inf['out'].append(ts)

    tf = re.sub(pat_pte, change_pt_flip, t, 1)
    # Удаляем зеркальность, если есть
    tf, flipen = re.subn(r'(?msu) ?\(isFlipped True\)', '', tf, 1)

    if not flipen:  # Добавляем зеркальность, если нет
        tf = re.sub(r'(?msu)\(textStyleRef ".*?"\) \(rotation [^)]+\)|'
                r'\(textStyleRef ".*?"\)',
                r'\g<0> (isFlipped True)', tf, 1)
    flip_lay_inf['out'].append(tf)
#..............................................................................


#------------------------------------------------------------------------------
#noinspection PyUnusedLocal
def h_field(mo2, cur_lay_inf, cur_pair_lay_num, top_side, flip_lay_inf):

    t = mo2.group()

    if result_type != 'flip':
        ts = re.sub(pat_pte, change_pt_shift, t, 1)
        cur_lay_inf['out'].append(ts)

    tf = re.sub(pat_pte, change_pt_flip, t, 1)
    # Удаляем зеркальность, если есть
    tf, flipen = re.subn(r'(?msu) ?\(isFlipped True\)', '', tf, 1)

    if not flipen:  # Добавляем зеркальность, если нет
        tf = re.sub(r'(?msu)\(pt [^)]+\) \(rotation [^)]+\)|\(pt [^)]+\)',
                r'\g<0> (isFlipped True)', tf, 1)
    flip_lay_inf['out'].append(tf)
#..............................................................................

rez = None
start_ind = None


#------------------------------------------------------------------------------
def get_inf_multilay(t):
    global start_ind, rez

    mo1 = re.search(  # Перебираем слои с содержимым
                r'(?msu)^  \(multiLayer .*?(?=^  \()', t)
    rez = [t[:mo1.start()], '  (multiLayer \r\n']

    for mo2 in re.finditer(  # Запоминаем элементы слоя
            r'(?msu)^    \((?P<name>\w+).*?^'
            r'(?=  \)|    \()(?!    \(patternGraphicsNameRef)', mo1.group()):
        # Перебираем и обрабатываем элементы слоя
        try:  # Обработчик по имени элемента
            handler = eval('h_' + mo2.group('name'))
        except NameError:  # Обработчик по умолчанию для остальн элементов
            handler = multi_layer_handler
        handler(mo2)
    rez.append('  )\r\n')
#..............................................................................


#------------------------------------------------------------------------------
def multi_layer_handler(mo2):
    global rez

    if result_type == 'flip':
        tf = re.sub(pat_pte, change_pt_flip, mo2.group())
        rez.append(tf)
#..............................................................................


#------------------------------------------------------------------------------
def h_via(mo2):
    global rez

    if result_type == 'sbor':
        return

    t = mo2.group()

    if result_type != 'flip':
        ts = re.sub(pat_pte, change_pt_shift, t, 1)
        rez.append(ts)

    tf = re.sub(pat_pte, change_pt_flip, t, 1)
    # Удаляем зеркальность, если есть
    tf, flipen = re.subn(r'(?msu) ?\(isFlipped True\)', '', tf, 1)

    if not flipen:  # Добавляем зеркальность, если нет
        tf = re.sub(r'(?msu)\(pt [^)]+\) \(rotation [^)]+\)|\(pt [^)]+\)',
                r'\g<0> (isFlipped True)', tf, 1)
    rez.append(tf)
#..............................................................................


#------------------------------------------------------------------------------
def h_pad(mo2):
    global rez

    t = mo2.group()

    if result_type != 'flip':
        ts = re.sub(pat_pte, change_pt_shift, t, 1)
        rez.append(ts)

    tf = re.sub(pat_pte, change_pt_flip, t, 1)
    # Удаляем зеркальность, если есть
    tf, flipen = re.subn(r'(?msu) ?\(isFlipped True\)', '', tf, 1)

    if not flipen:  # Добавляем зеркальность, если нет
        tf = re.sub(r'(?msu)\(pt [^)]+\) \(rotation [^)]+\)|\(pt [^)]+\)',
                r'\g<0> (isFlipped True)', tf, 1)
    rez.append(tf)
#..............................................................................


#------------------------------------------------------------------------------
def h_pattern(mo0):
    global rez

    t = mo0.group()
    """mo = re.search( r'(?msu)^    \(pattern(?: \([^\)]+\)){3}'
                    r'(?: \(rotation [^\)]+\))?'
                    r'(?P<isFlipped> \(isFlipped True\))?.*?'
                    r'\(patternGraphicsNameRef "(?P<Graphics>[^"]*)"\)', t)"""

    mo = re.search( r'(?msu)^    \(pattern'
                    r'(?: \([^"]+"[^"]+"\)){2}'
                    r'(?: \([^\)]+\))'
                    r'(?: \(rotation [^\)]+\))?'
                    r'(?P<isFlipped> \(isFlipped True\))?.*?'
                    r'\(patternGraphicsNameRef "(?P<Graphics>[^"]*)"\)', t)

    flipen = mo.group('isFlipped')
    ts = None
    tf = None

    # Двухсторонние (проще все) компоненты необходимо дублировать.

    if result_type != 'flip' and not flipen or result_type == 'sbor_cu':
        # Получаем смещённый вариант компонента
        ts = re.sub(pat_pte, change_pt_shift, t, 1)  # шифт координаты

    if flipen or result_type != 'sbor':
        # Начинаем получение отражённого варианта компонента ...

        mo1 = re.search(
            r'(?msu)^        \(patternGraphicsNameRef "%s"\).*?^      \)' %
            re.escape(mo.group('Graphics')), t)

        tmp = []
        d = 0

        # Перебор всех атрибутов
        for mo2 in re.finditer(r'(?msu)^        \(attr "'
                                r'[^\n]*\n', mo1.group()):

            # Удаляем зеркальность, если есть
            tf2, flipen2 = re.subn(r'(?msu) ?\(isFlipped True\)',
                                    '', mo2.group(), 1)

            if not flipen2:  # Добавляем зеркальность, если нет
                tf2 = re.sub(r'(?u)^.*? \(rotation [^)]+\)|'
                                 r'^.*? \(pt [^)]+\)|'
                                 r'^.*? \(attr "[^"]+" "[^"]+"',
                                 r'\g<0> (isFlipped True)', tf2, 1)

            if ' (pt 0.0 ' in tf2:
                pass
            elif ' (pt -' in tf2:
                tf2 = tf2.replace(' (pt -', ' (pt ', 1)
            elif ' (pt ' in tf2:
                tf2 = tf2.replace(' (pt ', ' (pt -', 1)

            #t2 = mo2.group()
            tmp.append(t[d:mo1.start() + mo2.start()] + tf2)
            d = mo1.start() + mo2.end()

        tmp.append(t[d:])
        tf = ''.join(tmp)


        if flipen:  # Удаляем зеркальность, если есть
            tf = re.sub(r'(?msu) ?\(isFlipped True\)', '', tf, 1)
        else:  # Добавляем зеркальность, если нет
            tf = re.sub(r'(?msu)\(pt [^)]+\) \(rotation [^)]+\)|\(pt [^)]+\)',
                    r'\g<0> (isFlipped True)', tf, 1)

        tf = re.sub(pat_pte, change_pt_flip, tf, 1)  # флип координаты
    # ... Отражённый вариант компонента получен

    if result_type == 'flip' or flipen:
        # Компоненты БОТ стороны необходимо: - перенести с переворотом
        rez.append(tf)                     #   на ТОП слой БОТ фрагмента
        if result_type == 'sbor_cu':  # - дублировать со смещениеи
            rez.append(re.sub(r'(?u)\(refDesRef "([^"]+)',
                    r'(refDesRef "%s\g<1>' % DOP_RD_PREFIX, ts, 1))
    else:  # Компоненты ТОП стороны необходимо: - сместить
        rez.append(ts)
        if result_type == 'sbor_cu':
            # - дублировать с переворотом на БОТ слой БОТ фрагмента
            rez.append(re.sub(r'(?u)\(refDesRef "([^"]+)',
                    r'(refDesRef "%s\g<1>' % DOP_RD_PREFIX, tf, 1))
#..............................................................................


#------------------------------------------------------------------------------
def new_lays(t):
    global rez
    for lay_num in inf_lays:

        if inf_lays[lay_num]['out']:
            rez += ['  (layerContents (layerNumRef %s)\r\n' % lay_num
                                ] + inf_lays[lay_num]['out'] + ['  )\r\n']
    rez.append(t[end_ind:])
    return ''.join(rez)
#..............................................................................


#------------------------------------------------------------------------------
def execute(fpne):
    global mirror_const, measdef

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    # Неотображение цепей
    t = re.sub(r'(?msu)^(  \(net "[^"]*" ).*?\r\n',
                r'\g<1>(isVisible False) \r\n', t)

    # Удаление outline
    t = re.sub(r'(?msu)^    \(boardOutlineObj .*?(?=^  (?:  \(|\)))', '', t)

    # Удаление infoPoint
    t = re.sub(r'(?msu)^    \(infoPoint .*?(?=^  (?:  \(|\)))', '', t)

    # Вычисл смещений сторон плат и допустимого размера листа
    t = get_pcb_params(t)

    # Получение информации из слоёв
    get_inf_multilay(t)
    get_inf_lays(t)

    t = new_lays(t)

    # Включение текущим ТОП-слой, отключение неосновных
    if result_type == 'flip':
        tmp_lay = (1,2,3,6,10,11)
    else:
        tmp_lay = (1,3,6,10)
    t = re.sub(r'(?msu)^    \(layerState .*?^    \).\n',
        '    (layerState \r\n'
        '      (currentLayer (layerNumRef 1))\r\n' + ''.join([
        '      (layerDisabled (layerNumRef %s))\r\n' % k
                for k, v in inf_lays.items()
                if int(k) not in tmp_lay]) +
        '    )\r\n', t)

    # Дублирование компонентов в Netlist-е
    # и цепей к ним
    if result_type == 'sbor_cu':
        t = re.sub(r'(?msu)^  \(compInst "(.*?^  \)\r\n)',
                    r'\g<0>  (compInst "%s\1' % DOP_RD_PREFIX, t)
        t = re.sub(r'(?msu)^    \(node "(.*?\)\r\n)',
                    r'\g<0>    (node "%s\1' % DOP_RD_PREFIX, t)

    # Новые установки печати
#    import pcbprintsettings
    t = re.sub(r'(?msu)'
                r'^  \(pcbPrintSettings .*?'
                r'^  \).\n', pcbPrintSettings, t)

    # Сохранить с инструкциями.
    fpn = re.sub(r'(?u)_ASCII$', '', splitext(fpne)[0])
    if result_type == 'swap':
        fpne_out = fpn + '_SWAP.PCB'
    if result_type == 'flip':
        fpne_out = fpn + '_FLIP.PCB'
    elif result_type == 'sbor_cu':
        fpne_out = fpn + '_СБ+.PCB'
    else:  # result_type == 'sbor':
        fpne_out = fpn + '_СБ.PCB'
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#------------------------------------------------------------------------------
def ley_clear(mo):
    if int(mo.group('num')) > 11:
        return ''
    return mo.group()
#..............................................................................


#------------------------------------------------------------------------------
def ley_clear2(mo):
    if int(mo.group('num')) > 11:
        return ''
    return mo.group(1)
#..............................................................................


#------------------------------------------------------------------------------
def clear(fpne):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    # Удаление содержимого нестанд слоёв из графики компонентов
    t = re.sub(r'(?msu)^      \(layerContents  \(layerNumRef  (?P<num>\d+)\)'
                r'.*?^      \)..^', ley_clear, t)
    # Удаление содержимого нестанд слоёв из проекта
    t = re.sub(r'(?msu)(^  \(layerContents \(layerNumRef (?P<num>\d+)\)'
                r'.*?^  \)..^)', ley_clear2, t)
    # Удаление почти ненужных настроек и состояний проекта
    t = re.sub(r'(?msu)^  \(pcbPrintSettings .*?'
                r'(?=^\))', '', t)
    # Удаление определений нестанд слоёв из проекта
    t = re.sub(r'(?msu)^  \(layerDef "[^"]*".*?'
                r'^    \(layerNum (?P<num>\d+)\).*?'
                r'^  \)..^', ley_clear, t)

#    # Удаление .....................
#    t = re.sub(r'(?msu)^    \(fromTo [^\n]*\n', '', t)
#
#    # Удаление цепей и классов цепей
#    t = re.sub(r'(?msu)^  \((?:net|netClass) ".*?^  \).*?^', '', t)
#
#    # Удаление ссыдок на цепи
#    t = re.sub(r'(?msu) \(netNameRef "[^"]*"\)', '', t)

    # Удаление outline
    t = re.sub(r'(?msu)^    \(boardOutlineObj .*?(?=^  (?:  \(|\)))', '', t)

    # Удаление infoPoint
    t = re.sub(r'(?msu)^    \(infoPoint .*?(?=^  (?:  \(|\)))', '', t)

    # Включение текущим ТОП-слой, отключение всех нижних
    t = re.sub(r'(?msu)^    \(layerState .*?^    \).\n',
            '    (layerState \r\n'
            '      (currentLayer (layerNumRef 1))\r\n'
            '    )\r\n', t)

    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + '_CLEAR.PCB'
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
    #else:
    #    os.system('wine "/media/leon/A8B8D14DB8D11B20/Program Files/P-CAD 2006/pcb.exe" "D:\\WORK\\WORK-MLM\Themes\\+22_WZ-7A\\rab2-ЮС\\ЮС3.082.674V2_СБ.PCB"')
#7904|7981<-os.spawnv(os.P_NOWAIT, '/usr/bin/wine', ['/usr/bin/wine', "/media/leon/A8B8D14DB8D11B20/Program Files/P-CAD 2006/pcb.exe", "D:\\WORK\\WORK-MLM\Themes\\+22_WZ-7A\\rab2-ЮС\\ЮС3.082.674V2_СБ.PCB"])
#(0, 0)|(8358, 0)<-os.waitpid(8358, os.WNOHANG)
#0<-os.spawnv(os.P_WAIT, '/usr/bin/wine', ['/usr/bin/wine', "/media/leon/A8B8D14DB8D11B20/Program Files/P-CAD 2006/pcb.exe", "D:\\WORK\\WORK-MLM\Themes\\+22_WZ-7A\\rab2-ЮС\\ЮС3.082.674V2_СБ.PCB"])
#...args = shlex.split('wine "/media/leon/A8B8D14DB8D11B20/Program Files/P-CAD 2006/pcb.exe" "D:\\WORK\\WORK-MLM\Themes\\+22_WZ-7A\\rab2-ЮС\\ЮС3.082.674V2_СБ.PCB"')
#..............................................................................


#------------------------------------------------------------------------------
def rd2_assy(fpne):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    st = 0  # Начальное состояния
    ts = []
    for s in t.split(PCAD_LINESEP):

        if st == 3:
            ts.append(s)
            continue

        if st == 0:
            ts.append(s)
            if s == '      (layerContents  (layerNumRef  6)':
                st = 1  # Внимание! м.б. рефдес2
                rd = ''
            elif s.startswith('  (compDef "'):
                st = 3  # Закончилось
            continue

        if s.startswith('        (attr "RefDes2" "'):
            rd = s
            continue

        ts.append(s)
        if s == '      (layerContents  (layerNumRef  10)':
            if rd:
                ts.append(rd)
            st = 0  # возвращаемся к поиску


    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + '_assy.PCB'
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(PCAD_LINESEP.join(ts).encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#------------------------------------------------------------------------------
def gerb_opt(fpne):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    pcb_dir = split(fpne)[0]
    gerb_dir = join(pcb_dir, 'GERB')
    if not exists(gerb_dir):
        os.mkdir(gerb_dir)

    gerb_dir = gerb_dir.replace('\\', '\\'*4).replace('/', '\\'*4)

    fi = open(join(split(sys.argv[0])[0], 'grb_opt.pcb.txt'))
    gerb_opt_str = fi.read().decode(PCAD_CODE) % gerb_dir
    fi.close()
    fi = open(join(split(sys.argv[0])[0], 'drl_opt.pcb.txt'))
    drl_opt_str = fi.read().decode(PCAD_CODE) % gerb_dir
    fi.close()

    t = re.sub(r'(?msu)'
            '^  \(gerberSettings.+?^  \).?\n'
            , gerb_opt_str, t)
    t = re.sub(r'(?msu)'
            '^  \(ncDrillSettings.+?^  \).?\n'
            , drl_opt_str, t)

    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + '_gerb_opt.PCB'
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#------------------------------------------------------------------------------
def uncopy_rd5(m):
    t = m.group()
    m2 = re.search(r'(?sm)^        \(attr "RefDes5" ".*?"(.*?\r\n)', t)
    if m2:
        t = re.sub(r'(?sm)(^        \(attr "RefDes" ".*?").*?\r\n',
               r'\1%s' % m2.group(1), t)
    return t
#..............................................................................


#------------------------------------------------------------------------------
def manip_rd5(fpne, mode):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    t = re.sub(r'(?sm)'
                r'^      \(layerContents|patternGraphicsRef .*?'
                r'^      \)\r\n', uncopy_rd5, t)

    # Удаление RefDes5
    t = re.sub(r'    (?:    )?\(attr "RefDes5" .*?\r\n', '', t)

    if mode == 'add_rd5':
        # Копирование в RefDes5
        t = re.sub( r'(        \(attr "RefDes" (.*?\r\n))',
                   r'\1        (attr "RefDes5" \2', t)

        # Отклюыение видимости RefDes
        t = re.sub(r'(        \(attr "RefDes" .+?) \(isVisible True\)(.*?\r\n)',
                  r'\1\2', t)

    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + ('_rd5.PCB' if mode == 'add_rd5' else '_drd5.PCB')
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#------------------------------------------------------------------------------
def pgd_copy_rd2(m):
    t = m.group()   # исходный текст группы

    for k in (10, 11):
        if (re.search((r'(?sm)'
                r'^      \(layerContents  \(layerNumRef  %s\)\r\n'     '.*?'
                r'^        \(attr "RefDes2" .*?\r\n'                   '.*?'
                r'^      \)\r\n') % k, t)):
            return t   # Если RefDes2 уже есть

    # Ищем исходный RefDes
    for k in (6, 7):
        m = re.search((r'(?sm)'
            r'^      \(layerContents  \(layerNumRef  %s\)\r\n'      '.*?'
            r'^(        \(attr "RefDes" .*?\r\n)'                  '.*?'
            r'^      \)\r\n') % k, t)
        if m:
            # формирование текста attr RefDes2
            rd2 = m.group(1).replace('RefDes', 'RefDes2', 1)
            break
    else:
        return t   # Если RefDes нет (чудо)

    # Пытаемся добавить attr RefDes2 в существующий слой
    t, n = re.subn((r'(?sm)'
        r'^(      \(layerContents  \(layerNumRef  %s\)\r\n)') %
        (k + 4), r'\1' + rd2, t)

    if n:    # Получилось
        return t

    # Создадим требуемый слой с attr RefDes2
    return re.sub((r'(?sm)'
        r'^(      \(layerContents  \(layerNumRef  %s\)\r\n'      '.*?'
        r'^      \)\r\n)') % k,
        (r'\1      (layerContents  (layerNumRef  %s)\r\n'
        r'%s'
        r'      )\r\n') % (k + 4, rd2), t)
#..............................................................................


#------------------------------------------------------------------------------
def pgr_copy_rd2(m):
    t = m.group()   # исходный текст группы

    if re.search(r'(?sm)^        \(attr "RefDes2" .*?\r\n', t):
        return t   # Если RefDes2 уже есть

    # добавляем attr RefDes2 после RefDes
    return re.sub(r'(?sm)^((        \(attr "RefDe)s(" .*?\r\n))',
               r'\1\2s2\3', t)
#..............................................................................


#------------------------------------------------------------------------------
def add_rd2(fpne, mode):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    # Копирование RefDes в RefDes2 во всех фрагментах patternGraphics-Def
    t = re.sub(r'(?sm)'
                r'^    \(patternGraphicsDef \r\n'   '.*?'
                r'^    \)\r\n', pgd_copy_rd2, t)

    # Копирование RefDes в RefDes2 во всех фрагментах patternGraphics-Ref
    t = re.sub(r'(?sm)'
                r'^      \(patternGraphicsRef \r\n'   '.*?'
                r'^      \)\r\n', pgr_copy_rd2, t)

    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + ('_rd2.PCB' if mode == 'add_rd2' else '_drd2.PCB')
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#------------------------------------------------------------------------------
def manip_rd2(fpne, mode):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return


    # Удаление RefDes2
    t = re.sub(r'    (?:    )?\(attr "RefDes2" .*?\r\n', '', t)

    if mode == 'add_rd2':
        # Копирование в RefDes2
##        t = re.sub(r'(?sm)'
##                    r'^      \(layerContents|patternGraphicsRef .*?'
##                    r'^      \)\r\n', copy_rd2, t)

        # Копирование в RefDes2
        t = re.sub( r'(        \(attr "RefDes" (.*?\r\n))',
                   r'\1        (attr "RefDes2" \2', t)

        # Отклюыение видимости RefDes2
        t = re.sub(r'(        \(attr "RefDes2" .+?) \(isVisible True\)(.*?\r\n)',
                  r'\1\2', t)

    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + ('_rd2.PCB' if mode == 'add_rd2' else '_drd2.PCB')
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................
"""
    (pattern (patternRef "SMA_1") (refDesRef "VD2") (pt 55.88 50.8) (patternGraphicsNameRef "Primary")
      (patternGraphicsRef
        (patternGraphicsNameRef "Primary")
        (attr "Type" "1N4007-M7_SMA" (rotation 90.0) (justify Center) (textStyleRef "PT") )
        (attr "RefDes5" "VD2" (pt 0.0 3.81) (textStyleRef "PRD") )
        (attr "RefDes2" "RefDes2" (pt 0.0 3.175) (rotation 90.0) (isVisible True) (justify Left) (textStyleRef "PRD2") )
        (attr "RefDes" "VD2" (pt 0.0 3.81) (rotation 90.0) (isVisible True) (justify Left) (textStyleRef "PRD") )
      )
    )

    (pattern (patternRef "SMA_1") (refDesRef "VD2") (pt 55.88 50.8) (patternGraphicsNameRef "Primary")
      (patternGraphicsRef
        (patternGraphicsNameRef "Primary")
        (attr "Type" "1N4007-M7_SMA" (rotation 90.0) (justify Center) (textStyleRef "PT") )
        (attr "RefDes" "VD2" (pt 0.0 3.81) (rotation 90.0) (isVisible True) (justify Left) (textStyleRef "PRD") )
        (attr "RefDes5" "VD2" (pt 0.0 3.81) (textStyleRef "PRD") )
        (attr "RefDes2" "RefDes2" (pt 0.0 3.175) (rotation 90.0) (isVisible True) (justify Left) (textStyleRef "PRD2") )
      )
    )

r'    (pattern (patternRef ".*?\r\n'
r'        (attr "RefDes" "VD2" (pt 0.0 3.81) (rotation 90.0) (justify Left) (textStyleRef "PRD") ).*?\r\n'
r'        (attr "RefDes5" "VD2".*? (isVisible True).*?\r\n'
r'    )\r\n'

r'    (pattern (patternRef ".*?\r\n'
r'        (attr "RefDes5" "VD2" (pt 0.0 3.81) (isVisible True) (textStyleRef "PRD") ).*?\r\n'
r'        (attr "RefDes" "VD2" (pt 0.0 3.81) (rotation 90.0) (justify Left) (textStyleRef "PRD") ).*?\r\n'
r'    )\r\n'
"""

#------------------------------------------------------------------------------
def ley_clear(mo):
    n = int(mo.group('num'))
    if n > 11:
        return ''
    if n == 2 or n == 1:
        t = re.sub(r'(?msu)^    \(line \(pt [^\n]*\n', '', mo.group())
        t = re.sub(r'(?msu)^    \(pcbPoly .*?^    \)..^', '', t)
        t = re.sub(r'(?msu)^    \(polyCutOut .*?^    \)..^', '', t)
        t = re.sub(r'(?msu)^    \(copperPour95 .*?^    \)..^', '', t)
        return t
    return mo.group()
#..............................................................................


#------------------------------------------------------------------------------
def clear_nets(fpne):

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    # Удаление содержимого нестанд слоёв из графики компонентов
    t = re.sub(r'(?msu)^      \(layerContents  \(layerNumRef  (?P<num>\d+)\)'
                r'.*?^      \)..^', ley_clear, t)
    # Удаление содержимого нестанд слоёв из проекта
    t = re.sub(r'(?msu)^  \(layerContents \(layerNumRef (?P<num>\d+)\)'
                r'.*?^  \)..^', ley_clear, t)
    # Удаление почти ненужных настроек и состояний проекта
    t = re.sub(r'(?msu)^  \(pcbPrintSettings .*?'
                r'(?=^\))', '', t)
    # Удаление определений нестанд слоёв из проекта
    t = re.sub(r'(?msu)^  \(layerDef "[^"]*".*?'
                r'^    \(layerNum (?P<num>\d+)\).*?'
                r'^  \)..^', ley_clear, t)

    # Удаление .....................
    t = re.sub(r'(?msu)^    \(fromTo [^\n]*\n', '', t)

    # Удаление .....................
    t = re.sub(r'(?msu)^    \(via [^\n]*\n', '', t)

    # Удаление цепей и классов цепей
    t = re.sub(r'(?msu)^  \((?:net|netClass) ".*?^  \).*?^', '', t)

    # Удаление ссыдок на цепи
    t = re.sub(r'(?msu) \(netNameRef "[^"]*"\)', '', t)

    # Удаление outline
    t = re.sub(r'(?msu)^    \(boardOutlineObj .*?(?=^  (?:  \(|\)))', '', t)

    # Удаление infoPoint
    t = re.sub(r'(?msu)^    \(infoPoint .*?(?=^  (?:  \(|\)))', '', t)

    # Включение текущим ТОП-слой, отключение всех нижних
    t = re.sub(r'(?msu)^    \(layerState .*?^    \).\n',
            '    (layerState \r\n'
            '      (currentLayer (layerNumRef 1))\r\n'
            '    )\r\n', t)
    #return

    # Сохранить с инструкциями.
    fpne_out = splitext(fpne)[0] + '_net_del.PCB'
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем
    fh_out.write(t.encode(PCAD_CODE))
    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#-------------------------------------------------------------------------------
def check_one_sch(fRefDes, fEmptyValue, fValue):#InL):
    """Обработывает текст файла "*.sch" """
    global count_v, count_ev, count_rd2

    netlist  = False
    compInst = False
    addL = []

    for i, sIn in enumerate(InL):

        if not netlist:
            if sIn.startswith('(netlist "'):
                netlist = True # Начался раздел netlist
            continue

        if sIn == u")":
            netlist = False # Закончился раздел netlist
            continue

        if not compInst:
            stmp = '  (compInst "'
            if sIn.startswith(stmp):
                compInst = True # Начался раздел compInst
                sRefDes = sIn[len(stmp):-1] # Запомнить значение RefDes
            continue

        if sIn == u"  )":
            compInst = False; # Закончился раздел compInst
            continue

        stmp = '    (attr "RefDes2" "'
        if sIn.startswith(stmp):  # Подставить в RefDes2 значение RefDes
            if not fRefDes:
                continue
            InL[i] = stmp + sRefDes + sIn[sIn.find('"', len(stmp)):]
            count_rd2 += 1
            continue

        stmp = '    (originalName "'
        if not sIn.startswith(stmp): continue

        sType = sIn[len(stmp):-2]   # Type

        sIn = InL[i + 1]

        stmp = '    (compValue "'
        if not sIn.startswith(stmp):
            # если нет атр Value, добавить атр Value с знач sType (потом)
            if not fValue:
                continue
            addL.insert(0, (i + 1, stmp + sType + '")'))
            count_ev += 1
            continue

        # очередная строка с атрибутом Value ?
        sValue = sIn[len(stmp):-2] # значение атрибута Value
        if fEmptyValue and ('value' in sValue.lower() or
                sValue.strip() == ''):
            InL[i + 1] = stmp + sType + '")' # заменить значение на sType
            count_v += 1

    for i, s in addL:
        InL.insert(i, s)


#-------------------------------------------------------------------------------
def check_one_pcb(fRefDes, fEmptyValue):#InL):
    """Обработывает текст файла "*.pcb" """
    global count_rd2, count_rd3, count_rd4, count_rd5

    pcbDesign          = False
    multiLayer         = False
    pattern            = False
    patternGraphicsRef = False

    for i, sIn in enumerate(InL):

        if not pcbDesign:
            if sIn.startswith('(pcbDesign "'):
                pcbDesign = True # Начался раздел pattern pcbDesign
            continue

        if sIn == u")":
            pcbDesign = False # Закончился раздел pcbDesign
            continue

        if not multiLayer:
            if sIn == '  (multiLayer ':
                multiLayer = True # Начался раздел pattern multiLayer
            continue

        if sIn == u"  )":
            multiLayer = False # Закончился раздел multiLayer
            continue

        if not pattern:
            if sIn.startswith('    (pattern (patternRef "'):
                pattern = True # Начался раздел pattern
                stmp = '(refDesRef "'
                pos = sIn.find(stmp) + len(stmp)
                sRefDes = sIn[pos:sIn.find('"', pos)] # Запомнить знач RefDes
            continue

        if sIn == u"    )":
            pattern = False # Закончился раздел pattern
            continue

        if not patternGraphicsRef:
            if sIn == '      (patternGraphicsRef ':
                patternGraphicsRef = True # Начался раздел patternGraphicsRef
            continue

        if sIn == u"      )":
            patternGraphicsRef = False # Закончился раздел patternGraphicsRef
            continue

        stmp = '        (attr "RefDes2" "'
        if sIn.startswith(stmp): # Подставить в RefDes2 RefDes
            if not fRefDes:
                continue
            InL[i] = stmp + sRefDes + sIn[sIn.find('"', len(stmp)):]
            count_rd2 += 1
            continue

        stmp = '        (attr "RefDes3" "'
        if sIn.startswith(stmp): # Подставить в RefDes3 RefDes
            if not fRefDes:
                continue
            InL[i] = stmp + sRefDes + sIn[sIn.find('"', len(stmp)):]
            count_rd3 += 1
            continue

        stmp = '        (attr "RefDes4" "'
        if sIn.startswith(stmp): # Подставить в RefDes3 RefDes
            if not fRefDes:
                continue
            InL[i] = stmp + sRefDes + sIn[sIn.find('"', len(stmp)):]
            count_rd4 += 1

        stmp = '        (attr "RefDes5" "'
        if sIn.startswith(stmp): # Подставить в RefDes3 RefDes
            if not fRefDes:
                continue
            InL[i] = stmp + sRefDes + sIn[sIn.find('"', len(stmp)):]
            count_rd5 += 1
#..............................................................................


#------------------------------------------------------------------------------
def copy_atr(fpne, fRefDes=True, fEmptyValue=True, fValue=False):
    """Проверяет, подготавливает к обработке и сохраняет текст каждого файла"""
    global InL#, FInName
    global count_v, count_ev
    global count_rd2, count_rd3, count_rd4, count_rd5
    #FInName = FInName_

    # Проверка типов файлов.
    # Преобразовывание в ASCII, если необходимо.
    # Считывание файла
    t = read_pcad_file(fpne)
    if not t:
        printm('\n   Нет текста платы.\n')
        return

    InL = t.split(PCAD_LINESEP)
    fpn, ext = splitext(fpne)
    ext = ext[1:].upper()

    count_v = 0
    count_ev = 0
    count_rd2 = 0
    count_rd3 = 0
    count_rd4 = 0
    count_rd5 = 0

    # Проверка типа файла
    if ext == u"SCH":
        check_one_sch(fRefDes, fEmptyValue, fValue)
    elif ext == u"PCB":
        check_one_pcb(fRefDes, fEmptyValue)
    else:
        printm('  Это не "*.SCH" или "*.PCB" файл\n')
        return

    printm('  Содержимое файла обработано:\n')
    printm('    создано %s Value,\n' % count_v)
    printm('    скопировано %s Value,\n' % count_ev)
    printm('    скопировано %s RefDes2,\n' % count_rd2)

    if ext == u"PCB":
        printm('    скопировано %s RefDes3,\n' % count_rd3)
        printm('    скопировано %s RefDes4.\n' % count_rd4)
        printm('    скопировано %s RefDes5.\n' % count_rd5)

    # Сохранить с инструкциями.
    fpne_out = fpn + '_atr.' + ext
    fh_out = open(fpne_out, 'wb')  # Возможно обрамить Тру Кечем

    #fh_out.write(t.encode(PCAD_CODE))
    #fh_out.write(PCAD_LINESEP.join(ts).encode(PCAD_CODE))
    fh_out.write(PCAD_LINESEP.join(InL).encode(PCAD_CODE))

    fh_out.close()
    printm('\n  Файл обработан и сохранён с именем:\n' +
        '%s\n' % fpne_out.replace('/', '\\'))

    if re.match(r'win(32|64)', sys.platform):
        os.startfile(fpne_out)
#..............................................................................


#------------------------------------------------------------------------------
def run_mode(mode, fpne):
    global result_type
    result_type = mode

    if mode == 'sbor_cu' or mode == 'sbor' or mode == 'flip':
        execute(fpne)
    elif mode == 'clear':
        clear(fpne)
    elif mode == 'clear_nets':
        clear_nets(fpne)
    elif mode == 'rd2_assy':
        rd2_assy(fpne)
    elif mode == 'gerb_opt':
        gerb_opt(fpne)
    elif mode == 'copy_atr':
        copy_atr(fpne)
    elif mode == 'add_rd2':
        add_rd2(fpne, mode)
    elif mode == 'add_rd5':
        manip_rd5(fpne, mode)
    elif mode == 'del_rd5':
        manip_rd5(fpne, mode)
#..............................................................................


#------------------------------------------------------------------------------
def main(args):
    pass

    # Поиск программ для преобразования в ASCII.
    #complete_exts()

    # Перебираем все файлы.
    for fpne in args:
        #execute(fpne)
        run_mode('clear', fpne)

#..............................................................................

pcbPrintSettings = (
u"""  (pcbPrintSettings
  )
""")


#------------------------------------------------------------------------------
if __name__ == '__main__':
    common.pyscr = 'pyscripter' in dir()

    # Проверяем количество аргументов (если надо, генерим BAT-файл).
    _n_args = 1
    common.main0(main, _n_args)  # Нет необходимости трогать
#..............................................................................

