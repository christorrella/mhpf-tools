# Melbourne House Pack File packer/repacker by Chris Torrella

import sys, getopt, os, errno, math, re, struct, json, contextlib


############################################################
# UN-packing functions
############################################################

                      # "section name": (start byte, size)
headerLocations =   {
                        "magic":                        (0, 4),     # should always be 'MHPF', confirms filetype
                        "version":                      (4, 4),     # unconfirmed; might be "version" of the file, or "version" of the packing program
                        "total_size":                   (8, 4),     # size of entire .pck in bytes
                        "num_res":                      (12, 4),    # number of game resource files contained in this .pck
                        "pack_index":                   (16, 4),    # unconfirmed; might be the number of the .pck in the system, i.e. two different pack files for the same game will never have the same index
                        "res_addr_table_loc":           (20, 4),    #
                        "res_addr_table_size":          (24, 4),
                        "res_content_table_loc":        (28, 4),
                        "res_content_table_size":       (32, 4),
                        "res_dest_str_lens_table_loc":  (36, 4),
                        "res_dest_str_lens_table_size": (40, 4),
                        "res_dest_str_table_loc":       (44, 4),
                        "res_dest_str_table_size":      (48, 4)
                    }

header = {} # stores information about header after it's read from the file
resourceInfo = {} # contains resource file information: "filename":(start, size)

resource_content_locations = []
resource_dest_lengths = []
resource_dest_strings = []



def littleBytesToInt(bytes):
    return int.from_bytes(bytes, "little", signed=False)



def readHeader(): # reads the first 52 bytes of the file, gives locations of tables
    for key in headerLocations:
        start, size = headerLocations.get(key)
        fi.seek(start)
        if key == "magic": # only case where this data isn't an int, it's a string
            header[key] = fi.read(size).decode("utf-8")
        else:
            header[key] = littleBytesToInt(fi.read(size))

def printHeaderInfo():
  for key in header.keys():
      print(key + ": " + str(header.get(key)))

def readTables():

    # create resource contents address table

    start_offset = header.get("res_addr_table_loc")
    size = header.get("res_addr_table_size")
    fi.seek(start_offset, 0)
    for i in range(start_offset, start_offset+size, 12):
        resource_content_locations.append({"unknown":littleBytesToInt(fi.read(4)), "start":littleBytesToInt(fi.read(4)), "size":littleBytesToInt(fi.read(4))})

    # create resource filename string offsets table

    start_offset = header.get("res_dest_str_lens_table_loc")
    size = header.get("res_dest_str_lens_table_size")
    fi.seek(start_offset,0)
    for i in range(start_offset, start_offset+size, 4):
        resource_dest_lengths.append(littleBytesToInt(fi.read(4)))

    # create resource filename strings table

    start_offset = header.get("res_dest_str_table_loc")
    end_offset = header.get("res_dest_str_table_size")
    fi.seek(start_offset,0)
    for offset in resource_dest_lengths:
        name = ""
        fi.seek(start_offset + offset, 0)
        while(fi.read(1) != b'\x00'):
            fi.seek(-1,1)
            name += fi.read(1).decode("ascii")
        resource_dest_strings.append(name)

    # print(resource_dest_strings)

def printUnknownIDsForEachResource():
    for i in range(0, len(resource_dest_strings)):
        # print(str(resource_content_locations[i]) + ", " + resource_dest_strings[i])
        print(str(resource_content_locations[i].get("unknown")) + ": \"" + resource_dest_strings[i] + "\"," )

def printTable1():
    for i in range(0, len(resource_dest_strings)):
        # print(str(resource_content_locations[i]) + ", " + resource_dest_strings[i])
        print(str(resource_content_locations[i].get("unknown")) + ", " + str(resource_content_locations[i].get("start")) + ", " + str(resource_content_locations[i].get("size")) + ", \"" + resource_dest_strings[i] + "\"," )


def mkdir(path):
 with contextlib.suppress(OSError):
        os.makedirs(path)

def safe_open_w(path):
    ''' Open "path" for writing, creating any parent directories as needed.
    '''
    mkdir(os.path.dirname(path))
    return open(path, 'wb')

def unpack():
    for i in range(0, len(resource_content_locations)):
        print("(" + str(math.ceil((i/len(resource_content_locations)) * 100)) + "%) Unpacking " + resource_dest_strings[i])
        extractFile(resource_dest_strings[i], resource_content_locations[i].get("start"), resource_content_locations[i].get("size"))


def extractFile(destination, start, size):
    fo = safe_open_w(outputfile + destination)

    fi.seek(start, 0)

    for i in range(start, start+size):
        fo.write(fi.read(1))

def findFirstFile():
    smallestLoc = resource_content_locations[0].get("start")
    smallestLocDest = resource_dest_strings[0]
    for i in range(0, len(resource_content_locations)):
        if resource_content_locations[i].get("start") < smallestLoc:
            smallestLoc = resource_content_locations[i].get("start")
            smallestLocDest = resource_dest_strings[i]

    print(str(smallestLoc) + ", " + smallestLocDest)

