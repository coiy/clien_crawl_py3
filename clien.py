from bs4 import BeautifulSoup
import requests
import re, string
import config
import MySQLdb
import datetime
import PyRSS2Gen
import sys
import os 
    
BASEPATH = '/Users/coiy/dev/clien_crawl_py3'

def makerss():
  lst_title = []
  lst_category = []
  lst_text = []
  lst_url = []
  lst_pubdate = []
  lst_author = []
  lst_reply = []
  lst_recom = []

  db = MySQLdb.connect(config.mysql_server, config.mysql_id, config.mysql_password, config.mysql_db, charset='utf8mb4')
  curs = db.cursor(MySQLdb.cursors.DictCursor)

  rss = PyRSS2Gen.RSS2(
    title = "clien_crawl",
    link = "https://www.clien.net",
    description = "RSS_clien",
    lastBuildDate = datetime.datetime.now(),
    items = [])

  rowcount = curs.execute( """SELECT * FROM rss order by pubdate DESC limit 80 """ )
    
  for r in curs.fetchall():
    lst_title.append( r['title'] )
    lst_category.append( r['category'] )
    lst_text.append( r['text'] )
    lst_url.append( r['url'] )
    lst_pubdate.append( r['pubdate'] )
    lst_author.append( r['author'] )
    lst_reply.append( r['reply'] )
    lst_recom.append( r['recom'] )

  for i, title in enumerate(lst_title):
    #tt = "[%s][%s]" % ( str(lst_reply[i]), str(lst_recom[i]))
    item = PyRSS2Gen.RSSItem(
    title = lst_title[i],
    link = 'https://www.clien.net' + lst_url[i],
    guid = PyRSS2Gen.Guid('https://www.clien.net' + lst_url[i]),
    description = lst_text[i],
    # pubDate = datetime.datetime.fromtimestamp(lst_pubdate[i]),
    pubDate = lst_pubdate[i],
    author = lst_author[i])
    rss.items.append(item)
	
  rss.write_xml(open("rss_clien_mac.xml",  "w"), "utf-8")
  print('XML created')

def check_pk(url, reply, recom):
  db = MySQLdb.connect(config.mysql_server, config.mysql_id, config.mysql_password, config.mysql_db, charset='utf8mb4')
  curs = db.cursor(MySQLdb.cursors.DictCursor)
		
  bFind = False
	
  # 같은 주소에 덧글, 공감수 바뀌었나?
  rowcount = curs.execute ( """SELECT reply, recom FROM rss WHERE url = %s """, (url,) )
  data = curs.fetchone()
  if rowcount > 0:
    bFind = True
    # 값이 변경되었으면 업데이트.
    if ( reply > data['reply']  ) or ( recom  > data['recom'] ):
      rowcount = curs.execute ( """UPDATE rss SET reply = %s, recom = %s WHERE url = %s""", (int(reply), int(recom), url) )
      db.commit()
		
    return bFind
	
def insert_bbs(category, title, text, url, pubdate, author, reply, recom):
  db = MySQLdb.connect(config.mysql_server, config.mysql_id, config.mysql_password, config.mysql_db, charset='utf8mb4')
  curs = db.cursor(MySQLdb.cursors.DictCursor)
  curs.execute("""INSERT INTO rss (category, title, text, url, pubdate, author, reply, recom)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
    ON DUPLICATE KEY 
    UPDATE reply = %s, recom = %s """, (category, title, text, url, pubdate, author, reply, recom,  reply, recom))
		
  db.commit()

def pasing_url(link):
  r = requests.get(link)
  soup = BeautifulSoup(r.text, "lxml")
  elements = soup.findAll("div", {"class" : "list_item symph_row"})

  for el in reversed(elements):
    title = el.a.find("span", {"data-role" : "list-title-text"}).attrs["title"]
    url = el.find("a")["href"]
    url = url.strip()
		
    try:
      reply = el.findAll("span", {"class": "rSymph05"})
      reply = reply[0].text
      #print reply
    except:
      reply = '0'
      #print '0'

    try:
      symph = el.find("div", {"data-role": "list-like-count"})
      span = symph.find("span")
      recom = span.text
      #print recom

    except:
      recom = '0'
      #print '0'
    
    try:
      category = el.find("span", {"class": "category"}).attrs["title"]
    except:
      category = ' ' 	

    # 덧글 10개 이상이면 내용 가져오기
    #if ( int(reply) >= 10 ) or ( int (recom) >= 5 ):
			#기존 저장 된건가? 
			# feedly 에 제목이 두번나온다. 일단 제목에 업데이트 금지.
    if not check_pk(url, reply, recom):
      r = requests.get("https://www.clien.net" + url)
      soup = BeautifulSoup(r.text, "lxml")
      elements = soup.find("div", {"class": "post_article fr-view"}).text
      text = elements
    
				
      # 날짜
      pdate = soup.find("div", {"class": "post_author"})
      pubdate = pdate.find("span").text.strip()
      pubdate = pubdate[0:20].strip()

      author = soup.find("span", {"class": "contact_name"}).text.strip()
				
      insert_bbs(category, title, text, url, pubdate.strip(), author, reply, recom )
      print ("INSERT BODY!! ")



		

# 검색할 게시판 List
url_list = []
#url_list.append ('https://www.clien.net/service/board/news')
#url_list.append ( 'https://www.clien.net/service/board/park')
#url_list.append ( 'https://www.clien.net/service/board/lecture')
url_list.append('https://www.clien.net/service/board/cm_mac')
#url_list.append ( 'https://www.clien.net/service/board/jirum')

url_list.append ( 'https://www.clien.net/service/board/cm_iphonien')
#url_list.append ( 'https://www.clien.net/service/board/cm_car')
url_list.append ( 'https://www.clien.net/service/board/cm_bike')
url_list.append ( 'https://www.clien.net/service/board/cm_havehome')
#url_list.append ( 'https://www.clien.net/service/board/cm_nas')


for u in url_list:
  for i in range(3,-1,-1):
    if i == 0:
      print(u)
      pasing_url(u)
    else:
      print(u + '&po=%d' % i)
      pasing_url(u + '?&po=%d' % i)

makerss()