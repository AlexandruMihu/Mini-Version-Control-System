import sys
import os
import zlib
import hashlib
from hashlib import sha1
import time 

def init():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")

def catFile(hash):
    hashPath = f".git/objects/{hash[0:2]}/{hash[2:]}"
    with open(hashPath,"rb") as f:
        data = f.read()
        data = zlib.decompress(data)
        headerEnd = data.find(b"\x00")
        content = data[headerEnd + 1:].strip()
        print(content.decode("utf-8"),end="")
  
def hashObject(filepath):
    with open(filepath,"rb") as f:
        data = f.read()
        
    header = f"blob {len(data)}\x00".encode("utf-8")
    hash = sha1(header+data).hexdigest()
    print(hash)
    dname, fname = hash[:2], hash[2:]
    dname = os.path.join(".git/objects",dname)
    os.mkdir(dname)
    with open(os.path.join(dname,fname),"wb") as f:
        f.write(zlib.compress(header + data))  

def lsTree(arguments):
    is_name_only = "--name-only" in arguments
    if is_name_only:
        object_hash = arguments[3]
    else:
        object_hash = arguments[2]
        
    filepath = f".git/objects/{object_hash[:2]}/{object_hash[2:]}"
    with open(filepath,"rb") as f:
        data  = f.read() 
        data = zlib.decompress(data)  
        header_end = data.index(b"\x00")
        content = data[header_end+1:]
        
    entries = []
    while content:
        spaceIndex = content.index(b" ")
        nullIndex = content.index(b"\x00", spaceIndex)
        
        nameBytes = content[spaceIndex+1:nullIndex]
        name = nameBytes.decode("utf-8")
        
        if is_name_only:
            entries.append(name)
        else:
            mode = content[:spaceIndex].decode("utf-8")
            typeMode = "tree" if mode == "40000" else "blob" if mode == "100644" else "" 
            binaryHash = content[nullIndex +1:nullIndex+21]
            sha = binaryHash.hex()
            row = f"{mode} {typeMode} {sha}\t{name}"
            entries.append(row)
        endOfEntry = nullIndex + 21
        content = content[endOfEntry:]
    entries.sort()
    for entry in entries:
        print(entry)
        
def hashObjectFile(filepath):
    try:
        with open(filepath, "rb") as f:
            contents = f.read()
        blob_data = b"blob " + str(len(contents)).encode("ascii") + b"\0" + contents
        hash_value = hashlib.sha1(blob_data).hexdigest()
        compressed = zlib.compress(blob_data)
        dir_path = f".git/objects/{hash_value[:2]}"
        os.makedirs(dir_path, exist_ok=True)
        with open(f"{dir_path}/{hash_value[2:]}", "wb") as f:
            f.write(compressed)
        return hash_value
    except FileNotFoundError:
        return None
    
def writeTree(directory="."):
    treeEntries = []
    entries = []
    
    for entry in os.listdir(directory):
        if entry == ".git":
            continue
        entryPath = os.path.join(directory,entry)
        entries.append((entry,entryPath))
    
    entries.sort(key=lambda x:x[0])
    
    for entryName, entryPath in entries:
        if os.path.isfile(entryPath):
            blobHash = hashObjectFile(entryPath)
            if blobHash:
                mode = "100644"
                treeEntries.append((mode,entryName,blobHash))
        elif os.path.isdir(entryPath):
            subtreeHash = writeTree(entryPath)
            mode = "40000"
            treeEntries.append((mode,entryName,subtreeHash))
            
    treeContent = b""
    for mode, name,sha1Hex in treeEntries:
        treeContent += mode.encode("ascii") + b" " + name.encode("utf-8") + b"\0"
        sha1Binary = bytes.fromhex(sha1Hex)
        treeContent += sha1Binary
    
    treeData = b"tree " + str(len(treeContent)).encode("ascii")+b"\0"+treeContent
    treeHash = hashlib.sha1(treeData).hexdigest()
    compressed = zlib.compress(treeData)
    dirPath = f".git/objects/{treeHash[:2]}"
    os.makedirs(dirPath,exist_ok=True)
    with open(f"{dirPath}/{treeHash[2:]}","wb") as f:
        f.write(compressed)
    return treeHash

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
    
def main():
    command = sys.argv[1]
    if command == "init":
        init()  
    elif command == "cat-file":
        if sys.argv[2] != "-p":
            raise RuntimeError(f"Unexpected flag #{sys.argv[2]}")
        catFile(sys.argv[3])            
    elif command == "hash-object":
        if not sys.argv[2] == "-w":
            raise RuntimeError(f"Unexpected flag #{sys.argv[2]}")
        hashObject(sys.argv[3]) 
    elif command == "ls-tree":
         lsTree(sys.argv) 
    elif command == "write-tree":
        tree_hash = writeTree(".")
        print(tree_hash)  
    elif command == "commit-tree":
        commitTree = writeTree(sys.argv)
        print(commitTree)
    else:
        raise RuntimeError(f"Unknown command #{command}")

if __name__ == "__main__":
    main()
