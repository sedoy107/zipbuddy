'''
ZipBuddy
Sergey Gorbov / sedoy51289@gmail.com
'''

import argparse
import os, sys
import struct

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class ZipFormatError(Exception):
    pass

class ZipBuddyError(Exception):
    pass

    

class CentralDirRecord:
    '''
    Handles creation of the Central Directory Record located at the end of a
    properly fomed Zip file. The only health check performed here is the magic check
    '''

    FORMAT = "=4sHHHHIIH"
    BASE_SIZE = 22 # Should match with struct.calcsize(CentralDirRecord.FORMAT)
    MAGIC = b'PK\x05\x06'

    def __init__(self, buf):

        self.signature, \
        self.diskNum, \
        self.startDiskNum, \
        self.entriesOnDisk, \
        self.entriesInDir, \
        self.dirSize, \
        self.dirOfft, \
        self.commentLen = struct.unpack(CentralDirRecord.FORMAT, buf)
    
    def isGood(self):
        return self.signature == CentralDirRecord.MAGIC

    def print(self):
        print("End of Central Directory Record:")
        print(self.signature)
        print(self.diskNum)
        print(self.startDiskNum)
        print(self.entriesOnDisk)
        print(self.entriesInDir)
        print(self.dirSize)
        print(self.dirOfft)
        print(self.commentLen)
        

class DirFileHeader:
    '''
    Handles creation of the Central Directory File Records
    '''

    FORMAT = "=4sHHHHHHIIIHHHHHII"
    BASE_SIZE = 46 # Should match with struct.calcsize(DirFileHeader.FORMAT)
    MAGIC = b'PK\x01\x02'
    
    
    def __init__(self, buf):

        self.signature, \
        self.verMadeBy, \
        self.verNeeded, \
        self.flags, \
        self.compType, \
        self.modTime, \
        self.modDate, \
        self.crc32, \
        self.compSize, \
        self.uncompSize, \
        self.fnLen, \
        self.extraLen, \
        self.commLen, \
        self.diskNumStart, \
        self.intAttr, \
        self.extAttr, \
        self.locHdrOfft = struct.unpack(DirFileHeader.FORMAT, buf[:DirFileHeader.BASE_SIZE])
        
        s = DirFileHeader.BASE_SIZE
        e = DirFileHeader.BASE_SIZE + self.fnLen
        
        self.fileName = struct.unpack(f"{self.fnLen}s", buf[s:e])
        s = e
        e += self.extraLen
        self.extra = struct.unpack(f"{self.extraLen}s", buf[s:e])
        s = e
        e += self.commLen
        self.comment = struct.unpack(f"{self.commLen}s", buf[s:e])
        
        self.end = e
    
    def isGood(self):
        return self.signature == DirFileHeader.MAGIC

    def getTimestamp(self):

        def padZero(v):
            if (v < 10):
                return f"0{v}"
            else:
                return f"{v}"

        t = self.modTime
        hour = padZero((t & 0xf800) >> 11)
        minute = padZero((t & 0x07e0) >> 5)
        second = padZero((t & 0x001f) << 1)

        d = self.modDate
        year = 1980 + ((d & 0xfe00) >> 9)
        month = padZero((d & 0x01e0) >> 5)
        day = padZero(d & 0x001f)

        

        return f"{year}-{month}-{day}T{hour}:{minute}:{second}"

    def getFileName(self):
        return self.fileName[0].decode('ascii')

    def isDir(self):
        return self.extAttr & 0x20 > 0

    def getComment(self):
        return self.comment[0].decode('ascii')

    def getUncompSize(self):
        return self.uncompSize

    def getCompSize(self):
        return self.compSize
            
    def print(self):
        print("File Header Entry:")
        print(self.signature)
        print(self.verMadeBy)
        print(self.verNeeded)
        print(self.flags)
        print(self.compType)
        print(self.modTime)
        print(self.modDate)
        print(self.crc32)
        print(self.compSize)
        print(self.uncompSize)
        print(self.fnLen)
        print(self.extraLen)
        print(self.commLen)
        print(self.diskNumStart)
        print(self.intAttr)
        print(self.extAttr)
        print(self.locHdrOfft)
        print(self.fileName)
        print(self.extra)
        print(self.comment)
        
    


class ZipInfo:
    '''
    Handles parsing of a zip file and provides raw data to the user.
    All the Zip sanity checks and raising parsing errors should be handled in this class.
    '''
    
    def __init__(self, path):
        self.path = os.path.normpath(path)
        
        '''
        The ctor will fail if the file cannot be opened and the error will be propagated 
        to the callee
        '''
        self.fd = open(self.path, 'rb')
        self.size = (os.stat(self.path)).st_size
        
        '''
        The ctor will fail if there is any Zip Format errors encountered.
        '''
        self.cdr = None
        self.fileRecords = []
        self.__parseCentralDir()
        self.__parseFileHeaders()
            
    def __del__(self):
        if (self.fd):
            self.fd.close()
            
    def __parseCentralDir(self):
        '''
        Two cases possible here:
        1. The zip file has no comment, then we just read 22 bytes from the end and struct unpack them.
        2. There is a comment at the end. In this case we need to slide-window up the file byte-by-byte until we 
        hit the magic value for the End of Central Directory Record.
        '''

        MAX_COMMENT_SIZE = 0xffff # 65535
        RECORD_MIN_SIZE = 22
        RECORD_MAX_SIZE = RECORD_MIN_SIZE + MAX_COMMENT_SIZE
        commentLen = 0

        if (self.size < RECORD_MIN_SIZE):
            raise ZipFormatError(f"The size of the file is too small")

        while(True):
            cdrOfft = self.size - (RECORD_MIN_SIZE + commentLen)
            self.fd.seek(cdrOfft, 0)
            readPos = self.fd.tell()
            buf = self.fd.read(RECORD_MIN_SIZE)
            self.cdr = CentralDirRecord(buf)

            if (self.cdr.isGood()):
                break

            commentLen += 1

            if (commentLen == MAX_COMMENT_SIZE or cdrOfft == 0):
                raise ZipFormatError(f"Central Directory Record magic value not found")


       
        
        
            
    def __parseFileHeaders(self):
        '''
        This method will fail with ZipBuddyError if the Central Record is not
        properly initialized or if any of the central directory entries' magic value
        does match the expected value.
        '''

        if (self.cdr is None):
            raise ZipBuddyError("End of Central Directory Record is not initialized")
            
        self.fd.seek(self.cdr.dirOfft, 0)
        readPos = self.fd.tell()
        buf = self.fd.read(self.cdr.dirSize)
        start = 0
        while(start < self.cdr.dirSize):
            fRec = DirFileHeader(buf[start:])
            if (not fRec.isGood()):
                raise ZipFormatError(f"Directory File Record magic value mismatch at offset: {readPos + start}")
            self.fileRecords.append(fRec)
            start += fRec.end
    
    def getFileDescriptor(self):
        self.fd.seek(0,0) # set to the beginning of the file prior to returning to the user
        return self.fd

    def getCentralDirRecord(self):
        return self.cdr

    def getDirFileRecords(self):
        return self.fileRecords