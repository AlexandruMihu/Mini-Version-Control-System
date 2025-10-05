import sys
import os
import zlib
from hashlib import sha1

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
    object_hash = is_name_only if arguments[2] else arguments[3]
    
    filepath = f"./git/objects/{object_hash[:2]}/{object_hash[2:]}"
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
        content = content[endOfEntry]
    entries.sort()
    for entry in entries:
        print(entry)
          
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
    else:
        raise RuntimeError(f"Unknown command #{command}")

if __name__ == "__main__":
    main()