def findChunkSizes():
    locations = []

    #pull starts
    for location in resource_content_locations:
        locations.append(location.get("start"))

    #sort starts ascending
    locations.sort()

    differences = []

    for i in range(0, len(locations) - 1):
        differences.append((locations[i+1] - locations[i]) / 1024)

    differences.sort()

    print(differences)

############################################################
# RE-packing functions
############################################################

global fileIDs

fileIDs = {}
with open("fileids.json", "r") as config:
    fileIDs = json.load(config)

# this contains the filelist but without the first dir and without sys files
fileInfo = []
contentOffsets = []

headerInfo =   {
                        "magic":                        "MHPF",     # should always be 'MHPF', confirms filetype
                        "version":                      1,     # unconfirmed; might be "version" of the file, or "version" of the packing program
                        "total_size":                   0,     # size of entire .pck in bytes
                        "num_res":                      0,    # number of game resource files contained in this .pck
                        "pack_index":                   0,    # unconfirmed; might be the number of the .pck in the system, i.e. two different pack files for the same game will never have the same index
                        "res_addr_table_loc":           0,    #
                        "res_addr_table_size":          0,
                        "res_content_table_loc":        0,
                        "res_content_table_size":       0,
                        "res_dest_str_lens_table_loc":  0,
                        "res_dest_str_lens_table_size": 0,
                        "res_dest_str_table_loc":       0,
                        "res_dest_str_table_size":      0
                    }

def getFileInfo(): # we store all the file names in this list
    filelist = []

    for root, dirs, files in os.walk(inputfile):
    	for file in files:
            #append the file name to the list
    		filelist.append(os.path.join(root,file))

    # remove filesystem stuff we don't need and the containing directory

    for file in filelist:
        if not re.search("DS_Store", file):
            fileInfo.append((file.replace(inputfile, "").replace("\\", "/"), os.path.getsize(file)))

def calculateHeaderValues():

    headerInfo["num_res"] = len(fileInfo)
    headerInfo["pack_index"] = 31 # no idea what this means; keep it what we already know it can be?

    headerInfo["res_addr_table_loc"] = 2048 # haven't seen anything different; keep fixed
    headerInfo["res_addr_table_size"] = 12 * headerInfo["num_res"] # 1 line * 3 cells per line * 4 bytes per cell * number of resources

    headerInfo["res_content_table_loc"] = 59392 #keep this fixed; no idea if we can change it
    headerInfo["res_content_table_size"] = getSizeOfContent()

    headerInfo["res_dest_str_lens_table_loc"] = headerInfo["res_content_table_loc"] + headerInfo["res_content_table_size"] # "dest string lengths table" comes right after file contents table
    headerInfo["res_dest_str_lens_table_size"] = len(fileInfo) * 4 # 4 bytes * number of destinations

    headerInfo["res_dest_str_table_loc"] = headerInfo["res_dest_str_lens_table_loc"] + headerInfo["res_dest_str_lens_table_size"] #"dest string" table comes right after prev table
    headerInfo["res_dest_str_table_size"] = getSizeOfConcatDests()

    headerInfo["total_size"] = headerInfo["res_dest_str_table_loc"] + headerInfo["res_dest_str_table_size"]

def getSizeOfContent():
    total = 0
    for file in fileInfo:
        dest, size = file
        # each chunk is at least 2 kibibytes in size
        size = (math.ceil(size / 2048) * 2) * 1024
        total += size
    # print(total)
    return total

def getSizeOfConcatDests():
    total = 0
    for file in fileInfo:
        dest,size = file
        total += len(dest)
    # add in nullbytes
    total += len(fileInfo)
    return total

def writeHeader():

    # order matters when writing the header (obviosuly) but I wanted to have these as key:values, so that's why this method is uuugly.

    fo.write(bytes(headerInfo.get("magic"), 'ascii'))
    fo.write(intToLittleEndianBytes(headerInfo.get("version")))

    fo.write(intToLittleEndianBytes(headerInfo.get("total_size")))
    fo.write(intToLittleEndianBytes(headerInfo.get("num_res")))

    fo.write(intToLittleEndianBytes(headerInfo.get("pack_index")))

    fo.write(intToLittleEndianBytes(headerInfo.get("res_addr_table_loc")))
    fo.write(intToLittleEndianBytes(headerInfo.get("res_addr_table_size")))

    fo.write(intToLittleEndianBytes(headerInfo.get("res_content_table_loc")))
    fo.write(intToLittleEndianBytes(headerInfo.get("res_content_table_size")))

    fo.write(intToLittleEndianBytes(headerInfo.get("res_dest_str_lens_table_loc")))
    fo.write(intToLittleEndianBytes(headerInfo.get("res_dest_str_lens_table_size")))

    fo.write(intToLittleEndianBytes(headerInfo.get("res_dest_str_table_loc")))
    fo.write(intToLittleEndianBytes(headerInfo.get("res_dest_str_table_size")))

