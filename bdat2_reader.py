# coding=utf-8

# Sir Teatei Moonlight's Xenoblade BDAT2 reader
# version 0.2.0 ~ 2022-09-02 ~ minimal support for value types 10-13, change hashes to print as uppercase
# version 0.1.0 ~ 2022-08-17 ~ can read basic bdat2s, only tried ones with simple ints and strings in them, hashes just get printed raw

import os
import struct
import sys

if len(sys.argv) < 2:
	quit("inFilename?")
inFilename = sys.argv[1]
outFilename = "./bdat2_outFile.txt"

game = "xc3"
#while game not in ["xc3"]:
#	game = input("game? (XC3) ").lower()

newlineReplacement = input("newline replacement in strings? (leave blank for raw) ")

# only XC1 and XCX seem to be big-endian so far (everything since is little), so don't need to check that

u8Code = "<B"
i8Code = "<b"
u16Code = "<H"
i16Code = "<h"
u32Code = "<L"
i32Code = "<l"
fpCode = "<f"

valueTypeDict = { # the ones with blank second items are not parsed normally
				1:["u8",u8Code],
				2:["u16",u16Code],
				3:["u32",u32Code],
				4:["i8",i8Code],
				5:["i16",i16Code],
				6:["i32",i32Code],
				7:["str",""],
				8:["fp",fpCode],
				9:["hash",""],
				10:["%",i8Code],
				11:["?32_t11",u32Code],
				12:["?8_t12",u8Code],
				13:["?16_t13",u16Code],
				-1:["flag",""],
				}

def readAndParseInt(inFile,bytes,signed=False):
	if bytes == 1:
		parseString = i8Code if signed else u8Code
	elif bytes == 2:
		parseString = i16Code if signed else u16Code
	elif bytes == 4:
		parseString = i32Code if signed else u32Code
	else:
		raise ValueException("invalid int bytesize: "+str(bytes))
	return struct.unpack(parseString,inFile.read(struct.calcsize(parseString)))[0]

def intToHash(val):
	return "murmur32_"+format(val,"#010X")[2:]
def readStr(inFile):
	strBytes = b""
	c = inFile.read(1)
	while c != b"\x00" and c != b"":
		strBytes += c
		c = inFile.read(1)
	try:
		return strBytes.decode("shift-jis")
	except:
		print("bad shift-jis:",inFile.tell(),strBytes)
		return strBytes.decode("utf-8")
def readValueStr(inFile):
	strBytes = b""
	c = inFile.read(1)
	while c != b"\x00" and c != b"":
		strBytes += c
		c = inFile.read(1)
	return strBytes.decode("utf-8")

