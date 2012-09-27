#!/usr/bin/python
import BeautifulSoup
import urllib
import urllib2
import pickle
from pprint import pprint
import time
#proxy = urllib2.ProxyHandler({'http': '177.36.242.57:8080'})
#opener = urllib2.build_opener(proxy)
#urllib2.install_opener(opener)

def delay(reqfunc):
    def delayfunc(*args):
        time.sleep(0)
        return reqfunc(*args)
    return delayfunc

@delay
def getPage(request):
    MAX_ATTEMPTS = 8
    for attempt in range(MAX_ATTEMPTS):
        try:
            res = urllib2.urlopen(request)
            break
        except urllib2.URLError, e:
            sleep_secs = attempt ** 2
            time.sleep(sleep_secs)
    return  res.read()

url = 'http://www.broncobookstore.com/buy_main.asp?'
quarterList = []
req = urllib2.Request(url)
req.add_header('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0')

the_page = getPage(req)
soup = BeautifulSoup.BeautifulSoup(the_page)
qholder = soup.find('select', attrs={'id':'fTerm'})
qchildlist = qholder.findChildren()

for qchild in qchildlist:
    if qchild['value'] == '0|0':
        continue

    newQuarter = {'name':qchild.text.replace('CAL POLY POMONA - ', ''), 'departments':[]}
    url1 = 'http://www.broncobookstore.com/textbooks_xml.asp?control=campus&campus='+qchild['value'].split('|')[0]+'&term='+qchild['value'].split('|')[1]+'&t=1337387733434'
    req1 = urllib2.Request(url1)
    req1.add_header('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0')
    the_dep_page = getPage(req1)
    departmentList= []
    soup1 = BeautifulSoup.BeautifulSoup(the_dep_page)
    for department in soup1.findChild():
        departmentList.append({'id':department['id'], 'abrev':department['abrev'],   'name':department['name'] })
    for department in departmentList:
        url2 = 'http://www.broncobookstore.com/textbooks_xml.asp?control=department&dept='+department['id']+'&term='+qchild['value'].split('|')[1]+'&t=1337389332928'
        req2 = urllib2.Request(url2)
        req2.add_header('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0')
        the_cor_page = getPage(req2)
        courseList= []
        soup2 = BeautifulSoup.BeautifulSoup(the_cor_page)
        department['courses'] = []
        for course in soup2.findAll('course'):
            newCourse = {'id':course['id'], 'name':department['abrev'] + course['name'] ,  'sections': []}
            url3 = 'http://www.broncobookstore.com/textbooks_xml.asp?control=course&course='+newCourse['id']+'&term='+qchild['value'].split('|')[1]+'&t=1337390759014'
            req3 = urllib2.Request(url3)
            req3.add_header('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0')
            the_sec_page = getPage(req3)
            soup3 = BeautifulSoup.BeautifulSoup( the_sec_page)
            for section in soup3.findChild():
                newSection = {'id':section['id'], 'name':section['name'] , 'instructor':section['instructor'],  'books':[]}
                url4 = 'http://www.broncobookstore.com/textbooks_xml.asp?control=section&section='+newSection['id']+'&t=1337391122366'
                req4 = urllib2.Request(url4)
                req4.add_header('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0')
                the_book_page = getPage(req4)
                soup4 = BeautifulSoup.BeautifulSoup(the_book_page)
                for booktable in soup4.findChildren('tr', attrs={'class':BeautifulSoup.re.compile(r'(book course-required.*)|(book course-optional.*)|(book course-part of set.*)')}):

                    newBook = {}
                    desc = booktable.find('td',attrs={'class':'book-desc'})
                    # no books listed
                    if desc == None:
                        continue

                    if (desc.find('span',attrs={'class':'isbn'}) == None):
                        continue
                    else:
                        newBook['ISBN'] = int(desc.find('span',attrs={'class':'isbn'}).text)

                    if (desc.find('span',attrs={'class':'book-meta book-author'}) == None):
                        newBook['author'] = None
                    else:
                        newBook['author'] = desc.find('span',attrs={'class':'book-meta book-author'}).text

                    if (desc.find('span',attrs={'class':'book-meta book-edition'}) == None):
                        newBook['edition'] = None
                    else:
                         # looks like Edition&nbsp;8 at first
                        newBook['edition'] = desc.find('span',attrs={'class':'book-meta book-edition'}).text.strip('Edition&nbsp;')

                    if (desc.find('p',attrs={'class':'book-req'}) == None):
                        newBook['isRequired'] = None
                    else:
                        newBook['isRequired'] = desc.find('p',attrs={'class':'book-req'}).text

                    if (desc.find('span',attrs={'class':'book-meta book-edition'}) == None):
                        newBook['binding'] = None
                    else:
                        newBook['binding']  = desc.find('span',attrs={'class':'book-meta book-binding'}).text.strip('Binding&nbsp;')

                    if (desc.find('span',attrs={'class':'book-title'}) == None):
                        newBook['title'] = None
                    else:
                        newBook['title']  = desc.find('span',attrs={'class':'book-title'}).text

                    pricestuff = booktable.find('td',attrs={'class':'book-pref'})

                    if(pricestuff == None or pricestuff.find('span', attrs={'class':'book-price-list'}) == None):
                         newBook['broncoListPrice'] = None
                    else:
                        newBook['broncoListPrice'] = float(pricestuff.find('span', attrs={'class':'book-price-list'}).text.strip('$'))
                    newSection['books'].append(newBook)
                newCourse['sections'].append(newSection)
            department['courses'].append(newCourse)
        newQuarter['departments'] = departmentList
    quarterList.append(newQuarter)

import time
import difflib
import pprint
data = pickle.load(open('courseData.txt'))

result =  '\n'.join(difflib.unified_diff(pprint.pformat(data).splitlines(), pprint.pformat(quarterList).splitlines()))
if result:
    pickle.dump(quarterList,  open('courseData.txt','w'))

