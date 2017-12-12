#!/usr/bin/env python

import sys
import argparse
import numpy as np
import hfst

if sys.version_info < (3, 0):
	print("Spaceless Segmentation requires Python 3.0 and above.")
	exit(1)

parser = argparse.ArgumentParser(description='Spaceless Segmentation.')
parser.add_argument('-hf', '--hfst', help='hfst file', required=True)
parser.add_argument('-i', '--input', help='input file', required=True)

args = vars(parser.parse_args())

class Tokeniser:

	def __init__(self, hfst):
		self.hfst = hfst

	def tokenise(self, text):
		chars = list(text)
		n = len(chars)

		D = np.zeros([len(chars), len(chars)], dtype=object)

		for i in range(0,n):
			for j in range(0,n):
				D[i,j] = []

		for l in range(1,n):
			for i in range(0,n-1-l):
				j = i + l
				units = []
				for k in range(i,j-1):
					if (D[i,k] != "FAIL") and (D[k+1,j] != "FAIL"):
						if len(units) < len(D[i,k])+len(D[k+1,j]):
							units = D[i,k] + D[k+1,j]
					if len(units) == 0:
						unit = self.isWord(chars[i:j])
						if unit != False:
							D[i,j] = [unit]
						else:
							D[i,j] = "FAIL"
					else:
						D[i,j] = units
					print(D[i,k])
		tokens = D[0,n-1]

		return tokens

	def isWord(self, ls):
		string = ''.join(ls)
		filename = "apertium-jpn/jpn.automorf.hfst"
		input_stream = hfst.HfstInputStream(filename)
		analyser = input_stream.read()
		fullout = analyser.lookup(string)
		if len(fullout) == 0:
			return False
		output = fullout[0][0]
		items = output.split("<",1)
		token = Unit(items[0], items[1])
		return token

class Unit:
	def __init__(self, word, tagtext):
		self.word = word
		self.tags = []
		tags = tagtext.split("<")
		for i in range(1, len(tags)):
			self.tags.append("<"+tags[i])

	def __repr__(self):
		return self.word

	def get_tags(self, word):
		return self.tags


def main(args):
	hfst = args['hfst']
	tokeniser_obj = Tokeniser(hfst)

	tokenised = []
	i_file = open(args['input'], 'r')
	for line in i_file:
		line = line.strip()
		if line == "":
			continue

		units = tokeniser_obj.tokenise(line)
		units = [unit.__repr__() for unit in units]
		print(' '.join(units))

main(args)