with open(inFilename,"rb") as f:
	fileMagic = f.read(4)
	if fileMagic != b"BDAT":
		quit("not a BDAT (fileMagic: {})".format(fileMagic))
	typeMagic = f.read(2) # seems to be 0x0410 for containers, 0x0430 if not
	bdatStartOffset = 0
	if typeMagic == b"\x04\x10": # container
		bdatStartOffset = 0x14
		unknown1 = f.read(2)
		bdatCount = readAndParseInt(f,2)
		if bdatCount > 1: # if it's only a single, can work with that - otherwise, needs to be split first
			quit("seems to be a container of {} bdat2s, please split it first".format(bdatCount))
		f.seek(bdatStartOffset)
		innerMagic = f.read(4)
		if innerMagic != b"BDAT":
			quit("not a BDAT (fileMagic: {})".format(innerMagic))
		innerTypeMagic = f.read(2)
		if innerTypeMagic != b"\x04\x30":
			quit("unknown innerTypeMagic: {}".format(innerTypeMagic))
	f.seek(bdatStartOffset+8)
	memberCount = readAndParseInt(f,4)
	entryCount = readAndParseInt(f,4)
	baseID = readAndParseInt(f,4)
	unknownHash1 = readAndParseInt(f,4)
	memberTableOffset = readAndParseInt(f,4)
	mysteryNamesOffset = readAndParseInt(f,4)
	dataOffset = readAndParseInt(f,4)
	unknown2 = readAndParseInt(f,4)
	stringsOffset = readAndParseInt(f,4)
	stringsLength = readAndParseInt(f,4)
	
	memberSize = 3
	
	memberNames = []
	memberNameOffsetList = []
	memberTypes = []
	valueTypes = []
	arrayCounts = []
	flagData = []
	
	f.seek(bdatStartOffset+memberTableOffset)
	for c in range(memberCount):
		infoOffset = memberTableOffset + (c * memberSize)
		memberType = 1 #readAndParseInt(f,1) no idea if arrays and flags are still around in the same way yet
		memberTypes.append(memberType)
		if memberType == 3: # flags
			pass # no idea how this works yet
		else: # not flags
			flagData.append([])
			f.seek(bdatStartOffset+infoOffset) # maybe not needed, but to be safe
			valueType = readAndParseInt(f,1)
			valueTypes.append(valueType)
			memberNameOffset = readAndParseInt(f,2)
			memberNameOffsetList.append(memberNameOffset)
		if memberType == 2: # array
			pass # no idea how this works yet
		else: # not array
			arrayCounts.append(1)
	
	memberNames = ["" for i in range(memberCount)]
	f.seek(bdatStartOffset+stringsOffset+1) # dunno what the one is about yet
	tableName = intToHash(readAndParseInt(f,4))
	for c in range(memberCount):
		f.seek(bdatStartOffset+stringsOffset+memberNameOffsetList[c])
		memberNames[c] = intToHash(readAndParseInt(f,4))
	
	with open(outFilename,"w",encoding="utf-8") as o:
		o.write(tableName+"\t"+"\t".join(memberNames)+"\n")
		o.write("\t"+"\t".join([str(x) for x in memberTypes])+"\n")
		o.write("\t"+"\t".join([valueTypeDict[x][0] for x in valueTypes])+"\n")
		o.write("\t"+"\t".join([str(x) for x in arrayCounts])+"\n")
		o.write("\t"+"\t".join([str(x) for x in flagData])+"\n")
		o.write("\t"+"\t".join([str(x) for x in memberNameOffsetList])+"\n")
		o.write("\n")
		
		# got the columns, now get each row's values
		f.seek(bdatStartOffset+dataOffset)
		for i in range(entryCount):
			values = []
			for c in range(memberCount):
				itemIndex = i
				if memberTypes[c] == 1 or memberTypes[c] == 2: # scalar, array
					arrayCount = arrayCounts[c]
					for a in range(arrayCount):
						valueType = valueTypes[c]
						if valueType == 7: #str
							savepoint = f.tell()
							f.seek(bdatStartOffset+stringsOffset+readAndParseInt(f,4))
							valueStr = readValueStr(f)
							if newlineReplacement:
								valueStr = valueStr.replace("\x0a",newlineReplacement)
							values.append(valueStr)
							f.seek(savepoint+4)
						elif valueType == 9: #hash
							#print(f.tell())
							values.append(intToHash(readAndParseInt(f,4)))
						else:
							values.append(struct.unpack(valueTypeDict[valueType][1],f.read(struct.calcsize(valueTypeDict[valueType][1])))[0])
				elif memberTypes[c] == 3: # flags - some duplication is necessary, in case we can't guarantee that flags always come after their root
					flagRootIndex = flagData[c][0]
					flagVarOffset = itemOffset + memberNameOffsetList[flagRootIndex]
					f.seek(flagVarOffset)
					flagValueType = valueTypes[flagRootIndex]
					if flagValueType == 7 or flagValueType == 8 or flagValueType == 9: # non-int flag root types (bad)
						values.append("[f!]")
					else:
						flagRootValue = struct.unpack(valueTypeDict[flagValueType][1],f.read(struct.calcsize(valueTypeDict[flagValueType][1])))[0]
						flagMask = flagData[c][1]
						values.append((flagRootValue & flagMask) > 0)
				else: # unsupported/wrong data
					values.append("[~]")
			o.write(str(i+baseID)+"\t"+"\t".join([str(x) for x in values])+"\n")

#[EOF]