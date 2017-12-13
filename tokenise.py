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
parser.add_argument('-t', '--tags', action='store_true', help='show tags')

args = vars(parser.parse_args())

class Tokeniser:

	def __init__(self, hfst):
		self.hfst = hfst

	def tokenise(self, text):
		chars = list(text)
		n = len(chars)+1

		D = np.zeros([(n),], dtype=object)

		for i in range(0,n):
			D[i] = "FAIL"

		first = self.isWord(chars[0:1])
		if first != False:
			D[1] = [first]

		for i in range(2,n):
			for j in range(0,i+1):
				right = self.isWord(chars[i-j:i])
				if right != False:
					left = D[i-j]
					if left != "FAIL":
						D[i] = left + [right]
					else:
						D[i] = [right]

		tokens = D[-1]

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

	def no_tags(self):
		return self.word

	def with_tags(self):
		strtag = ""
		for tag in self.tags:
			strtag += tag
		return self.word + strtag


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
		if not args['tags']:
			units = [unit.no_tags() for unit in units]
		else:
			units = [unit.with_tags() for unit in units]
		print(' '.join(units))

main(args)
