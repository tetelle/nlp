from flask import Flask, render_template, redirect, flash, request, url_for
from config import DB_USER,DB_PWD,DB_NAME
import MySQLdb 
import nltk	
app = Flask(__name__)
app.config.from_object('config')

try:
	db = MySQLdb.connect(user=DB_USER,passwd=DB_PWD,db=DB_NAME)
	cursor = db.cursor()
except:
	db.close()

def make_slug(alist): # to check words in the list (avoid errors not ascii letters in words)
	import string
	l =[]
	for item in alist:
		res=""
		w = item[0]
		for ch in w.lower():
			if ch in string.ascii_lowercase:
				res+=ch
		l.append(res)		
	return l

@app.route('/',methods=['GET','POST'])
def main():
	my_links = []
	categories = []
	stems = []
	alternatives = []
	try:
		# Get words in query
		word = request.args.get('aword')
		my_words = request.args.get('aword').split()
		myStemmer = nltk.stem.porter.PorterStemmer()
		# For each word
		for my_word in my_words:	
			# Get root of this word
			myStemmer.b = my_word
			myStemmer.k = len(my_word) - 1
			myStemmer.k0 = 0
			myStemmer.step1ab()
			st = myStemmer.b[myStemmer.k0:myStemmer.k+1]
			# Look out for this word in different tables
			cursor.execute("select thing_url from Things where thing_name='%s' or thing_name='%s'" %(st,my_word))	
			results1=cursor.fetchall()
			cursor.execute("select people_url from People where people_name='%s' or people_name='%s'" %(st,my_word))	
			results2=cursor.fetchall()
			cursor.execute("select place_url from Places where place_name='%s' or place_name='%s'" %(st,my_word))	
			results3=cursor.fetchall()	
			# my_links contain all urls for this word
			# categories contain all different categories this word belong to
			# stems contains word stem
			if results1:
				my_links+=results1
				categories.append("Things")
			if results2:
				my_links+=results2
				categories.append("People")
			if results3:
				my_links+=results3
				categories.append("Places")
			stems.append(st)

		# for each of this url, find alternative words
		alternatives = []
		for l in my_links:	
			cursor.execute("select thing_name from Things where thing_url='%s'" %l)	
			results1=cursor.fetchall()
			cursor.execute("select people_name from People where people_url='%s'" %l)	
			results2=cursor.fetchall()	
			cursor.execute("select place_name from Places where place_url='%s'" %l)	
			results3=cursor.fetchall()
			alternatives+=make_slug(results1) + make_slug(results2) + make_slug(results3)
	except:
		word = ""
		
	return render_template('index.html', w = word , urls = my_links, cat = categories, s = stems, m = alternatives)

if __name__ == '__main__':
  app.run(debug=True)