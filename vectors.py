#-*- coding: utf8 -*-
from __future__ import division
import math

""" Definition of documents and term frequencies """
documents = ["Sense and Sensibility","Pride and Prejudice","Wuthering Heights"]
words = ["affection","jealous","gossip","wuthering"]

frequencies = {}
frequencies[0] = {
	"affection":115,
	"jealous":10,
	"gossip":2,
	"wuthering":0
}

frequencies[1] = {
	"affection":58,
	"jealous":7,
	"gossip":0,
	"wuthering":0
}

frequencies[2] = {
	"affection":20,
	"jealous":11,
	"gossip":6,
	"wuthering":38
}

""" compute vector and cos similarities """

# get the weights for each term in each document
log_weighting = []
for i in range(len(documents)):
	l = []
	for j in words:
		if frequencies[i][j] != 0:
			w = 1 + math.log10(frequencies[i][j])
			l.append(w)
		else:
			l.append(0)
	log_weighting.append(l)	
print log_weighting

# compute the log weighting after length normalisation
after_normalisation = []
for d in range(len(documents)):
	tot = 0
	for k in range(len(words)):
		tot += math.pow(log_weighting[d][k], 2) # euclidean distance square root of each coordinate squared and added together
	tot = math.sqrt(tot)
	l = []
	for k in range(len(words)):
		l.append(log_weighting[d][k]/tot)
	after_normalisation.append(l)
print after_normalisation

# compute distances between documents
dist_values = []
dist_names  = []
for i in range(len(documents)):
	for j in range (0,len(documents)):
		if (i > 0 or j > 0) and (i + j < len(documents)) and (i != i + j):
			tot = 0
			for k in range(len(words)):
				tot += after_normalisation[i][k]*after_normalisation[i+j][k]
			dist_values.append(tot)
			dist_names.append("("+documents[i]+","+documents[i+j]+")")
m = max(dist_values)
pos = dist_values.index(m)
print dist_names[pos],m #higest value, closest match betwen these documents 



