#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""    Программа pcad_univ_tk.py - графическая оболочка для
    программы-модуля pcad_univ_cp.py (командной строки) для получения
    заготовок файлов "Перечня элементов" и "Спецификации" из PCB-файла. """

#                Автор: Л.М.Матвеев

import common
common.pyscr = True    # False     # 'pyscripter' in dir()
from common import trm_code, pyscr
import sys


#------------------------------------------------------------------------------
def printm(s):
    """ Печать Юникод-строк в терминал и скриптер.
        Автоматический перевод строки не производится. """

    if pyscr:# or True:
        sys.stdout.write(s)
    else:
        sys.stdout.write(s.encode(trm_code))
    if prn_only:
        return
    txt.insert(END, s)
    txt.yview(END)
    root.update()
#..............................................................................
prn_only = True
# Переопределение функции печати
common.printm = printm

from os.path import join, split  #, splitext, exists

from tkinter import *
from tkinter import filedialog
# from   Tkinter import *
# import tkFileDialog   # filedialog

try:
    from ini import last_open, last_check
    last_open = last_open
    last_check = last_check
except ImportError:
    last_open = ''#splitext(__file__)[0] + '.pcb'
    last_check = ' '


import pcad_univ_cp


#------------------------------------------------------------------------------
def save_old_values():
    """"""
    prg_code = 'utf-8'
    ss = ['# -*- coding: %s -*-\n\n' % prg_code,
            'last_open = r"%s"\n\n' % last_open,
            'last_check = "%s"\n\n' % mode_str.get()]

    ini_file_name = join(split(__file__)[0], 'ini.py')
    #ini_file_name ='_'.join(splitext(ini_file_name))  # Для отладки
    fd = open(ini_file_name, 'wb')
    fd.write(''.join(ss).encode(prg_code))
    fd.close()
    printm('\n    Сохранение файла состояния произведено.\n')
    printm('    %s\n' % ini_file_name.replace('/', '\\'))
#..............................................................................


#------------------------------------------------------------------------------
root = Tk()
root.title('  Нестандартные операции с PCB-файлами.')
root.resizable(False, False)  # запрет изм разм окна по гориз и по верт


fra1 = LabelFrame(root, text=' Лог операций ', labelanchor='n')
fra1.pack()
txt = Text(fra1, font="Verdana 10")
scr = Scrollbar(fra1, command=txt.yview)
txt.configure(yscrollcommand=scr.set)
scr.grid(row=0, column=1, sticky=NS, padx=3, pady=3)
txt.grid(row=0, column=0, padx=3, pady=4)

edval = StringVar(value=last_open)


#------------------------------------------------------------------------------
def select_file():
    """ Выбор файла (и т.п.) """
    global last_open

    fp, fne = split(last_open)
    if not fp:
        fp = None
    if not fne:
        fne = None

    fpne2 = filedialog.askopenfilename(initialdir=fp,
            title = 'Выбор исходного файла',
            filetypes = [('PCB-файл', '*.PCB')]
                if mode_str.get() != 'copy_atr'
                else [('PCAD-файл', ('*.SCH', '*.PCB')),],
            initialfile = fne)

    if fpne2:
        last_open = fpne2.replace('/', '\\')
        edval.set(last_open)
        edFN.xview_moveto(1)
#..............................................................................


#------------------------------------------------------------------------------
fra42 = LabelFrame(root, labelanchor='n', text=' Дополнительно ')
fra42.pack(side=LEFT)

rButts = {'sbor':{'t':'Две стороны без трасс', 'x':1, 'y':0},
            'sbor_cu':{'t':'Две стороны', 'x':0, 'y':0},
            'flip':{'t':'Отзеркаливание', 'x':0, 'y':1},
            'clear':{'t':'Очистка к изготовлению', 'x':1, 'y':1},
            'clear_nets':{'t':'Удаление цепей', 'x':0, 'y':2},
            'rd2_assy':{'t':'RefDes2 на Assy', 'x':1, 'y':2},
            'gerb_opt':{'t':'Опции Герберов', 'x':0, 'y':3},
            'copy_atr':{'t':'copy Attr', 'x':1, 'y':3},
            'add_rd2':{'t':'add RefDes2', 'x':0, 'y':4},
            #'del_rd2':{'t':'del RefDes2', 'x':1, 'y':4},
            'add_rd5':{'t':'add RefDes5', 'x':0, 'y':5},
            'del_rd5':{'t':'del RefDes5', 'x':1, 'y':5},
            }
mode_str = StringVar(value=last_check)

for k, v in rButts.items():
    rb = Radiobutton(fra42, text=v['t'], variable=mode_str, value=k)
    rb.grid(row=v['y'], column=v['x'], sticky=W)
#    rb.bind('<Button-1>')
    v['Radiobutton'] = rb
#..............................................................................


#------------------------------------------------------------------------------
fra3 = LabelFrame(root, text=' Имя файла ', labelanchor='n')
fra3.pack()

btSel = Button(fra3, text='<<', command=select_file)
#btSel.bind('<Button-1>')
btSel.grid(row=0, column=2, padx=3, pady=3)

ed_width = (txt['width'] - btSel['width'] - 10)
edFN = Entry(fra3, bd=2, textvariable=edval, width=38, state='readonly')
edFN['readonlybackground'] = edFN['background']
edFN.grid(row=0, column=0, padx=3, sticky=EW)
edFN.xview_moveto(1)

btRun = Button(fra3, text=u"Выполнить", width=10,
        command=lambda : pcad_univ_cp.run_mode(mode_str.get(), edval.get()))
#btRun.bind('<Button-1>')
btRun.grid(row=0, column=3, padx=3)
#..............................................................................

prn_only = False  # not prn_only  #
print(1)
root.mainloop()
print(2)
prn_only = True

save_old_values()
