# coding=utf-8
import os
import struct
import sys

# Sir Teatei Moonlight's Xenoblade BDAT2 splitter
# version 1.0.0 ~ 2022-08-06 ~ public release, expected to work on most common/merged BDATs for XC3

if len(sys.argv) < 3:
	quit("inFilename? outFolder?")
inFilename = sys.argv[1]
outFolder = sys.argv[2]

game = "xc3"
#while game not in ["xc3"]:
#	game = input("game? (XC3) ").lower()

# only XC1 and XCX seem to be big-endian so far (everything since is little), so don't need to check that

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
		with open(os.path.join(outFolder,os.path.splitext(os.path.basename(inFilename))[0]+"_"+str(b+1)+".bdat"),"wb") as o:
			o.write(f.read(bdatSize))

#[EOF]