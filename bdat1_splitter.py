# coding=utf-8
import os
import struct
import sys

# Sir Teatei Moonlight's Xenoblade BDAT1 splitter
# version 1.0.1 ~ 2022-08-06 ~ now refers to bdats as "bdat1" to be distinct from XC3's "bdat2"
# version 1.0.0 ~ 2022-01-18 ~ public release, expected to work on most common/merged BDATs for XC1, XCX, XC2, and XC1DE

if len(sys.argv) < 3:
	quit("inFilename? outFolder?")
inFilename = sys.argv[1]
outFolder = sys.argv[2]

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
	bdatCount = struct.unpack(u32Code,f.read(4))[0]
	fileLength = struct.unpack(u32Code,f.read(4))[0]
	bdatOffsets = []
	for b in range(bdatCount):
		bdatOffsets.append(struct.unpack(u32Code,f.read(4))[0])
	bdatOffsets.append(fileLength)
	for b in range(bdatCount):
		#print("~~~")
		f.seek(bdatOffsets[b])
		# need to go through this song and dance to get to the table's name
		magicIgnore = f.read(4)
		dummyMaybe = f.read(2)
		nameLocation = struct.unpack(u16Code,f.read(struct.calcsize(u16Code)))[0]
		f.seek(bdatOffsets[b]+nameLocation)
		tableName = readStr(f)
		# got table name - bulk-write the whole thing, no logic
		f.seek(bdatOffsets[b])
		bdatSize = bdatOffsets[b+1]-bdatOffsets[b]
		with open(os.path.join(outFolder,tableName+".bdat"),"wb") as o:
			o.write(f.read(bdatSize))

#[EOF]