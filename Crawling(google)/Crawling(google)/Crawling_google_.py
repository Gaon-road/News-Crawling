# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import schedule
import requests
import re
import pymysql
import datetime

conn = pymysql.connect(
    user = 'root',
    passwd = '@1ghldydqlqjs',
    host = 'localhost',
    db = 'crime',
    charset='utf8mb4'
    )

cursor = conn.cursor()
options = Options()
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36')
driver = webdriver.Chrome(executable_path='chromedriver')
driver = webdriver.Chrome(options=options) # 브라우저 창 안보이기
driver.implicitly_wait(5)
driver.set_window_size(1920,1280)


PAGE_START = 1
PAGE_STOP = 20
Lastest_Search_Date = "2021-10-27 21:08"
Keywords = ["살인","성폭행","폭행","폭력","상해","절도","살해","추행"]
Locals = [["서울",11],["경기",41],["인천",28],["부산",26],["울산",31],["경남",48],["대구",27],["경북",47],["광주",29],["전남",46],["전북",45],["대전",30],["충남",44],["세종",36],["충북",43],["강원",42],["제주",50]]
STOP_SEARCH = False

#날짜비교
def Date_Comparing(A,B):
    A = re.sub('[\-\:\ ]',"",A);
    B = re.sub('[\-\:\ ]',"",B);
    if(int(A)>int(B)):
        return 1
    if(int(A)==int(B)):
        return 0
    else:
        return -1
#시간문자열 재가공
def Date_setting(date):
    now = datetime.datetime.now();
    if (date.find("시간")>-1):
        A=date.find("시간")
        B=date[0:A]
        C = int(B)
        new_date = now - datetime.timedelta(hour=C)
        str_date = new_date.strftime("%Y-%m-%d")
        return str_date
    if (date.find("주")>-1):
        A=date.find("주")
        B=date[0:A]
        C = int(B)
        new_date = now - datetime.timedelta(weeks=C)
        str_date = new_date.strftime("%Y-%m-%d")
        return str_date
    if (date.find("일")>-1):
        A=date.find("일")
        B=date[0:A]
        C = int(B)
        new_date = now - datetime.timedelta(days=C)
        str_date = new_date.strftime("%Y-%m-%d")
        return str_date
    if (date.find("개월")>-1):
        A=date.find("개월")
        B=date[0:A]
        C = int(B)
        new_date = now - datetime.timedelta(weeks=C*4)
        str_date = new_date.strftime("%Y-%m-%d")
        return str_date
    date = re.sub('[\.\ ]',"-",date);
    return date;
#문자열 쿼리문에 맞게 재가공  
def Set_String_mysql(str):
    Cleaned_str = re.sub('[\']',"",str)
    Cleaned_str = re.sub('[\"]',"\"",Cleaned_str)
    Cleaned_str = re.sub('[\,]',"\,",Cleaned_str)
    return Cleaned_str
#검색어 설정
def Searchword(Keyword,Local):
    Add_Keywords = ["시","대검","고법","지구","지검"]
    Sub_Keywords = ["넷플릭스","영화","드라마"]
    STR ='\"'+Keyword+'\", \"'+Local+'\",('
    for add in Add_Keywords:
        STR += add+' | '
    STR += ')'
    for sub in Sub_Keywords:
        STR += ', -'+sub
    return STR

for Local in Locals:
    STOP_SEARCH = False
    PAGE_START=1
    Search_Count = 0;
    for Keyword in Keywords:
        SEARCH_URL = 'https://www.google.com/'
        driver.get(SEARCH_URL)
        time.sleep(10)
        #검색창
        search = driver.find_element_by_xpath('/html/body/div[1]/div[3]/form/div[1]/div[1]/div[1]/div/div[2]/input')
        S=Searchword(Keyword,Local[0])
        search.send_keys(S)
        time.sleep(10)
        search.send_keys(Keys.RETURN)
        #뉴스메뉴선택
        news_menu = driver.find_element_by_link_text("뉴스")
        news_menu.click()
        soup = BeautifulSoup(driver.page_source,'html.parser')
        Search_News = soup.select('div.v7W49e > div ')
        for News in Search_News:
            try:
                Title = Set_String_mysql(News.select_one('g-card > div > div > a > div > div.iRPxbe > div.mCBkyc.tNxQIb.ynAwRc.JIFdL.JQe2Ld.nDgy9d').text)
                Body = Set_String_mysql(News.select_one('g-card > div > div > a > div > div.iRPxbe > div.GI74Re.nDgy9d').text)
                Img = News.select_one('g-card > div > div > a > div > div.FAkayc > div > g-img > img')['src']
                Url = News.select_one('g-card > div > div > a')['href']
                Date = Date_setting(News.select_one('g-card > div > div > a > div > div.iRPxbe > div > p > span').text)
                City = str(Local[1])
                sql = "INSERT INTO news (url, title, body, reporting_date , img, CD) VALUES (\'"+Url+"\', \'"+Title+"\', \'"+Body+"\', \'"+Date+"\',base64_decode(\'"+Img+"\'), \'"+City+"\');"
                cursor.execute(sql)
                conn.commit()
                Search_Count += 1
            except Exception as e:
                print(e)
                continue
        if(STOP_SEARCH==True):
            break;
        PAGE_START+=1
    print("지역 : \""+Local[0]+"\"에서 키워드관련 기사 "+str(Search_Count)+"개 추가.\n")
conn.close()
driver.close()
