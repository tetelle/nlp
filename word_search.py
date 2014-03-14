#-*- coding: utf8 -*-
from __future__ import division
import math
import nltk
import sys
import collections
from newspaper import Article
from collections import Counter,OrderedDict 
from text.blob import TextBlob as tb
import MySQLdb
from config import DB_USER,DB_PWD,DB_NAME   # Database Settings  

myStemmer = nltk.stem.porter.PorterStemmer()

# method 1: calculate tf-idf using the text.blob module
def tf(word, blob):
	cnt = Counter(blob.words)	# instead of blob.words could be using nltk.word_tokenize()
	return cnt[word] / len (blob.words)	

def n_containing(word, bloblist):
	total = 0
	for blob in bloblist:
		all_words = blob.words # instead of blob.words could be using re.findall('\w+', blob) 
		if word in all_words:
			total += 1
	return total

def idf(word, bloblist):
    d = len(bloblist) / (1 + n_containing(word, bloblist))
    return math.log(d)

def tfidf(word, blob, bloblist):
	return tf(word, blob) * idf(word, bloblist) # Decimal(tf(word, blob)) * Decimal(idf(word, bloblist))

# method 2: calculate tf-if using words recorded in database
def tf2(word, url):
	cursor.execute("select thing_name,thing_freq from Things where thing_url='%s'" %url) 
	allnames = cursor.fetchall()
	total = len(allnames)
	myfreq = 0
	for item in allnames:
		if item[0] == word:
			myfreq = item[1]
			break
	return myfreq / total	

def n_containing2(word, urllist):
	total = 0
	for url in urllist:
		cursor.execute("select thing_name from Things where thing_url='%s'" %url) 
		all_words = cursor.fetchall()
		if word in all_words:
			total += 1
	return total

def idf2(word, urllist):
    d = len(urllist) / (1 + n_containing2(word, urllist))
    return math.log(d)

def tfidf2(word, url, urllist):
	return tf2(word, url) * idf2(word, urllist)



#target: find in how many documents does a word appear, use the tf-idf algorithm

#method 1 from blob
print "Method 1"
print

# load documents
document1 = Article(sys.argv[1])
document1.download()
document1.parse()
document2 = Article(sys.argv[2])
document2.download()
document2.parse()
document3 = Article(sys.argv[3])
document3.download()
document3.parse()
bloblist = [tb(document1.text), tb(document2.text), tb(document3.text)]

# get top words for each of those documents
for i, blob in enumerate(bloblist):
    print("Top words in document {}".format(i + 1))
    words = blob.words 

    # get stems of all these words in document
    new_list = []
    for x in words: 
    	myStemmer.b = x
    	myStemmer.k = len(x) - 1
    	myStemmer.k0 = 0
    	myStemmer.step1ab()
    	res = myStemmer.b[myStemmer.k0:myStemmer.k+1]
    	new_list.append((x,res.lower()))
   
    # make a list of tf-idf values and stem for each word and sort this list according to its td-idf values
    scores = [(tfidf(item[0], blob, bloblist),item[1],item[0]) for item in new_list]
    sorted_words = sorted(scores,key=lambda x: x[0],reverse=True)


    # display top 5 results without repeats (same stem), without words less than 3 letters long and words cannot be numbers
    stems =[]
    n = 0
    for s in sorted_words:
    	if n > 5:
    		break
    	if len(s[2]) > 3 and not s[2].isdigit():
    		if s[1] not in stems:
    			stems.append(s[1])
    			print "\tword: {}, stem: {}, TF-IDF: {}".format(s[2],s[1],round(s[0],5))
    			n += 1
  
    """	
    scores = {word: tfidf(word, blob, bloblist) for word in words}
    sorted_words = sorted(scores.items(), key=lambda x: (-x[1], x[0])) # 2 criteria, 1 criteria = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    new_list= [(x[0],x[1]) for x in sorted_words if not x[0].isdigit() and len(x[0])>2] # this has been added to eliminate short words and numbers
    for word, score in new_list[:5]:
        print("\tWord: {}, TF-IDF: {}".format(word, round(score, 5)))
    """


#method 2 from database
#could have been done via a query select * from Things order by thing_freq DESC,thing_name ASC LIMIT 5
#but we don't want any repeats, we want to calculate the stems and the tf-idf values for all of the words
print
print "Method 2"
print

try:
	db = MySQLdb.connect(user=DB_USER,passwd=DB_PWD,db=DB_NAME,use_unicode=True,charset='utf8')
	cursor = db.cursor()
except:
	db.close()

#urllist = ['http://www.bbc.co.uk/news/uk-26176582', 'http://www.bbc.co.uk/news/uk-politics-26176976', 'http://www.bbc.co.uk/news/uk-26127121']
urllist=[sys.argv[1],sys.argv[2],sys.argv[3]]

for i, url in enumerate(urllist):
    print("Top words in document {}".format(i + 1))
    cursor.execute("select thing_name,thing_prob from Things where thing_url='%s'" %url) 
    words = cursor.fetchall()

    # make a list of (word, stem)
    new_list = []
    for x in words: 
    	myStemmer.b = x[0]
    	myStemmer.k = len(x[0]) - 1
    	myStemmer.k0 = 0
    	myStemmer.step1ab()
    	res = myStemmer.b[myStemmer.k0:myStemmer.k+1]
    	new_list.append((x[0],res.lower(),x[1]))
    
    # make a list of (tf-idf, stem, word) and sort it from td-idf values
    scores = [(tfidf2(item[0], url, urllist),item[1],item[0],item[2]) for item in new_list]
    sorted_words = sorted(scores,key=lambda x: x[0],reverse=True)
    
    # display top 5 results without repeats (same stem), without words less than 3 letters long and words cannot be numbers
    stems =[]
    n = 0
    for s in sorted_words:
    	if n > 5:
    		break
    	if len(s[2]) > 3 and not s[2].isdigit():
    		if s[1] not in stems:
    			stems.append(s[1])
    			print "\tword: {}, stem: {}, TF-IDF: {} probability: {}".format(s[2],s[1],round(s[0],5),round(s[3],3))
    			n += 1
    #print stems			