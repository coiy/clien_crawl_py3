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

	db = MySQLdb.connect(config.mysql_server, config.mysql_id, config.mysql_password, config.mysql_db, charset='utf8')
	curs = db.cursor(MySQLdb.cursors.DictCursor)

	rss = PyRSS2Gen.RSS2(
		title = "clien_crawl",
		link = "https://www.clien.net",
		description = "RSS_clien_hot10",
		lastBuildDate = datetime.datetime.now(),
		items = [] )

	rowcount = curs.execute ( """SELECT * FROM rss order by pubdate DESC limit 80 """ )

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
		tt = "[%s][%s]" % ( str(lst_reply[i]), str(lst_recom[i]))
		item = PyRSS2Gen.RSSItem(
			title = lst_title[i] + tt,
            link = 'https://www.clien.net' + lst_url[i],
            guid = PyRSS2Gen.Guid('https://www.clien.net' + lst_url[i]),
            description = lst_text[i],
            # pubDate = datetime.datetime.fromtimestamp(lst_pubdate[i]),
			pubDate = lst_pubdate[i], 
			author = lst_author[i] )
			
		rss.items.append(item)
	
	rss.write_xml(open(BASEPATH + 'rss_clien.htm',  'w'))

def check_pk (url, reply, recom):
	db = MySQLdb.connect(config.mysql_server, config.mysql_id, config.mysql_password, config.mysql_db, charset='utf8')
	curs = db.cursor(MySQLdb.cursors.DictCursor)
		
	bFind = False
	
	# 같은 주소에 덧글, 공감수 바뀌었나?
	rowcount = curs.execute ( """SELECT reply, recom FROM rss WHERE url = %s """, url )
	data = curs.fetchone()
	if rowcount > 0:
		bFind = True
		# 값이 변경되었으면 업데이트.
		if ( reply > data['reply']  ) or ( recom  > data['recom'] ):
			rowcount = curs.execute ( """UPDATE rss SET reply = %s, recom = %s WHERE url = %s""", (int(reply), int(recom), url) )
			db.commit()
		
	return bFind
	
def insert_bbs(category, title, text, url, pubdate, author, reply, recom):
	db = MySQLdb.connect(config.mysql_server, config.mysql_id, config.mysql_password, config.mysql_db, charset='utf8')
	curs = db.cursor(MySQLdb.cursors.DictCursor)
	curs.execute ( u"""INSERT INTO rss (category, title, text, url, pubdate, author, reply, recom)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
		ON DUPLICATE KEY 
		UPDATE reply = %s, recom = %s """, (category, title, text, url, pubdate, author, reply, recom,  reply, recom))
		
	db.commit()

def pasing_url(link):
	
	r = requests.get(link) 
	
	# BeautifulSoup 로 파싱
	soup = BeautifulSoup(r.text, "lxml")
	elements = soup.findAll('div', {'class' : 'list_item symph_row'})

	for el in reversed(elements):
		title = el.a.find('span', {'data-role' : 'list-title-text'}).attrs['title']
		url = el.find('a')['href']
		url = url.strip()
		print(title)
		
		try:
			reply = el.findAll("span", {"class": "rSymph05"})
			reply = reply[0].text
			#print reply
		except:
			reply = '0'
			#print '0'

		try:
			symph = el.findAll("div", {"class": "list-symph"})
			recom = symph[0].text
			#print recom

		except:
			recom = '0'
			#print '0'

		lst_cate = link.split('/')
		c = lst_cate[-1]
		ca = c.split('?')
		category = ca[0]

		
		# 덧글 10개 이상이면 내용 가져오기
		if ( int(reply) >= 10 ) or ( int (recom) >= 5 ):
			#기존 저장 된건가? 
			# feedly 에 제목이 두번나온다. 일단 제목에 업데이트 금지.
			if not check_pk (url, reply, recom):
				r = requests.get('https://www.clien.net' + url) 
				
				# BeautifulSoup 로 파싱
				soup = BeautifulSoup(r.text, "lxml")
				elements=soup.findAll("body")
				text = elements[1]
				
				# 날짜
				pdate = soup.findAll("div", {"class": "post-time"})
				pubdate = pdate[0].text.strip()
				
				#<button class="button-md button-report" onclick="app.articleSingo('samsung');
				
				# 글쓴이
				pauthor = soup.findAll("button", {"class": "button-md button-report"})
				auth1 = ''.join(pauthor[0].encode('utf-8'))
				# 정규식
				# 문자숫자\w+ 로 시작하고 끝이 따옴표이지만 포함하지 않음
				rex = re.search("[\w]+(?=\')", auth1)
				author = rex.group()
				
				insert_bbs(category, title, text, url, pubdate.strip(), author, reply, recom )
				print ("INSERT BODY!! ")
					
		continue; 


		

# 검색할 게시판 List
url_list = []
#url_list.append ('https://www.clien.net/service/board/news')
#url_list.append ( 'https://www.clien.net/service/board/park')
#url_list.append ( 'https://www.clien.net/service/board/lecture')
url_list.append ( 'https://www.clien.net/service/board/cm_mac')
#url_list.append ( 'https://www.clien.net/service/board/jirum')

url_list.append ( 'https://www.clien.net/service/board/cm_iphonien')
#url_list.append ( 'https://www.clien.net/service/board/cm_car')
url_list.append ( 'https://www.clien.net/service/board/cm_bike')
#url_list.append ( 'https://www.clien.net/service/board/cm_havehome')
#url_list.append ( 'https://www.clien.net/service/board/cm_nas')


for u in url_list:
	for i in range(3,-1,-1):
		if i == 0: 
			print(u) 
			try:
				pasing_url(u)
			except:
				continue

		else:
			print(u + '&po=%d' % i)
			try:
				pasing_url(u + '?&po=%d' % i)
			except:
				continue
			
makerss()