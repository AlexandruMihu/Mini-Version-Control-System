import os
import zlib
import hashlib
from hashlib import sha1
from urllib.parse import urlparse
from .objects import readObject
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
        dirPath = f".git/objects/{hash_value[:2]}"
        os.makedirs(dirPath, exist_ok=True)
        with open(f"{dirPath}/{hash_value[2:]}", "wb") as f:
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

def renderTree(repoPath: str, dirPath: str, sha: str):
    print(f"Rendering tree {sha} to {dirPath}")
    os.makedirs(dirPath, exist_ok=True)
    _, treeContent = readObject(repoPath, sha)

    
    while treeContent:
        
        mode, treeContent = treeContent.split(b" ", 1)
        
        name, treeContent = treeContent.split(b"\x00", 1)
        
        entrySha = treeContent[:20].hex()
        treeContent = treeContent[20:]

        entryPath = os.path.join(dirPath, name.decode())

        if mode == b"40000":  
            renderTree(repoPath, entryPath, entrySha)
        elif mode == b"100644":  
            _, content = readObject(repoPath, entrySha)
            with open(entryPath, "wb") as f:
                f.write(content)
        else:
            raise RuntimeError(f"Unsupported mode: {mode}")