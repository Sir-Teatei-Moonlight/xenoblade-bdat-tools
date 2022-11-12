# coding=utf-8

# Sir Teatei Moonlight's murmur32 hashmapper (mostly for Xenoblade BDAT2 purposes)
# reads a file, takes all the "murmur32_A1BD0758" strings, and replaces them with "spam"
# requires a xc3_hashes.txt file in the same folder that's tab-delineated, e.g.:
# A1BD0758	spam
# 680474C1	eggs
# version 1.0.0 ~ 2022-09-02 ~ basic functionality

import os
import re
import struct
import sys
import traceback

if len(sys.argv) < 2:
	quit("inFilename?")
inFilename = sys.argv[1]
outFilename = "./dehashed.txt"

hashFileName = "xc3_hashes.txt"

hashDict = {}
currentLine = ""
currentLineNumber = 0
try:
	with open(hashFileName,"r") as hashFile:
		for line in hashFile:
			currentLine = line
			currentLineNumber += 1
			(key,value) = line.split("\t")
			if value: # don't add hashes if they map to blanks (which means they're unknowns)
				if key in hashDict:
					print("Warning: found duplicate hash "+key+" in file (keeping oldest entry only)")
				else:
					hashDict[key.upper()] = value.strip()
	hashDict["00000000"] = "" # special case enforcement
except FileNotFoundError:
	print("This script requires "+hashFileName+" to exist in the same folder.")
	print("This file is not included with the script because it is (currently) liable to become outdated very quickly.")
	print("It should be a simple tab-separated text file in the following format:")
	print()
	print("A1BD0758\tspam")
	print("680474C1\teggs")
	print()
	print("It should not be difficult to create this sort of file yourself by starting with the following spreadsheet:")
	print("https://docs.google.com/spreadsheets/d/1PpnIHqj9SU0tHYDf57Fse-OykrjvSPWM6PbsfQFghYw/edit#gid=0")
	quit()
except Exception as e:
	print("The provided "+hashFileName+" does not seem to be formatted correctly on line {}:".format(currentLineNumber))
	print()
	print(currentLine)
	#print() # built-in the line itself, probably
	print("It might have too many tabs, too few tabs, or be broken in some other way.")
	print("It ought to be a tab-separated text file such as this:")
	print()
	print("A1BD0758\tspam")
	print("680474C1\teggs")
	print()
	print("The exact error thrown follows:")
	print(traceback.format_exc())
	quit()

murmurRegex = re.compile("murmur32_([0-9A-F]{8})",re.IGNORECASE)
unknownHashes = [] # yeah this is a global, bite me

def getHashedString(regexObj):
	try:
		return hashDict[regexObj.group(1).upper()]
	except KeyError:
		unknownHashes.append(regexObj.group(1))
		return "murmur32_"+regexObj.group(1) # if the hash isn't known, no-op the replacement

with open(inFilename,"r") as f:
	with open(outFilename,"w",encoding="utf-8") as o:
		o.write(re.sub(murmurRegex,getHashedString,f.read()))

decision = input("Print list of {} unknown hashes? (y/n) ".format(len(unknownHashes)))
if decision.lower() == "y":
	for h in sorted(list(set(unknownHashes))):
		print(h)

#[EOF]