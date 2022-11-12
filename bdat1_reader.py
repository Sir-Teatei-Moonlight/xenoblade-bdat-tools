# coding=utf-8

# Sir Teatei Moonlight's Xenoblade BDAT1 reader
# version 1.1.1 ~ 2022-08-06 ~ now refers to bdats as "bdat1" to be distinct from XC3's "bdat2"
# version 1.1.0 ~ 2022-07-15 ~ fixed off-by-one error in the output name of array params (e.g. was pc0 - pc15, fixed to pc1 - pc16)
# version 1.0.0 ~ 2021-11-21 ~ public release, expected to work on most BDATs for XC1, XCX, XC2, and XC1DE

import os
import struct
import sys

if len(sys.argv) < 2:
	quit("inFilename?")
inFilename = sys.argv[1]
outFilename = "./bdat1_outFile.txt"

game = ""
while game not in ["xc1","xcx","xc2","xc1de"]:
	game = input("game? (XC1, XCX, XC2, XC1DE) ").lower()

if game == "xc1" or game == "xcx":
	endian = "big"
else:
	endian = "little"

if endian == "big":
	u8Code = ">B"
	i8Code = ">b"
	u16Code = ">H"
	i16Code = ">h"
	u32Code = ">L"
	i32Code = ">l"
	fpCode = ">f"
