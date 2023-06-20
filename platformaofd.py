#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Скрипт для скачивания чеков с личного кабинета ПлатформаОФД (Эвотор)
from lxml import html
import requests
from requests.exceptions import HTTPError
from sys import argv
from sys import platform
from datetime import timedelta, datetime
from os import path
import report
import csv

def num_rub(input_str):# вынимаем 1000 из строки '1 000 р'
    result_str=""
    for ch in input_str[:-2]: # отрезаем лишнее
        if ch != ' ': result_str=result_str+ch # вырезаем пробелы
    return result_str

def get_tree(url):
    try:
        response = session.get(url, timeout=30) # Получаем страницу
        # если ответ успешен, исключения задействованы не будут
        response.raise_for_status()
    except HTTPError as http_err:
        print('HTTP ошибка: ',http_err)
        exit()
    except Exception as err:
        print('Ошибка: ',err)
        exit()
    if debug: file_debug.write(response.text) # запись в файл для отладки
    tree = html.document_fromstring(response.text) # парсим страничку
    return tree

def csv_reader(f_obj): 
    #Read a csv file
    reader = csv.reader(f_obj, delimiter=';')
    for row in reader:
        cheque_id = row[5]
        cheques_file.add(cheque_id)

def download_cheques_for_day(date):
    global new_loads
    start=datetime.now()
    new_loads = 0 # счётчик загруженных чеков
    if platform=="win32": file_name=date+".csv"
    else: file_name="/home/cyril/cheques/"+date+".csv"
    
    if path.isfile(file_name): 
        print (date," Файл за такую дату уже есть.")
        reloading=1
        csv_file = open(file_name, "r+", encoding='utf-8') # открываем файл для чтения/записи
        csv_reader(csv_file)
    else:
        reloading=0 # загружаем все данные с нуля
        csv_file = open(file_name, "w", encoding='utf-8') # открываем файл для записи
    cheques_num=0 #счётчик чеков в списке
    periods=[('11:30','17:59'),('09:00','11:29'),('07:30','08:59'),('05:00','07:29')]
    #periods=[('12:01','18:00'),('10:01','12:00'),('08:01','10:00'),('05:01','08:00')]
    for t in periods:
        cheques_url = lk+ "/web/auth/cheques?start="+date+"+"+t[0]+"&end="+date+"+"+t[1]+\
                      "&deviceId=&operType=&fragments=cheques-search-content&ajaxSource=cheques_filter_form_id" # URL, с которого нужно парсить данные
        cheques_tree = get_tree(cheques_url) # получаем список чеков за период

        empty_data = cheques_tree.xpath("//div[@class='empty-data']")
        if empty_data:
            print (date," ",t[0],'-',t[1],"За данный период времени транзакций не было.")
            continue # следующий период

        limit = cheques_tree.xpath("//a[@id='terminal_cheque_limit_id']")
        if limit: 
            print (date," ",t[0],'-',t[1],"Превышен лимит.")
            #csv_file.write("Превышен лимит. Выгрузка прервана") # запись в файл
            exit() 

        trs = cheques_tree.xpath("//table/tbody/tr")
        print (date," ",t[0],'-',t[1],len(trs)) # количество чеков за период
        cheques_num += len(trs)
        for tr in trs: # цикл по строкам таблицы чеков
            cheque_id = tr.get("id")
            if (reloading==0) or (cheque_id not in cheques_file):
                # Надо загрузить
                new_loads+=1 #увеличиваем счётчик загружаемых чеков
                href = tr.get("href")
                td = tr.xpath('.//text()') # текстовые колонки из строки таблицы чеков (тип, дата/время, имя кассы, номер чека, номер смены, сумма 
                #td = tr.xpath('.//@title | .//text()') # "Наличными" + ^ 
                cheques_details_url = lk+ href+"&fragments=common-modal-content&ajaxSource="+ cheque_id # ссылка на детализацию чека
                cheques_details_tree = get_tree(cheques_details_url) # получаем детализацию чека
                trs1 = cheques_details_tree.xpath("//table/tbody/tr")
                for tr1 in trs1: # цикл по строкам таблицы номенклатуры чека
                    td1 = tr1.xpath('.//text()') # колонки из строки номенклатуры чека (наименование, количество, цена, скидка, сумма)
                    summa = num_rub(td1[4])
                    if td[0] == "Возврат прихода": summa="-"+summa # возврат с минусом
                    string1 = td[1]+";"+td[2]+";"+td1[0]+";"+td1[1]+";"+summa+";"+ cheque_id # дата/время, имя кассы, наименование, количество, сумма
                    if debug: print(string1)
                    csv_file.write(string1+"\n") # запись в файл
    csv_file.close()
    print (date,"Всего чеков:", cheques_num)
    print ("Загружено чеков:", new_loads)
    print(datetime.now()-start)

def get_cheques_sum_for_day(date):
    cheques_url = lk+ "/web/auth/cheques/indicator/shifts?start="+date+"+05:00"+"&end="+date+"+18:00"+\
    "&fragments=content&ajaxSource=date_range_id" # URL, с которого нужно парсить данные
    cheques_tree = get_tree(cheques_url) # получаем суммы по чекам за период
    empty_data = cheques_tree.xpath("//div[@class='empty-data']")
    if empty_data:
        print (date," Транзакций не было.")
        return
    summarno = cheques_tree.xpath("//table[contains(@class, 'table-cheque-motion')]/tbody/tr[3]/td[7]//text()") # Итого по приходу, Суммарно
    if debug: print(summarno)
    print(date, "По показателям,", summarno[1].strip()) #чеков
    return

if __name__ == "__main__":
    debug = 0 # переменная для отладки (1-включить,0-выключить)
    if debug: file_debug = open("cheques_download.htm","w", encoding='utf-8') # открываем отладочный файл для записи
    login = "+790xxxxxxx" # !
    password = "xxxxxxxxx"# !
    lk = "https://lk.platformaofd.ru" # URL личного кабинета

    if len (argv) > 1: # если передан параметр в командной строке
        date=argv[1]    # выгрузка за дату из командной строки
        date2 = ""
    else:
        date = (datetime.now() - timedelta(1)).strftime('%d.%m.%Y') # если параметр не передан, выгрузка за вчера.
        date2 = (datetime.now() - timedelta(2)).strftime('%d.%m.%Y') # если параметр не передан, выгрузка за позавчера
        #date = time.strftime( '%d.%m.%Y' , time.gmtime( time.time()) ) # если параметр не передан, выгрузка за сегодня.

    session=requests.Session()
    # логинимся в ЛК
    login_url = lk+ "/web/login?fragments=content&ajaxSource=login_link_id" # URL с формой логина
    login_tree = get_tree(login_url) # Получаем из страницы с формой логина
    csrf = login_tree.find(".//input[@name='_csrf']").get('value') # ищем _csrf
    data = {"_csrf":csrf, "j_username":login, "j_password":password} # Данные, которые будут отправляться в POST
    security_check_url = lk+ "/web/j_spring_security_check" # URL, куда отправляются учётные данные
    session.post(security_check_url, data) # Отправляем данные в POST, в session записываются наши куки
    cheques_file=set() # множество id (работает быстрее чем список)
    download_cheques_for_day(date)
    get_cheques_sum_for_day(date)
    new_loads2=new_loads # счётчик загруженных чеков за 2 дня
    if date2: # проверяем за позавчера
        cheques_file=set() # множество id (работает быстрее чем список)
        download_cheques_for_day(date2)
        get_cheques_sum_for_day(date2)
        new_loads2+=new_loads
    if debug: file_debug.close()
    if new_loads2>0: report.create_report()
