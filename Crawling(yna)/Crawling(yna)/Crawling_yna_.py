# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import schedule
import requests
import re
import pymysql

conn = pymysql.connect(
    user = 'root',
    passwd = '@1ghldydqlqjs',
    host = 'localhost',
    db = 'Crime',
    charset='utf8mb4'
)
cursor = conn.cursor()

options = Options()
options.add_argument('headless');
driver = webdriver.Chrome(executable_path='chromedriver')
driver = webdriver.Chrome(options=options)
driver.implicitly_wait(5)
driver.set_window_size(1920,1280)

#조사할 페이지 수
PAGE_START = 1
PAGE_STOP = 20
#시스템 시간
Lastest_Search_Date = "2021-10-27 21:08"
#조사할 키워드
Keywords = ["살인","성폭행","폭행","폭력","상해","절도","살해","추행"]
Locals = ["gyeonggi","incheon","busan","ulsan","gyeongnam","daegu-gyeongbuk","gwangju-jeonnam","jeonbuk","deajeon-chungnam-sejong","chungbuk","gangwon","jeju"]
STOP_SEARCH = False

def Overlap_check(url):
    for CHECK in Recode_News:
        if CHECK == url:
            return True
    return False
#날짜 비교
def Date_Comparing(A,B):
    A = re.sub('[\-\:\ ]',"",A);
    B = re.sub('[\-\:\ ]',"",B);
    if(int(A)>int(B)):
        return 1
    if(int(A)==int(B)):
        return 0
    else:
        return -1
#날짜 재가공
def Date_setting(date):
    date = "2021-"+date
    return date
#문자열 쿼리문에 맞게 재가공
def Set_String_mysql(str):
    Cleaned_str = re.sub('[\']',"",str)
    Cleaned_str = re.sub('[\"]',"\"",Cleaned_str)
    Cleaned_str = re.sub('[\,]',"\,",Cleaned_str)
    return Cleaned_str
#키워드매칭
def Find_Keyword(str):
    for Keyword in Keywords:
        if(str.find(Keyword)>-1):
            return True
    return False
#이미지url찾기
def Find_Img(str):
    """ html예제문 = <a href="//www.yna.co.kr/view/AKR20211105147600056?section=local/jeju/index" 
                     class="img img-cover imgLiquid_bgSize imgLiquid_ready" style="background-image: 
                     url(&quot;//img9.yna.co.kr/photo/cms/2016/04/17/01/C0A8CA3D0000015424301581000A812F_P2.jpeg&quot;); 
                     background-size: cover; background-position: center top; background-repeat: no-repeat;">
                     <img src="//img9.yna.co.kr/photo/cms/2016/04/17/01/C0A8CA3D0000015424301581000A812F_P2.jpeg" alt="제주서 또래 여고생 집단 폭행한 10대 2명 입건"></a> """
    sindex = str.find("url(\"")
    eindex = str.find("\");")
    return str[sindex+5:eindex]
#지역찾기
def Find_Local(str):
    Finding = re.findall('\(.+=연합뉴스\)',str)
    Local = re.sub("[=\(\)\연합뉴스]","",Finding[0])
    return Local
#지역명 재가공(와일드카드)
def acronym_expand(acronym):
    new = ""
    for i in range(len(acronym)):
        new = new + acronym[i]+"%"
    return new
#기사지역명으로부터 지역코드반환
def Finde_CD(state,city):
    states = state.split('-')
    for st in states:
        if(city=="서울"):
            print("서울발견")
            return 11
        else:
            A = acronym_expand(st)
            B = acronym_expand(city)
            sql = "SELECT SIG_CD FROM Crime.map_SIG WHERE (SELECT LEFT (SIG_CD,2)) = (SELECT CTPRVN_CD FROM Crime.map_CTPRVN WHERE CTP_ENG_NM LIKE \'"+A+"\') and SIG_KOR_NM LIKE \'"+B+"\' limit 1;"
            cursor.execute(sql)
            CD = cursor.fetchall()
            if(CD[0][0]==None):
                continue
            else:
                return CD[0][0]
    return "-1"

for Local in Locals:
    STOP_SEARCH = False
    PAGE_START=1
    Search_Count = 0;
    while PAGE_START <= PAGE_STOP:
        SEARCH_URL = 'https://www.yna.co.kr/local/'+Local+'/index/'+str(PAGE_START)
        driver.get(SEARCH_URL)
        time.sleep(4)
        soup = BeautifulSoup(driver.page_source,'html.parser')
        Search_News = soup.select('div.list-type038 > ul.list > li')
        for News in Search_News:
            try:
                Title = News.select_one('div.item-box01 > div.news-con > a > strong.tit-news').text
                Body = News.select_one('div.item-box01 > div.news-con > p.lead').text
                if(Find_Keyword(Body) or Find_Keyword(Title)):
                    Date = Date_setting(News.select_one('div.item-box01 > div.info-box01 > span.txt-time').text)
                    Img = Find_Img(News.select_one('div.item-box01 > figure.img-con > a')['style'])
                    Url = News.select_one('div.item-box01 > div.news-con > a')['href']
                    City = Finde_CD(Local,Find_Local(Body))
                    if(City=="-1"):
                        continue
                    else:
                        sql = "INSERT INTO news (url, title, body, reporting_date , img, CD) VALUES (\'"+Url+"\', \'"+Title+"\', \'"+Body+"\', \'"+Date+"\', \'"+Img+"\', \'"+City+"\');"
                        cursor.execute(sql)
                        conn.commit()
                        Search_Count += 1
                else:
                    continue
            except Exception as e:
                continue
        if(STOP_SEARCH==True):
            break;
        PAGE_START+=1
    print("지역 : \""+Local+"\"에서 키워드관련 기사 "+str(Search_Count)+"개 추가.\n")
conn.close()

driver.close()