elif endian == "little":
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
	encryptionFlag = f.read(2) # seems to be 0x0200 if encrypted, 0x0000 if not
	namesOffset = readAndParseInt(f,2)
	itemSize = readAndParseInt(f,2)
	hashTableOffset = readAndParseInt(f,2)
	hashTableLength = readAndParseInt(f,2)
	itemTableOffset = readAndParseInt(f,2)
	itemCount = readAndParseInt(f,2)
	baseID = readAndParseInt(f,2)
	unknown_14 = readAndParseInt(f,2)
	checksum = readAndParseInt(f,2)
	stringsOffset = readAndParseInt(f,4)
	stringsLength = readAndParseInt(f,4)
	
	if game == "xc1":
		memberTableOffset = 0x20
		# member count is not given - it must be figured out
		memberCount = (namesOffset-memberTableOffset)//4
	else:
		memberTableOffset = readAndParseInt(f,2)
		memberCount = readAndParseInt(f,2)
	
	f.seek(namesOffset)
	tableName = readStr(f)
	
	memberSize = 6
	
	memberNames = []
	memberPosList = []
	memberTypes = []
	valueTypes = []
	arrayCounts = []
	flagData = []
	
	if game == "xc1": # it's a lot easier to do this outside the main per-member loop below
		f.seek(namesOffset)
		for c in range(memberCount+1):
			memberNames.append(readStr(f))
			if f.tell() % 2 == 1:
				dummy = readAndParseInt(f,1)
			dummyIndex = readAndParseInt(f,2)
			dummyUnknown = readAndParseInt(f,2)
		del memberNames[0] # remove the table name itself from the front
	
	for c in range(memberCount):
		memberOffset = c * memberSize + memberTableOffset
		f.seek(memberOffset)
		
		if game == "xc1":
			infoOffset = memberTableOffset + (c * 4)
		else:
			infoOffset = readAndParseInt(f,2)
			f.seek(memberOffset+4)
		
		if game == "xc1":
			pass # memberNames has been set already
		elif game == "xc1de":
			nameOffset = memberOffset+4
			f.seek(nameOffset)
			f.seek(readAndParseInt(f,2))
			memberNames.append(readStr(f))
		else:
			nameOffset = readAndParseInt(f,2)
			f.seek(nameOffset)
			memberNames.append(readStr(f))
		
		f.seek(infoOffset)
		memberType = readAndParseInt(f,1)
		memberTypes.append(memberType)
		if memberType == 3: # flags
			valueTypes.append(-1)
			memberPosList.append(0)
			f.seek(infoOffset+1) # maybe not needed, but to be safe
			flagIndex = readAndParseInt(f,1)
			flagMask = readAndParseInt(f,4)
			flagVarOffset = readAndParseInt(f,2)
			flagVarIndex = (flagVarOffset-memberTableOffset)//memberSize
			flagData.append([flagVarIndex,flagMask])
		else: # not flags
			flagData.append([])
			f.seek(infoOffset+1) # maybe not needed, but to be safe
			valueType = readAndParseInt(f,1)
			valueTypes.append(valueType)
			memberPos = readAndParseInt(f,2)
			memberPosList.append(memberPos)
		if memberType == 2: # array
			f.seek(infoOffset+4)
			arrayCount = readAndParseInt(f,2)
			arrayCounts.append(arrayCount)
		else: # not array
			arrayCounts.append(1)
	
	with open(outFilename,"w",encoding="utf-8") as o:
		o.write(tableName+"\t"+"\t".join(memberNames)+"\n")
		o.write("\t"+"\t".join([str(x) for x in memberTypes])+"\n")
		o.write("\t"+"\t".join([valueTypeDict[x][0] for x in valueTypes])+"\n")
		o.write("\t"+"\t".join([str(x) for x in arrayCounts])+"\n")
		o.write("\t"+"\t".join([str(x) for x in flagData])+"\n")
		o.write("\t"+"\t".join([str(x) for x in memberPosList])+"\n")
		o.write("\n")
		
		unrolledMemberNames = []
		unrolledValueTypes = []
		for n in range(len(memberNames)):
			arrayCount = arrayCounts[n]
			if arrayCount == 1:
				unrolledMemberNames.append(memberNames[n])
				unrolledValueTypes.append(valueTypes[n])
			else:
				for ac in range(arrayCount):
					unrolledMemberNames.append(memberNames[n]+str(ac+1))
					unrolledValueTypes.append(valueTypes[n])
		o.write("ID\t"+"\t".join([str(x) for x in unrolledMemberNames])+"\n")
		o.write("\t"+"\t".join([valueTypeDict[x][0] for x in unrolledValueTypes])+"\n")
		
		# got the columns, now get each row's values
		f.seek(itemTableOffset)
		for i in range(itemCount):
			values = []
			for c in range(memberCount):
				itemIndex = i
				itemOffset = itemIndex * itemSize + itemTableOffset
				valueOffset = itemOffset + memberPosList[c]
				#print(itemSize,itemIndex,itemOffset,valueOffset)
				f.seek(valueOffset)
				if memberTypes[c] == 1 or memberTypes[c] == 2: # scalar, array
					arrayCount = arrayCounts[c]
					for a in range(arrayCount):
						valueType = valueTypes[c]
						if game == "xcx" and valueType == 8: # XCX floats are int32/4096
							values.append(struct.unpack(i32Code,f.read(struct.calcsize(i32Code)))[0]/4096.0)
						elif valueType == 7: #str
							f.seek(readAndParseInt(f,4))
							values.append(readValueStr(f))
						else:
							values.append(struct.unpack(valueTypeDict[valueType][1],f.read(struct.calcsize(valueTypeDict[valueType][1])))[0])
				elif memberTypes[c] == 3: # flags - some duplication is necessary, in case we can't guarantee that flags always come after their root
					flagRootIndex = flagData[c][0]
					flagVarOffset = itemOffset + memberPosList[flagRootIndex]
					f.seek(flagVarOffset)
					flagValueType = valueTypes[flagRootIndex]
					if flagValueType == 7 or flagValueType == 8: # non-int flag root types (bad)
						values.append("[f!]")
					else:
						flagRootValue = struct.unpack(valueTypeDict[flagValueType][1],f.read(struct.calcsize(valueTypeDict[flagValueType][1])))[0]
						flagMask = flagData[c][1]
						values.append((flagRootValue & flagMask) > 0)
				else: # unsupported/wrong data
					values.append("[~]")
			o.write(str(i+baseID)+"\t"+"\t".join([str(x) for x in values])+"\n")

#[EOF]