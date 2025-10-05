import os, time, zlib, hashlib

def commitTree(arguments):
    treeHash =  arguments[2]
    if "-p" in arguments:
        pIndex = arguments.index("-p")
        parentHash = arguments[pIndex + 1]
    if "-m" in arguments:
        mIndex = arguments.index("-m")
        message = arguments[mIndex + 1]
    author = "Alexandru Mihu <address@gmail.com>"
    timeStamp = int(time.time())
    timeZone = time.strftime("%z")
    
    authorTime = f"{author} {timeStamp} {timeZone}" 
    
    commitContent = f"tree {treeHash}\nparent {parentHash}\nauthor {authorTime}\ncommiter {authorTime}\n\n{message}\n"  
    commitContentBytes = commitContent.encode("utf-8")
    
    header = f"commit {len(commitContentBytes)}\x00".encode("utf-8")
    hashObject = hashlib.sha1()
    storedData = header + commitContentBytes
    hashObject.update(storedData)
    sha1Hash = hashObject.hexdigest()
    compressedData = zlib.compress(storedData)
    dirPath = f".git/objects/{sha1Hash[:2]}"
    if not os.path.exists(dirPath):
        os.mkdir(dirPath)
        with open(f"{dirPath}/{sha1Hash[2:]}","wb") as objFile:
            objFile.write(compressedData)
    print(sha1Hash)