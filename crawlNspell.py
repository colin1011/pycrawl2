import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse
#from autocorrect import spell
from spellchecker import SpellChecker
from flask import Flask,request
import json
from logging import FileHandler, WARNING
import logging
from flask_debugtoolbar import DebugToolbarExtension
import sys
import queue
import random
import string
from nltk import word_tokenize
import enchant



#trying to make a queue which implements set at its backend, so that we dont check if a url is already crawlled or in to_crawl queue

'''
class SetQueue(queue.Queue):

    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = set()

    def _put(self, item):
        self.queue.add(item)

    def _get(self):
        return self.queue.pop()

'''




#<-CONFIGS-START->

#user-agents to randomize, requests
UAS = ("Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1", 
       "Mozilla/5.0 (Windows NT 6.3; rv:36.0) Gecko/20100101 Firefox/36.0",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10; rv:33.0) Gecko/20100101 Firefox/33.0",
       "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
       "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
       "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
       )

#exclude these file extesnions
file_ext_not_to_crawl = ['.png','.ts','.m3u8','.mpd','.js','.css','.jpg']


#maximum time to crawl in milliseconds
max_time_for_crawl = 10000


#maximum links to crawl
max_counter = 20

#max no of typos
no_of_typos_to_display = 10

#intialize enchant english dictionary
d = enchant.Dict("en_US")


#<-CONFIGS-END->

app = Flask(__name__)


#DEBUG

'''
toolbar = DebugToolbarExtension(app)

file_handler = FileHandler('error.txt')
file_handler.setLevel("WARNING")
app.logger.addHandler(file_handler)

'''

#logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def hello():
    return "Hello Root!"



@app.route('/crawlNspellcheck/v1/input/',methods = ['GET'])
def crawl_function():
  try :
    data=crawl_web(request.args.get('q'))
    '''
    payload = {
    "crawled_urls" : data,
    "to_be_crawlled" : to_crawl
    }
    '''
    return json.dumps(data)
  except Exception as e:
    print(e,file=sys.stdout)
    return "Error while processing"



#process urls for the crawler
def process_url(url,current_url):
  #print("inside process_url fun",file=sys.stdout)
  if url[0] == '/':
    url = "http://"+urlparse(current_url).hostname + url

    '''
  for item in file_ext_not_to_crawl:
    if(url.find(item)):
      return False
    '''
  if( url[0:4]=='www'):
    return "http://"+url,True

  if (url[0:4]=='http'):
    return url,True
  else:
    return url,False



def process_text(text):
  #print("inside process_text fun",file=sys.stdout)
  typos_set=set()
  suggestion_set={}
  for word in word_tokenize(text):
    #print("inside process_text function's for loop",file=sys.stdout)
    if (re.match('^[a-zA-Z ]*$',word) and d.check(word) is False):
      #print("inside process_text function's for loop's if statement",file=sys.stdout)
      print(word,file=sys.stdout)
      typos_set.add(word)
      #suggestion_set.add(d.suggest(word)[0])

  return list(typos_set)#,list(suggestion_set)

  




def crawl_web(initial_url):
  #logging.warning("Inside crawl_web")
  crawled  = queue.Queue()
  to_crawl = queue.Queue()
  counter=0
  data = []
  
  now=int(time.time())
  then=now+max_time_for_crawl

  to_crawl.put(initial_url)

  #checks to crawl
  while((not to_crawl.empty()) and (then>int(time.time())) and (counter<max_counter)):
    #print("inside while loop",file=sys.stdout)
    current_url = to_crawl.get()

    #Get random UA so that host-webpage doesn't interpret it as bot
    ua = UAS[random.randrange(len(UAS))]
    headers = {'user-agent': ua}

    r = requests.get(current_url, headers=headers)
    counter=counter+1
    if(r.status_code==200):
      print("inside successful response ",file=sys.stdout)
      soup = BeautifulSoup(r.content, 'html.parser')
      #print("inside successful response {}".format(soup.text[0:200]),file=sys.stdout)
      crawled.put(current_url)
      print("Length of crawled queue {0}".format(len(crawled.queue)),file=sys.stdout)
      print("Length of to_crawl queue {0}".format(len(to_crawl.queue)),file=sys.stdout)
      typos = process_text(soup.text)

      
      payload = {
      "url" : current_url,
      "typos" : typos
      #"suggestion" : suggestion
      }
      

      data.append(payload)
    for link in soup.find_all('a'):
      url=link.get('href')
      try :
        if(url is not None):
          url,val=process_url(url,current_url)
          print(url,file=sys.stdout)
          if(val and  (url not in to_crawl.queue) and (url not in crawled.queue)):
            to_crawl.put(url)
            print("URL {} put in to_crawl queue ".format(url),file=sys.stdout)
      except IndexError:
        print(" URL : {} is giving index error ".format(url),file=sys.stdout)
  return data#,list(to_crawl.queue)




'''

count_value = crawl_web('http://www.google.com')
print("crawled {0} webpages".format(count_value))

'''


if __name__ == '__main__':
   app.run(debug=True,host='0.0.0.0',port=5000)

