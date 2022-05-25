'''
In this modue the user is free to implement additional functionality either through
inheritance of ZipIno or by instantiating ZipInfo and then using its members for 
whatever puroposes...
'''


from os import sep
from zipbuddy import ZipInfo
import argparse

class ZipView():
    '''
    This class will leverage ZipInfo to access the Zip file metadata.
    '''

    def __init__(self, zipInfo):
        self.zi = zipInfo

    def formatField(self, val, maxLen, units=""):
        v = f"{val}{units}"
        l = len(v)
        if (l < maxLen):
            return f"{v}{' ' * (maxLen - l)}"
        elif (l > maxLen):
            return f"{v[:maxLen - 3]}..."

    def ls(self):
        fileRecList = self.zi.getDirFileRecords()

        fileNameLen = 40
        isDirLen = 12
        uncompSizeLen = 15
        timestampLen = 20
        commentLen = 40

        hdrFileName = self.formatField("File Name", fileNameLen)
        hdrIsDir = self.formatField("Directory", isDirLen)
        hdrUncompSize = self.formatField("Uncomp Size", uncompSizeLen)
        hdrTimestamp = self.formatField("Timestamp", timestampLen)
        hdrComment = self.formatField("Comment", commentLen)
        hdr = f"{hdrFileName} {hdrIsDir} {hdrUncompSize} {hdrTimestamp} {hdrComment}"
        sep = "-" * (fileNameLen + isDirLen + uncompSizeLen + timestampLen + commentLen)

        print(hdr)
        print(sep)

        for fr in fileRecList:
            fileName = self.formatField(fr.getFileName(), fileNameLen)
            isDir = self.formatField(fr.isDir(), isDirLen)
            uncompSize = self.formatField(fr.getUncompSize(), uncompSizeLen, 'B')
            timestamp = self.formatField(fr.getTimestamp(), timestampLen)
            comment = self.formatField(fr.getComment(), commentLen)
            m = f"{fileName} {isDir} {uncompSize} {timestamp} {comment}"
            print(m)



if (__name__ == "__main__"):
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_file", metavar="zip_file", type=str, nargs=1, help="Path to a zip file")
    #parser.add_argument("-e", "--extract", action="store_true", default=False, help="extract zip content")
    #parser.add_argument("-p", "--password", type=str, default=None, help="password string")
    args = parser.parse_args()
    
    zi = ZipInfo(args.zip_file[0])
    zv = ZipView(zi)

    zv.ls()
