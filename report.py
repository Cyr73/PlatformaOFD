#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import csv
from decimal import Decimal
from sys import argv
from sys import platform
from os import path
from datetime import timedelta, datetime

def mes_str(date):
   #кортеж месяцев
   month_list =('январь','февраль','март','апрель','май','июнь','июль','август','сентябрь','октябрь','ноябрь','декабрь')
   date_list = date.split('.')
   return (month_list[int(date_list[0])-1] + ' ' +date_list[1] + ' года')

def correct_Usluga(USLUGA):
   # словарь перевода наименований в отделы (ЭКР)
   norm={           'OБЩ.TУAЛET':'Общ. туалет',
                   'ABTOCTOЯHKA':'Автостоянка',        
                      'XPAHEHИE':'Хранение',
                    'ДOП.УCЛУГИ':'Доп.услуги'
        }
   if USLUGA in norm: return norm[USLUGA]
   return USLUGA

def summa_to_decimal(SUMMA):
   SUMMA=SUMMA.replace(",",".")
   return Decimal(SUMMA)

def csv_reader(file_obj):
   #Read a csv file
   reader = csv.reader(file_obj, delimiter=';')
   for row in reader:
      USLUGA=correct_Usluga(row[2]) # наименование
      SUMMA =summa_to_decimal(row[4])
      #print(USLUGA,SUMMA)
      if USLUGA in tabl: tabl[USLUGA] += SUMMA
      else: print ("Неправильное наименование:"+USLUGA+".")

def create_report():
   if len (argv) > 1: # если передан параметр в командной строке
      if len(argv[1])>7: # скорее всего передана полная дата
         mes = argv[1][-7:] # вырезаем месяц.год
      else: mes=argv[1]   # месяц.год из командной строки
   else:
      mes = (datetime.now() - timedelta(1)).strftime('%m.%Y') # если параметр не передан, месяц.год на вчера.
   if platform=="win32": file_catalog=""
   else: file_catalog="/home/cheques/"
   #кортеж отделов
   departments=('Общ. туалет','Автостоянка','Универсал. рынок','Сельхоз. ярмарка','Услуги зала','Хранение','Сезонная ярмарка', 'Доп.услуги', 'Услуги рынка')
   #print ('Дата;'+';'.join(departments)) #заголовки по кортежу
   #создаём htm файл
   htm = open(file_catalog+mes+'.htm', "w", encoding='utf-8') # если файл есть, перезапись
   #выводим заголовок в htm файл
   htm.write('<html>')
   htm.write('<head>')
   htm.write('<meta charset="utf-8">')
   htm.write('<style>')
   htm.write(' table, th, td {border: 1px solid grey;border-collapse: collapse}') 
   htm.write(' th {background-color: Silver}')
   htm.write(' td {text-align: right}') 
   #htm.write(' td:nth-last-child(1) {font-weight: bold;}') # последний столбец
   #htm.write(' tr:nth-last-child(1) {font-weight: bold;}') # последняя строка 
   htm.write('</style>')
   htm.write('</head>')
   htm.write('<body>')
   htm.write('<table>')
   htm.write('<caption>Чеки от ОФД по секциям за '+mes_str(mes)+'</caption>')
   htm.write('<tr>')
   htm.write('<th>Дата</th>')
   for dep in departments: # из кортежа
      htm.write('<th>'+dep+'</th>')
   htm.write('<th>Итого:</th>')
   htm.write('</tr>')
   itogi = {dep: 0 for dep in departments} #инициализируем словарь
   global tabl 
   j=0 #общая сумма
   for filename in sorted(glob.glob(file_catalog+"*."+mes+".csv")): #по каждому файлу
      date = path.basename(filename[:-4]) #вырезаем дату из имени файла
      tabl = {dep: 0 for dep in departments} #инициализируем словарь
      with open(filename, "r", encoding='utf-8') as f_obj: 
         csv_reader(f_obj)
      #выводим словарь по кортежу
      #print(date, *[tabl[dep] for dep in departments], sep=';') #вариант nable
      i=0 # сумма по строке
      htm.write('<tr>') #новая строка
      #выводим дату в htm файл
      htm.write('<td>'+date+'</td>')
      #выводим словарь в htm файл
      for dep in departments:
         htm.write('<td>'+str(tabl[dep])+'</td>')
         itogi[dep]+=tabl[dep]
         i+=tabl[dep]
      htm.write('<td>'+str(i)+'</td>')# сумма по строке
      htm.write('</tr>') # конец строки
      j+=i
   #выводим итоговые суммы в htm файл
   htm.write('<tr style="font-weight: bold">')
   htm.write('<td>Всего:</td>')
   for dep in departments:
      htm.write('<td>'+str(itogi[dep])+'</td>')
   htm.write('<td>'+str(j)+'</td>') # общая сумма
   htm.write('</tr>')
   #записываем окончание htm файла
   htm.write('</table>')
   htm.write('</body>')
   htm.write('</html>')
   htm.close()
   print ("разнесено за "+mes_str(mes))
if __name__ == "__main__":
   create_report()
