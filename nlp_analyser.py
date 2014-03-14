#-*- coding: utf8 -*-
import sys
import nltk
import re

from nltk.corpus import cess_esp as cess    # Import Spanish Corpus
from nltk import UnigramTagger as ut        # Tagger Used for Spanish
from newspaper import Article				# From url containing news the Article module has useful functions such as tile, text, keywords, summary
from nltk.tag.stanford import POSTagger		# The stanford NLP processing group has produced modules that can be used for other languages than English:
from nltk.tag.stanford import NERTagger		# For French and German
from nltk.tag.stanford import POSTagger		# For French and German

import json									# To be able to read json files
import urllib2								# To be able to read url (speech) containing json

import collections							# The collection module has useful functions to count automatically frequencies
from collections import Counter             # Module useful for frequencies in a list

import MySQLdb 								# Module for Mysql database
import datetime 							# Module to use date and time 
from config import DB_USER,DB_PWD,DB_NAME   # Database Settings  

languages = ["ar","de","en","es","fr","it","ko","no","pt","sv","zh"] 				   	# languages supported by this parser
punctuation = [",",";",".",":","!","?","(",")","-","%","\"","[","]"]                    # all marks of punctuation
sent_detector = nltk.data.load('tokenizers/punkt/english.pickle')    					# Loading English file to detect sentences
cess_sents = cess.tagged_sents()									 					# Spanish sentences
uni_tag = ut(cess_sents)											 					# Tagging spanish sentences
st_tag_english = NERTagger('english.all.3class.distsim.crf.ser.gz','stanford-ner.jar') 	# Entities for English
st_pos_french = POSTagger('french.tagger', 'stanford-postagger.jar') 				   	# French Grammar
st_pos_german = POSTagger('german-fast.tagger', 'stanford-postagger.jar') 			   	# German Grammar
st_tag_german = NERTagger('hgc_175m_600.crf.ser.gz','stanford-ner.jar')                	# Entities for German
chunker = nltk.data.load('chunkers/maxent_ne_chunker/english_ace_multiclass.pickle') 	# Loads the Chunk Parser
maxEnt = chunker._tagger.classifier()                                                	# The tag classifier for entities


# Please note that at the moment English, French, German and Sapnish are the only languages supported by this program
# It is slower in German and better in English: in English it is possible to define a probability for entities (with the Chunk Parser)
#--------------------------------------------------------------------------------------------------------------------------------------


# Global variables
my_entities =[]
cnt = Counter()

# Connecting to database
try:
	db = MySQLdb.connect(user=DB_USER,passwd=DB_PWD,db=DB_NAME,use_unicode=True,charset='utf8')
	cursor = db.cursor()
except:
	db.close()


""" Function that checks that this data has not yet been inserted into the database """
def check_db(atype,aname,url):
	# Entity is a Thing
	if atype == "Thing" or atype == "noun":
		cursor.execute("select * from Things where thing_url='%s' and thing_name like '%s'" %(url,aname+"%"))
		result = cursor.fetchone()
		if result:
			return False
		else:
			return True
	# Entity is a Person
	elif "per" in atype.lower():
		cursor.execute("select * from People where people_url='%s' and people_name like '%s'" %(url,aname+"%"))
		result = cursor.fetchone()
		if result:
			return False
		else:
			return True
	# Entity is a Place
	elif atype == "Place" or "GPS" in atype or "LOC" in atype:
		cursor.execute("select * from Places where place_url='%s' and place_name like '%s'" %(url,aname+"%"))
		result = cursor.fetchone()
		if result:
			return False
		else:
			return True
 	else:
 		return False

""" Same as above for German (to deal with 'funny characters': ä ü ) """
def check_db_german(atype,aname,url):
	if atype == "Thing" or atype == "noun": #add unicode to query
		cursor.execute(u"select * from Things where thing_url='%s' and thing_name like '%s'" %(url,aname+"%"))
		result = cursor.fetchone()
		if result:
			return False
		else:
			return True
	elif "per" in atype.lower(): #add unicode to query 
		cursor.execute(u"select * from People where people_url='%s' and people_name like '%s'" %(url,aname+"%"))
		result = cursor.fetchone()
		if result:
			return False
		else:
			return True
	elif atype == "Place" or "GPS" in atype or "LOC" in atype: #add unicode to query
		cursor.execute(u"select * from Places where place_url='%s' and place_name like '%s'" %(url,aname+"%"))
		result = cursor.fetchone()
		if result:
			return False
		else:
			return True
 	else:
 		return False

