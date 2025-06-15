# coding=utf-8
import os
import struct
import sys

# Sir Teatei Moonlight's Xenoblade BDAT2 splitter
# version 1.0.0 ~ 2022-08-06 ~ public release, expected to work on most common/merged BDATs for XC3
# version 1.1.0 ~ 2025-06-15 ~ improved split filenames

if len(sys.argv) < 3:
	quit("inFilename? outFolder?")
inFilename = sys.argv[1]
outFolder = sys.argv[2]

game = "" # no known differences in format between XC3 and XCXDE, so we just skip this for now
#while game not in ["xc3","xcxde"]:
#	game = input("game? (XC3, XCXDE) ").lower()

# only XC1 and XCX seem to be big-endian so far (everything since is little), so don't need to check that

u8Code = "<B"
i8Code = "<b"
u16Code = "<H"
i16Code = "<h"
u32Code = "<L"
i32Code = "<l"
fpCode = "<f"

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

with open(inFilename,"rb") as f:
	fileMagic = f.read(4)
	typeMagic = f.read(2) # seems to be 0x0410 for containers, 0x0430 if not
	if fileMagic != b"BDAT" or typeMagic != b"\x04\x10":
		quit("not a BDAT container (fileMagic: {}) (typeMagic: {})".format(fileMagic, typeMagic))
	unknown1 = f.read(2)
	bdatCount = struct.unpack(u32Code,f.read(4))[0]
	fileLength = struct.unpack(u32Code,f.read(4))[0]
	bdatOffsets = []
	for b in range(bdatCount):
		bdatOffsets.append(struct.unpack(u32Code,f.read(4))[0])
	bdatOffsets.append(fileLength)
	for b in range(bdatCount):
		# bulk-write the whole thing, no logic
		# correct names not available, so name them numerically
		f.seek(bdatOffsets[b])
		bdatSize = bdatOffsets[b+1]-bdatOffsets[b]
		filename = os.path.join(outFolder,os.path.splitext(os.path.basename(inFilename))[0]+"_"+str(b+1))
		with open(filename+".bdat","wb") as o:
			o.write(f.read(bdatSize))
		# now open the file to get the table's (hashed) name
		tableName = ""
		with open(filename+".bdat","rb") as f2:
			# mostly copied from the bdat2 reader, though we can assume a bunch (e.g. assume it's a single file) so we skip that
			f2.seek(40)
			stringsOffset = readAndParseInt(f2,4)
			f2.seek(stringsOffset+1)
			tableName = "murmur32_"+format(readAndParseInt(f2,4),"#010X")[2:]
		os.rename(filename+".bdat",filename+"_"+tableName+".bdat")

#[EOF]