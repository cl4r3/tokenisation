# Spaceless Segmentation

Spaceless Segmentation is a tokeniser that *should* work for all spaceless languages. Currently, the only language which Spaceless Segmentation has been tested on is Chinese.

# Using Spaceless Segmentation

## `tokenise.py`

	usage: tokenise.py [-h] -d DICT [-a] [-t TRAINING] -i INPUT

	Spaceless Segmentation.

	optional arguments:
	  -h, --help            show this help message and exit
	  -d DICT, --dict DICT  dictionary file
	  -a, --all             return all possible segmentations instead of using a
	                        ranking algorithm
	  -t TRAINING, --training TRAINING
	                        file which trained data is obtained from. required if
	                        -a/--all is not set.
	  -i INPUT, --input INPUT
	                        input file

`tokenise.py` takes in input text from stdin and outputs the tokenised text from stdout.

Dictionaries are a crucial piece of data that Spaceless Segmentation requires. The larger your dictionary is, the more accurate your tokenisations will be.

## Tokenising a piece of example text

	$ ./tokenise.py -d dict/example.txt -a -i examples/example.txt

This will take in input text `examples/example.txt` and tokenise it with dictionary `dict/example.txt`. The "all-possible segmentations" option was set ("-a") and hence training data is not required.

	$ cat dict/example.txt
	efghi:efghi<efghi>
	a:a<a>
	cdefghi:cdefghi<cdefghi>
	abcdefg:abcdefg<abcdefg>
	i:i<i>

	$ cat examples/example.txt
	xabcdefghixghix