def sortLists():

    #we need to sort: fileInfo based on FileIDs


    sortedFileInfo = []
    global IDs
    global fileIDs
    IDs = []

    #convert fileIDs keys back to ints from json
    fileIDs = {int(k):str(v) for k,v in fileIDs.items()}

    while (len(fileIDs) != 0):
        smallestID = min(fileIDs.keys())
        IDs.append(smallestID)
        destOfSmallestID = fileIDs[smallestID]
        #print("smallest found is " + str(smallestID) + " for " + destOfSmallestID)
        #print(fileInfo)
        for item in fileInfo:
            dest, size = item
            if destOfSmallestID == dest:
                sortedFileInfo.append(item)
                fileIDs.pop(smallestID)


    for i in range(0, len(sortedFileInfo)):
        fileInfo[i] = sortedFileInfo[i]


    #print(sortedFileInfo)



def writeResAddrTable():

    fo.seek(headerInfo.get("res_addr_table_loc")) #should be 2048, until we decide not to hard-code this

    ptr = headerInfo.get("res_content_table_loc")

    for i in range(0, len(fileInfo)):
        dest, size = fileInfo[i]

        chunkSizeNeededInBytes = (math.ceil(size / 2048) * 2) * 1024 # evenly fits into a multiple of 2 kebibytes

        #print(IDs)
        fo.write(intToLittleEndianBytes(IDs[i])) # have no idea what this is supposed to respresent; random for now?

        fo.write(intToLittleEndianBytes(ptr)) # the starting index of the resource

        contentOffsets.append(ptr)
        #increment ptr for next loop
        ptr += chunkSizeNeededInBytes
        fo.write(intToLittleEndianBytes(size)) #size of the resource


def writeDestStrLenghtsTable():
    fo.seek(headerInfo.get("res_dest_str_lens_table_loc"))

    prev = 0

    for dest, size in fileInfo:

        fo.write(intToLittleEndianBytes(prev))
        prev += len(dest) + 1

def writeDestStrTable():
    fo.seek(headerInfo.get("res_dest_str_table_loc"))

    for dest, size in fileInfo:
        fo.write(bytes(dest, 'ascii'))
        fo.write(b'\x00')

def writeResourceToTable():

    for i in range(0, len(fileInfo)):

        dest, size = fileInfo[i]
        start = contentOffsets[i]

        print("(" + str(math.ceil((i/len(fileInfo)) * 100)) + "%) Packing " + dest + " at " + str(start) + " for " + str(size) + " with ID " + str(IDs[i]))

        fi = open(inputfile + dest, "rb")

        fo.seek(start)

        for j in range(0,size):
            fo.write(fi.read(1))

        fi.close()

def intToLittleEndianBytes(num):
    return struct.pack('<I', num)

############################################################
# flow/control stuff
############################################################

def packMode():

    global fo
    fo = open(outputfile, "wb")
    getFileInfo()
    calculateHeaderValues()
    sortLists()

    if scanmode:
        print("scan mode doesn't do much for packing files at the moment")
    else:
        writeHeader()
        writeResAddrTable()
        writeResourceToTable()
        writeDestStrLenghtsTable()
        writeDestStrTable()
    fo.close()

def unpackMode():
    global fi
    fi = open(inputfile, "rb")
    readHeader()
    readTables()

    if scanmode:
        printHeaderInfo()
        #findFirstFile()
        #findChunkSizes()
        #printUnknownIDsForEachResource()
        printTable1()
    else:
        unpack()
    fi.close()

def main(argv):
    global inputfile
    global outputfile
    global scanmode

    inputfile = ''
    outputfile = ''

    scanmode = False
    packOpt = False
    unpackOpt = False

    try:
        opts, args = getopt.getopt(argv,"shupi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('mhpf-tools.py -u/-p/-s (--unpack/--pack/--scan) -i (--input) <input file/dir> -o (--output) <output file/dir>')
        print('"unpack" mode takes .pck file as input, creates output directory')
        print('"pack" mode takes directory as input, creates output pack file')
        print('"scan" mode takes .pck file as input, prints information about given pack file')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('mhpf-tools.py -u/-p/-s (--unpack/--pack/--scan) -i (--input) <input file/dir> -o (--output) <output file/dir>')
            print('"unpack" mode takes .pck file as input, creates output directory')
            print('"pack" mode takes directory as input, creates output pack file')
            print('"scan" mode takes .pck file as input, prints information about given pack file')
            sys.exit()
        elif opt in ("-i", "--input"):
            inputfile = arg
        elif opt in ("-o", "--output"):
            outputfile = arg
        elif opt in ("-s", "--scan"):
            scanmode = True
        elif opt in ("-u", "--unpack"):
            unpackOpt = True
        elif opt in ("-p", "--pack"):
            packOpt = True

    if packOpt:
        packMode()
    elif unpackOpt:
        unpackMode()
    elif scanmode:
        unpackMode()

if __name__ == "__main__":
    main(sys.argv[1:])