import os
import zlib
from hashlib import sha1
from urllib.parse import urlparse
from typing import Tuple

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
        
def readObject(path: str, sha: str) -> Tuple[str, bytes]:
    with open(f"{path}/.git/objects/{sha[:2]}/{sha[2:]}", "rb") as f:
        data = zlib.decompress(f.read())

    nullPos = data.index(b"\x00")
    header = data[:nullPos]
    content = data[nullPos + 1 :]

    objType = header.split(b" ")[0].decode()
    return objType, content