""" Function that inserts data into the right table in the database """
def insert_db(atype,aname,adate,url,afreq,aprob):
	# Insert into database if not already in there!
	if check_db(atype,aname,url) and len(aname)>2:
		# Insert data into appropriate table according to entity (Place?Person?Thing?)
		if atype.lower() == "thing" or atype == "noun":
			cursor.execute("insert into Things (thing_name,thing_date,thing_url,thing_freq,thing_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob)) 
		elif "per" in atype.lower(): # each languages gives back results differently I-PER PERSON Person...
			cursor.execute("insert into People (people_name,people_date,people_url,people_freq,people_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob)) 
		elif atype.lower() == "place" or "GP" in atype or "LOC" in atype: # each language gives back different results I-Loc, I-GPE, I-GPS, Place...
			cursor.execute("insert into Places (place_name,place_date,place_url,place_freq,place_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob))
		elif "organization" in atype.lower(): # could be ORGANIZATION B-ORGANISATION etc
			cursor.execute("insert into Organisations (organisation_name,organisation_date,organisation_url,organisation_freq,organisation_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob))

""" Same as above for German (to deal with 'funny characters': ä ü ) """
def insert_db_german(atype,aname,adate,url,afreq,aprob):
	if check_db_german(atype,aname,url) and len(aname)>2:
		# add unicode to the insert query
		if atype.lower() == "thing" or atype == "noun": 
			cursor.execute(u"insert into Things (thing_name,thing_date,thing_url,thing_freq,thing_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob)) 
		elif "per" in atype.lower(): # each languages gives back results differently I-PER PERSON Person...
			cursor.execute(u"insert into People (people_name,people_date,people_url,people_freq,people_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob)) 
		elif atype.lower() == "place" or "GP" in atype or "LOC" in atype: # each language gives back different results I-Loc, I-GPE, I-GPS, Place...
			cursor.execute(u"insert into Places (place_name,place_date,place_url,place_freq,place_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob))
		elif "organization" in atype.lower(): # could be ORGANIZATION B-ORGANISATION etc
			cursor.execute(u"insert into Organisations (organisation_name,organisation_date,organisation_url,organisation_freq,organisation_prob) values ('%s','%s','%s',%d,'%s')" \
						%(aname,adate,url,afreq,aprob))

""" To deal with unicode problems """
def transform(a):
	try:
		word=a.encode('utf8')
	except:
		word=repr(a)	
	return word	

""" Function that looks into a list of tuples [(x,y), (v,w)...] and retrieves a specific item e.g. y if looking for x 
	This list of tuples represents the result of the entities search (word,entity)
	if this item is not found, check the previous item (previous word) in a list (of words) 
	if the previous word was a determinant, it is likely to be a thing
	if the previous word was a preposition, it is likely to be a place
	if the previous word was not a determinant neither a preposition, it is likely to be a person """
def lookup(item,atuple,aseries):
	start_places = ["a","en","de","del"]
	start_things = ["el","la","los","las","una","uno","un"]	

	if item[0] == "'":
		item = item[1::]
	if item[len(item)-1] == "'":
		item = item[0:len(item)-1]

	for x,y in enumerate(atuple):
		if y[0] == item:
			return y[1]

	# The Spanish Entity parser (based upon English, none implemented by the Stanford Group) missed out on entities - refine results
	backup = ""
	for j in aseries:
		if item == j:
			if backup.lower() in start_things or backup.endswith('ando'): #Previous word is in "ando" means gerund/descriptive of a word
				return "Thing"
			elif backup.lower() in start_places:
				return "PLACE"
			else:
				return "PERSON" 
		backup = j
	
	if item[0].isupper():
		return "PERSON"
	return 'O'	

""" function that returns True if 2 words follow each other in the sequence of words """
def following_words(thisword,previousword,words):
	backup = ""
	if previousword == "":
		return True

	for w in words:
		if thisword in w: 
			if backup in previousword:
				return True
			else:
				return False
		backup = w
	return False

""" Function that prints kept words and their entities but also regroup words together if they follow each other in the sentence """
def same_entity(awordlist,entitylist,words): #awordlist is a list of kept words, words is all the words in sentence
	previous_entity = ""
	previous_word = ""
	group = ""

	# go through entity list, if same entity check if the words follow each other
	for i in range(len(entitylist)):
		if previous_entity == entitylist[i]: 			# same entity
			if following_words(awordlist[i],previous_word,words): # yes, we have following words
				group += awordlist[i]+" "
				if i == len(entitylist) - 1: 			# last word of sentence, print it now (no next time!)
					print entitylist[i],group
			else: 									# not following words	
				if group != "":			
					print previous_entity,group    	# previous pair
				print previous_entity,awordlist[i] 	# current pair
				group = ""
		else:
			if group != "":
				print previous_entity,group        	# previous pair
			
			group = awordlist[i]+" "                 	# prepare next group
			if i == len(entitylist) - 1:               	# last word of sentence, print it now (no next time!)
				print entitylist[i],group

		previous_entity = entitylist[i]    			# backup of this entity to compare it to the next one
		previous_word = awordlist[i]       			

""" This function displays all entities but some words need to be grouped together e.g. Arrowe Park Hospital """
def english_nouns(entities,probs,words):
	backup = ""  # We need to keep a record of previous tag when we have noun phrases together
	total = 0    # We need to keep a record of all probs to compute an average (for noun phrases together)
	previous = ""# We need to keep a record of all previous words when we have noun phrases together
	counter =  1 # How many noun phrases together
	
	for j in range(0,len(entities)): 
		if entities[j] != "O": 				# Word that are nouns or noun phrases 
			if entities[j][0] == "B":		# Noun phrase to keep, this but might be part of something else
				backup = entities[j]
				total  = probs[j]
				previous = words[j] + " "
			elif backup != "" and entities[j][0] == "I": # Noun phrase and this is the second part
				previous += words[j] + " "
				counter += 1
				total += probs[j]
			else: # A simple noun
				if words[j] != "Mr" and words[j] != "Mrs" and words[j] != "Miss":
					my_entities.append([words[j],"noun",probs[j]])

        else: # It might be end of a group of words to keep   	
        	if backup != "": 
        		parts = previous.split()			      # Refinement: make sure that the noun entities are consecutive words in the sentence
        		pos = words.index(parts[0])
        		if len(parts) > 1 and len(words)>pos: # words[pos+1] is the next word, compare it to the second word in the string previous
        			if words[pos+1] == parts[1]:        # Yes these words follow each other
        				my_entities.append([previous,backup,total/counter])
        			else:                             # ooh these words need to be split, they are not together in the sentence
        				my_entities.append([parts[0],backup,total/counter])
        				my_entities.append([" ".join(parts[1::]),backup,total/counter])
        		else: # It was a word by itself 
        			my_entities.append([previous,backup,total/counter])
      			backup = ""  
        		counter = 1
        		previous = ""
        		total = 0    	

""" This function parses a English sentence, finds entities tries to identify what it is and calculates probabilities """
def english_language(sentence):
	tokens = nltk.word_tokenize(sentence) # Array of words
	tokens = nltk.pos_tag(tokens)         # Result as [(1st word,grammatical value),...,(last word,grammatical value)]
	tags = []    						  # entity type such as organisation,person,location...  ('O' if none)
	weights = [] 						  # Probabilities for each word which has been tagged ('O' by default)

	for i in range(len(tokens)): 						   # Find nouns and entities with probabilities for each word in a sentence
		if tokens[i][0] not in punctuation and (tokens[i][1] == "NN" or tokens[i][1] == "NNS"):  # noun found (singular or plural), tag it
			tags.append("NOUN")
			weights.append(0)
		elif tokens[i][1] == "NNP" and tokens[i][0] not in punctuation: # noun phrase:  look for entities ('O' if none)
			try:
				tag = chunker._tagger.choose_tag(tokens, i, tags)       # may crash with IndexError': prevtag = history[index-1] list index out of range
			except Exception, e:
				print e 
				tag = "NOUN"
			if tag != "O": 														 # with the entity tag, find probability
				featureset = chunker._tagger.feature_detector(tokens, i, tags)   # Features of this word
				dist = maxEnt.prob_classify(featureset)                          # Find entity distances     
				tags.append(tag) 
				weights.append(dist.prob(tag)) 
			else: # no tag
				tags.append("I") # Trick: it is part of a noun phrase that has not been recognised but needs keeping (I-person...I-GPS?)
				weights.append(0)  
		else: # Anything else than a noun or a noun phrase to be ignored
			tags.append("O") 
			weights.append(0)  
	english_nouns(tags,weights,[x[0] for x in tokens]) # Retrieve and display entities with their probabilities

""" Function that splits a French sentence into words and look for nouns and their roles (thing, people, place) """
def french_language(sentence):
	banned_words = ["le","la","les","un","une","des","mais","ou","et","donc","or","ni","car","enfin",\
	                 "il","elle","soit","qu\xe2\x80\x99elle","qu\xe2\x80\x99il","que"] # words that cannot be entities
	prep_place = ["dans","sur","\xc3\xa0","sous","pr\xc3\xa8s","au","aux","'\xe0'"]    # prepositions preceeding a place
	entities = []								
	probs = []
	tags = []

	sentence = sentence.replace("l'","le ")											   # Trick replace "d'" and "l'" by "de" and "le"
	sentence = sentence.replace("L'","Le ")
	sentence = sentence.replace("d'","de ")
	sentence = sentence.replace("l\xe2\x80\x99","le ")
	sentence = sentence.replace("d\xe2\x80\x99","de ")

	# 1) Get grammar of each word in sentence
	words = st_pos_french.tag(sentence.split())
	for i in range(len(words)): 						   			 
		myword=words[i][0]
		if len(myword) > 1 and myword[len(myword)-1] in punctuation: # if last character is a punctuation mark
			myword=myword[0:len(myword)-1]
		if len(myword) >1 and myword[len(myword)-1] in punctuation: # repeat in case there were 2 punctuation marks
			myword=myword[0:len(myword)-1]
		if len(myword) >1 and myword[len(myword)-1] in punctuation: # repeat in case there were 3 punctuation marks e.g. "),
			myword=myword[0:len(myword)-1]
		if myword != '' and myword[0] in punctuation: 			   # if first character is a punctuation mark
			myword=myword[1:]
		if myword != '' and myword[0] in punctuation: 			   # if first characters were 2 punctation marks e.g.("
			myword=myword[1:]
		if myword != '' and myword.lower() not in banned_words and not myword.isdigit() and 'N' in words[i][1] and not myword.endswith('ment'): 
			entities.append(myword)

	# 2) From all entities which are nouns, decide its function in the sentence and get its probability
	backup = ""
	word_list = [x[0] for x in words]
	previously = ""
	inserted = True
	for j in range(len(entities)): 					 				   # For all noun entities
		current_word = entities[j]	
		if current_word[0].isupper(): 				 				   # Starts with a letter in upper case
			if j > 0 and backup.lower() in prep_place: 				   # Previous word is a preposition defining a place
				if previously == "Person" and not inserted:
					my_entities.append([backup, "Person", 0.5])
					inserted = True
				my_entities.append([current_word, "Place", 0.5])
				previously = "Place"
			else:													   # Likely to be a person otherwise
				if previously == "Person":
					if following_words(current_word,backup,word_list): # It may be a group of words together
						my_entities.append([backup + " " + current_word, "Person", 0.5])
						inserted = True
					else:
						my_entities.append([backup,"Person",0.5])
				else:
					inserted = False
				previously = "Person"
		else: 															# First letter is lower case, it is just a noun
			if previously == "Person" and not inserted:
				my_entities.append([backup, "Person", 0.5])
				inserted = True
			my_entities.append([current_word, "Thing", 1])
			previously = "Thing"
		backup = current_word

""" Function that splits a Spanish sentence into words and look for nouns and their roles (thing, people, place) """
def spanish_language(sentence):
	nouns_list = []	
	delimiters = ["el","la","los","las","una","uno","en","a","un"]

	kept_words = []
	entity_words = []
	
	# Grammar parser
	sentence_tagged = uni_tag.tag(sentence.split(" ")) # [(word,grammar)...(,)]
	words = [x[0] for x in sentence_tagged]            # [word,word,word]
	c = 0
	for item in sentence_tagged:
		c += 1
		if not item[0].isdigit(): # eliminate numbers - check if it is a noun 
			if (item[1] and "nc" in item[1]) or (c>1 and item[0][0].isupper() and item[0].lower() not in delimiters):
				nouns_list.append(item[0]) 

	# Entity parser
	tagged = st_tag_english.tag(sentence.split())	
	
	# Group words together
	backup = ""
	previous = ""
	c = 0
	for item in nouns_list:
		c += 1
		# First deal with punctuation
		if item[0] in punctuation: # Remove punctuation
			item = item[1::]
		elif item[len(item)-1] in punctuation:
			item = item[0:len(item)-1]
		if item[0] in punctuation: # Repeat remove punctuation, in case they were 2 marks of punctuation following each other
			item = item[1::]
		elif item[len(item)-1] in punctuation:
			item = item[0:len(item)-1]
		
		# Look up for entity function form previous parsing: is is a thing? a person? a place etc.?
		# Careful entity parser and grammar parser do not cut the sentence the same way
		answer = lookup(str(transform(item)),tagged,words)  # find entity type for this item (careful with encoding)
		
		if backup == answer and answer != "O" and previous != "": # here we have 2 words following each other with the same entity, group them
			new_group = previous + " " + item
			my_entities.append([new_group,answer,0.5])
			previous = ""
		else:
			if c == 1 and answer == "O":						# first word in sentence and it is a thing, don't lose it!
				my_entities.append([item,"Thing",1])
			elif c == 2:										# second word in sentence and it hasn't been grouped, don't lose it!
				if [previous,"Thing",1] not in my_entities:
					my_entities.append([previous,backup,0.5])
				elif backup != "O":
					my_entities.append([previous,backup,0.5])					
			elif backup == "O":								# it is a thing by itself
				my_entities.append([previous,"Thing",1])
			elif backup != "O" and previous != "":			    # Entity by itself (hasn't been grouped)
				my_entities.append([previous,backup,0.5])				
			previous = item
		backup = answer

	# End of the sentence, save previous entity if it wasn't previously a group 
	if previous != "":
		if backup == "O":
			my_entities.append([previous,"Thing",1])
		else:
			my_entities.append([previous,backup,0.5])
	

""" Function that splits a German sentence into words and look for nouns and their roles (thing, people, place) """
def german_language(sentence):
	nouns_list = []
	important_nouns = {}
	tags = st_pos_german.tag(sentence.split())     # Grammar parser
	
	c = 0
	for t in tags:
		c += 1
		if "N" in t[1]: 						   # In German Nouns can be anything such as NN or NE
			nouns_list.append(t[0].decode('utf8'))				
			if t[0][0].isupper() and c > 1: 	   # We have a word in Upper case and it is not the first word in the sentence
				important_nouns[t[0]] = "Person"

	all_words = sentence.decode('utf8').split()	   # Keep a backup of all words in the sentence WITHOUT punctuation (the entity parser includes it)
	entities = st_tag_german.tag(sentence.split()) # Entity parser

	backup = ""
	previous = ""
	pos = 0
	for i in range(len(entities)): 				         	     # For all entities
		if len(entities[i][0]) > 1 and (entities[i][0][1].isalpha()):
			if entities[i][1] == "NN" or entities[i][1] == "NE": # NN or NE are nouns
				myent = "N"
			else:
				myent = entities[i][1]			
			if backup == myent and myent != 'O' and i > 1:	     # 2 consecutive words in the sentence with the same function		
				new_group = all_words[i-pos-1]+u" "+ all_words[i-pos] # Useful copy of words (utf8 cannot be used in Stanford Parser) 
				if entities[i][0] in important_nouns:		 # remove this word by itself
					del important_nouns[entities[i][0]]
					pos = nouns_list.index(entities[i][0])
					nouns_list.pop(pos)
				if previous in important_nouns:				 # remove the previous word by itself
					del important_nouns[previous]
					pos = nouns_list.index(previous)
					nouns_list.pop(pos)
				nouns_list.append(new_group)				 # group both words TOGETHER
				important_nouns[new_group] = myent
				previous = ""
			else:
				previous = entities[i][0]		
			backup = myent
		else:
			pos += 1	# punctuation

	for n in nouns_list: 				  # Group results from both parsing
		if n[0] in punctuation:           # Remove first character if it is a mark of punctuation
			n = n[1::]	
		if n[len(n)-1] in punctuation:    # Remove last character if it is a mark of punctuation
			n = n[0:len(n)-1]
		if n[len(n)-1] in punctuation:    # Remove last character again in case there were 2 marks of punctuation following each other
			n = n[0:len(n)-1]
		if n in important_nouns:		  # If it is a named entity keep its name 
			my_entities.append([n, important_nouns[n], 0.5])	
		else:                             # Otherwise define it as a 'thing'
			my_entities.append([n, "Thing", 1])


""" Main function that displays results of parsing and insert data into database """
def parse_my_text(mytext,mylanguage,url):
	d = datetime.datetime.now()

	# Calulate frequency of each word in lower case
	my_tokens = nltk.word_tokenize(mytext.lower())
	cnt = collections.Counter(my_tokens)

	# Parse each sentence
	sentences = sent_detector.tokenize(mytext)
	for s in sentences:
		print s.encode('utf8')
		langs[mylanguage](s.encode('utf8'))
			
	# Display results
	print "Word","Frequency","Entity","Probability"
	print "----","---------","------","-----------"
	for e in my_entities:
		if e[0] in cnt:
			if mylanguage != "de":
				insert_db(e[1],e[0],d,url,cnt[e[0]],e[2])
			else:
				insert_db_german(e[1],e[0],d,url,cnt[e[0]],e[2])
			print e[0],cnt[e[0]],e[1],e[2] 	   # word, freq, entity class, prob.
		else:
			total = 0
			split_group = e[0].split()         # for a group of words, add frequencies of each word 
			for item in split_group:
				total += cnt[item.lower()]
				if total == 0 :                # this is the first time we found this word
					total = 1
			print e[0],total,e[1],e[2]
			if mylanguage != "de":
				insert_db(e[1],e[0],d,url,total,e[2])
			else:
				insert_db_german(e[1],e[0],d,url,total,e[2])
	db.commit()
#--------------------------------------------------------------------------------------------------------------------------------------


# 3 arguments from command line e.g. python nlp_analyser.py argv1=url argv2=en argv3=html 
# what arguments and what order?                       1: web address, 2: language code (see the dictionary 'langs'), 3: type {html, json} 
langs = {'en':english_language,'fr':french_language,'de':german_language,'es':spanish_language}

if len(sys.argv) <= 3:           # 3 arguments are required 
	print "you need to pass a url,a language and a type (html/json) in the command line"
else:
	if sys.argv[3]== "html":     # HTML page
		if sys.argv[2] in langs: # Get newspaper article
			a = Article(sys.argv[1], language=sys.argv[2])
			a.download()
			a.parse()
			parse_my_text(a.text,sys.argv[2],sys.argv[1])
		else:
			print "Sorry only English, French, German or Spanish at the moment"
		
	elif sys.argv[3] == "json":     # Json page
		j = urllib2.urlopen(sys.argv[1])
		j_obj = json.load(j)
		obj = j_obj['objects']
		print re.sub('<[^<]+?>', '', obj[0]['text'])
		if sys.argv[2] in langs:
			parse_my_text(re.sub('<[^<]+?>', '', obj[0]['text']),sys.argv[2],sys.argv[1])
		else:
			print "Sorry only English, French, German or Spanish at the moment"

	else: # Not Json and not Html
		print "%s unrecognised (please specify html or json)" %sys.argv[3]	