The expected output should look like this:

	^x/*x$ ^abcdefghi/a+*b+cdefghi/abc+*d+efghi/abcdefg+*h+i$ ^x/*x$ ^g/*g$ ^h/*h$ ^i/i$ ^x/*x$

As you can see, the tokeniser obtains all possible segmentations. Note that the tokeniser, however, is unable to select the best segmentation. This can be done by using a set of training data. To do that, we need to use `train.py` to obtain training data from a corpus.

## `train.py`

	usage: train.py [-h] -d DICT -t TRAINING -i [INPUT [INPUT ...]] [-j J] [-a]

	Spaceless Segmentation Trainer.

	optional arguments:
	  -h, --help            show this help message and exit
	  -d DICT, --dict DICT  dictionary file
	  -t TRAINING, --training TRAINING
	                        file which trained data is obtained from.
	  -i [INPUT [INPUT ...]], --input [INPUT [INPUT ...]]
	                        input file
	  -j J                  number of threads used
	  -a, --amend           option to amend training data instead of creating new
	                        training file

Training data is crucial to Spaceless Segmentation. With a large enough corpus and a good dictionary, the tokeniser is likely to be more accurate.

`train.py` will write the new training data back to the training file specified. `train.py` uses multithreading, so a number of threads can be specified to concurrently process the data.

## Training an example piece of text

This is the text we will be training:

	$ cat corpus/example.txt
	xabcdefghix
	aaaaaaa
	cdefghi

Now, we supply a dictionary, a training file and a corpus as follows. The last part, '-j 1', specifies the number of threads used. As this is a small file, a single thread will suffice. For larger corpus, you may want to tune the number of threads according to your machine specifications.

	$ ./train.py -d dict/example.txt -t probabilities.txt -i corpus/example.txt -j 1
	Creating new training file...
	Loaded 3 lines from 'corpus/example.txt'.
	Finished processing 'corpus/example.txt'.

	All files processed.
	Total number of tokens in dictionary: 8

You should get this in `probabilities.txt`:

	abcdefg:0.25
	cdefghi:1.25
	a:7.25
	abc:0.25
	i:0.25
	x:1.0
	abcdefghi:0.25
	efghi:0.25

You can see that `a` has a really high frequency compared to the other segmentations.

Now, let's try using the training data with our tokeniser.

	$ ./tokenise.py -d dict/example.txt -t probabilities.txt -i examples/example.txt
	^*x/*x$ ^a/a$ ^*b/*b$ ^cdefghi/cdefghi$ ^*x/*x$ ^*g/*g$ ^*h/*h$ ^i/i$ ^*x/*x$

Note the difference: "a *b cdefghi" was chosen compared to other sequences available as a and cdefghi both appeared more often than the other tokens.

# Using for real tokenisation

There are dictionary and corpus files provided which can be used for tokenisation.

Training can be done in stages; to do so, use the -a/--amend option to amend onto an already created training file. By default, a new training file will be created if you do not toggle this action.

# Dictionary and corpus files

Spaceless Segmentation comes with default dictionary files for the following languages:

* Chinese (simplified) - **dict/zh_CN.txt**

You can ask for a corpus by contacting wei2912.supp0rt@gmail.com.

# How it works

Spaceless Segmentation uses a dictionary trie in Python and a finite state transducer to obtain all possible segmentations based on a dictionary. Here's how it looks like:

## Dictionary trie

The dictionary looks like this:

	abc:abc<abc>
	abcde:abcde<abcde>
	ade:ade<ade>

Where the format is `word:root form<PoS tag>`.

The program goes through 'abc' first.

	(0, 'a'): 1
	
is added to the dictionary where 0 is the initial state, 'a' is the letter and 1 is the new state. The program then takes in the new state and uses that as the current state for the next character.

	(1, 'b'): 2
	(2, 'c'): 3

At this moment, the word 'abc' has ended. 3 is added to the array of final states; this array records down where a word ends so that we can mark it as a token later on.

Now, the program goes through 'abcde'. 'abc' was already added to the trie, so the program goes through these 3 letters to arrive at state 3.

	(0, 'a'): 1
	(1, 'b'): 2
	(2, 'c'): 3

The program then adds more entries to the dictionary.

	(3, 'd'): 4
	(4, 'e'): 5

Once again, the end of the word has been reached and 5 is added to the list of final states.

Now, the dictionary goes through 'ade'.

	(0, 'a'): 1

The dictionary adds a new entry.

	(1, 'd'): 6 # new state was created
	(6, 'e'): 7

The program is now done with initializing the trie.

## Tokenization

After the initialization of the trie, it uses a [finite state transducer](http://en.wikipedia.org/wiki/Finite_state_transducer) to tokenise the text.

The finite state transducer goes through the text and advances states when the state can continue on the next character, otherwise terminates the state. When the state reaches a final state, it is added to the list of marks. Invalid characters are skipped.

When all states are terminated, the program does a flush. Each character in the sequence of characters parsed is added to `marks` as an invalid character to fill up any blanks. Then, the program passes the marks to a sequence generator that generates all possible sequences.

The sequence generator works from the start to the end as a recursive function. It will take in a token as part of a sequence if: 1) it is valid OR 2) it is invalid but there are no valid tokens starting with that invalid character. Once it obtains the list of sequences, it returns that to the tokeniser.

The tokeniser then takes in the sequences and generates a lattice that looks like this:

    ^abc/ab+c/a+bc/abc$

There are 3 possible segmentations: "ab c", "a bc" and "abc". All this is compressed into a single "unit".

When the tokeniser finishes, it returns the set of units, to be printed out or written to the output file.

Here's what the trace looks like for example text:

	abc:abc<abc>
	efghi:efghi<efghi>
	a:a<a>
	cdefghi:cdefghi<cdefghi>
	abcdefg:abcdefg<abcdefg>
	i:i<i>

and input:

	xabcdefghixghix

Trace:

	spos = 0 # start position
	cpos = 0 # current position

	| denotes the two pointers.
	The two numbers after the input denote spos and cpos.
	(0, "") denotes a state where 0 is the start position of that token and "" is the characters consumed.

	|x|abcdefghixghix 0 1 (0, "x") - MARK(0, "*x", 1), TERMINATE

As `x` is an invalid token, the tokenizer prepends "*" to the token (this indicates that the token is invalid) and terminates the token. As all tokens are terminated, the tokenizer flushes all tokens.

	marks = (0, "*x", 1)
	possible sequences:
		(0, "*x", 1)

The unit generated looks like this:

	^x/*x$

Then, a new blank state is created and the start position brought forward.

	x|a|bcdefghixghix 1 2 (1, "a") - MARK(1, "a", 2), CONTINUE

In our dictionary, there are words that continue after "a", so we will not destroy this state. No words start with the next character, "b", so we will not create a new state starting from 2.

	x|ab|cdefghixghix 1 3 (1, "ab")

Words that start with the next character, "c", exist ("cdefghi"), so we will create a new state.

	x|abc|defghixghix 1 4 (1, "abc") - MARK(1, "abc", 4), CONTINUE (3, "c")

There's "abcde" left, so we continue.

	x|abcd|efghixghix 1 5 (1, "abcd") (3, "cd")

Words that start with the next character, "e", exist ("efghi"), so we will create a new state.

	x|abcde|fghixghix 1 6 (1, "abcde") (3, "cde") (5, "e")
	x|abcdef|ghixghix 1 7 (1, "abcdef") (3, "cdef") (5, "ef")
	x|abcdefg|hixghix 1 8 (1, "abcdefg") - MARK(1, "abcdefg", 8), TERMINATE (3, "cdefg") (5, "efg")

No other words are possible after "abcdefg", so the token is terminated.

	x|abcdefgh|ixghix 1 9 (3, "cdefgh") (5, "efgh")

There's a single-character token, "i", in the dictionary. We'll create a new state for that.

	x|abcdefghi|xghix 1 10 (3, "cdefghi") - MARK(1, "cdefghi", 10), TERMINATE (5, "efghi") - MARK(5, "efghi", 10), TERMINATE (9, "i") - MARK(9, "i", 10), TERMINATE

All tokens terminated, so we'll flush the tokens. However, if you noticed, there are a few blanks inbetween our tokens. This is because a few letters are invalid. To fix this, every character in the string is treated as an invalid character and appended to marks, excluding valid single-character tokens.

	marks: (1, 'a', 2) (1, 'abc', 4) (1, 'abcdefg', 8) (3, 'cdefghi', 10), (5, 'efghi', 10) (9, 'i', 10) (2, '*b', 3) (3, '*c', 4) (4, '*d', 5), (5, '*e', 6) (6, '*f', 7) (7, '*g', 8) (8, '*h', 9)

The sequence generator only selects an invalid token if no valid tokens starts with that invalid token to limit long sequences of invalid text. As such, it produces the below sequences:

	(1, 'a', 2), (2, '*b', 3), (3, 'cdefghi', 10)
	(1, 'abc', 4), (4, '*d', 5), (5, 'efghi', 10)
	(1, 'abcdefg', 8), (8, '*h', 9), (9, 'i', 10)

All are combined into this unit:

	^abcdefghi/a+*b+cdefghi/abc+*d+efghi/abcdefg+*h+i$

A new state is created once again.

	xabcdefghi|x|ghix 10 11 (10, "x") - MARK(10, "*x", 11), TERMINATE

Another invalid token, so we'll flush the tokens.

	marks = (10, "*x", 11)
	possible sequences:
		(10, "*x", 11)

The unit generated looks like this:

	^x/*x$

The rest are invalid tokens as well, so I'll shorten everything.

	xabcdefghix|g|hix 11 12 (12, "g") - MARK(11, "*g", 12), TERMINATE - ^g/*g$
	xabcdefghixg|h|ix 12 13 (13, "h") - MARK(12, "*h", 13), TERMINATE - ^h/*h$
	xabcdefghixgh|i|x 13 14 (13, "i") - MARK(13, "*i", 14), TERMINATE - ^i/*i$
	xabcdefghixghi|x| 14 15 (12, "x") - MARK(14, "*x", 15), TERMINATE - ^x/*x$

After this, all the units are combined to form a lattice:

	^x/*x$ ^abcdefghi/a+*b+cdefghi/abc+*d+efghi/abcdefg+*h+i$ ^x/*x$ ^g/*g$ ^h/*h$ ^i/i$ ^x/*x$

## Characteristics

This tokeniser is able to obtain all possible segmentations, excluding invalid sequences. As compared to LRLM and RLLM matching, it is able to consider shorter tokens.

## Approach to ranking

Tokens are given a fractional count obtained from the possible number of segmentations. For example, if this is seen in the corpus text:

	^abcde/abc+de/ab+cde$

`abc`, `de`, `ab` and `cde` will all be assigned a fractional count of 0.5. This is because we are not certain which segmentation is correct.

Sequences are then ranked and the most probable sequence is selected.

# Example files

The following files are provided as examples in `examples/`.

* taoteching_1.txt - 道德经 (Tao Te Ching), Taoist text by Lao Tzu, chapter 1 ([http://www.tao-te-king.org/](http://www.tao-te-king.org/))
* the_analects_1.txt - 论语 (The Analects), Confucius sayings, chapter 1 ([http://ctext.org/analects](http://ctext.org/analects))
* medicine_1.txt - 药 (Medicine), popular short story by Lu Xun, chapter 1 ([http://www-personal.umich.edu/~dporter/sampler/medicine.html](http://www-personal.umich.edu/~dporter/sampler/medicine.html))
* recursion.txt - Recursion from Chinese Wikipedia ([http://zh.wikipedia.org/wiki/%E9%80%92%E5%BD%92](http://zh.wikipedia.org/wiki/%E9%80%92%E5%BD%92))