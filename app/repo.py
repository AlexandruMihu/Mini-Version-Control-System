import os
import sys
import os
import zlib
import hashlib
from urllib.parse import urlparse
import urllib.request
import struct
from typing import List, Tuple, Dict

from .objects import readObject
from .tree import renderTree

def init():
    os.mkdir(".git")
    os.mkdir(".git/objects")
    os.mkdir(".git/refs")
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")
    print("Initialized git directory")
    
def clone():
    remote = sys.argv[2]
    if len(sys.argv) == 4:
        local = sys.argv[3]
    else:
        parsed = urlparse(remote)
        local = parsed.path.split("/")[-1].replace(".git","")
        
    os.makedirs(local)
    os.makedirs(os.path.join(local,".git","objects"))
    os.makedirs(os.path.join(local,".git","refs"))
    
    print(f"Cloning {remote} to {local}")
    
    caps,refs = getRefs(remote)
    defaultBranch = caps.get("default_branch","refs/heads/main")
    
    defaultRefSha = None
    for sha,ref in refs:
        if ref == defaultBranch:
            defaultRefSha = sha
            break
        
    if defaultRefSha is None:
        raise RuntimeError(f"Default branch not found: {defaultBranch}")
    
    print(f"Downloading {defaultBranch} ({defaultRefSha})")
    packfile = downloadPackfile(remote, defaultRefSha)
    writePackfile(packfile,local)
    
    with open(os.path.join(local,".git","HEAD"),"w") as f:
        f.write(f"ref: {defaultBranch}\n")
    
    refDir = os.path.join(local,".git",os.path.dirname(defaultBranch))
    os.makedirs(refDir,exist_ok=True)
    with open(os.path.join(local,".git",defaultBranch),"w") as f:
        f.write(f"{defaultRefSha}\n")
    
    _, commitContent = readObject(local,defaultRefSha)
    treeSha = commitContent[5:45].decode()
    
    renderTree(local,local,treeSha)

def getRefs(url: str) -> Tuple[Dict[str, bool | str], List[Tuple[str, str]]]:
    
    url = f"{url}/info/refs?service=git-upload-pack"

    req = urllib.request.Request(url)
    refs, caps = [], {}
    with urllib.request.urlopen(req) as response:
        lines = response.read().split(b"\n")

    
    capBytes = lines[1].split(b"\x00")[1]
    for cap in capBytes.split(b" "):
        if cap.startswith(b"symref=HEAD:"):
            caps["default_branch"] = cap.split(b":")[1].decode()
        else:
            caps[cap.decode()] = True

    for line in lines[2:]:
        if line.startswith(b"0000"):
            break

        sha, ref_name = line.decode().split(
            " "
        ) 
        refs.append((sha[4:], ref_name))  
    return caps, refs

def downloadPackfile(url: str, want_ref: str) -> bytes:
    url = f"{url}/git-upload-pack"

    body = (
        b"0011command=fetch0001000fno-progress"
        + f"0032want {want_ref}\n".encode()
        + b"0009done\n0000"
    )

    headers = {
        "Content-Type": "application/x-git-upload-pack-request",
        "Git-Protocol": "version=2",
    }

    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req) as response:
        data = response.read()

    packLines = []

    while data:
        lineLen = int(data[:4], 16)
        if lineLen == 0:
            break
        packLines.append(data[4:lineLen])
        data = data[lineLen:]

    return b"".join(l[1:] for l in packLines[1:]) 

def writePackfile(data: bytes, targetDir: str) -> None:
    gitDir = os.path.join(targetDir, ".git")

    def nextSizeType(bs: bytes) -> Tuple[str, int, bytes]:
        ty = (bs[0] & 0b01110000) >> 4
        typeMap = {
            1: "commit",
            2: "tree",
            3: "blob",
            4: "tag",
            6: "ofs_delta",
            7: "ref_delta",
        }
        ty = typeMap.get(ty, "unknown")

        size = bs[0] & 0b00001111
        i = 1
        shift = 4
        while bs[i - 1] & 0b10000000:
            size |= (bs[i] & 0b01111111) << shift
            shift += 7
            i += 1
        return ty, size, bs[i:]

    def next_size(bs: bytes) -> Tuple[int, bytes]:
        size = bs[0] & 0b01111111
        i = 1
        shift = 7
        while bs[i - 1] & 0b10000000:
            size |= (bs[i] & 0b01111111) << shift
            shift += 7
            i += 1
        return size, bs[i:]

    data = data[8:]

    nObjects = struct.unpack("!I", data[:4])[0]
    data = data[4:]

    print(f"Processing {nObjects} objects")

    objects = []  
    remainingData = data

    for _ in range(nObjects):
        objType, _, remainingData = nextSizeType(remainingData)

        if objType in ["commit", "tree", "blob", "tag"]:
            decomp = zlib.decompressobj()
            content = decomp.decompress(remainingData)
            remainingData = decomp.unused_data
            objects.append((objType, content, None))

        elif objType == "ref_delta":
            baseSha = remainingData[:20].hex()
            remainingData = remainingData[20:]

            decomp = zlib.decompressobj()
            delta = decomp.decompress(remainingData)
            remainingData = decomp.unused_data

            objects.append(("ref_delta", delta, baseSha))

    
    processedObjects = set()  

    def processObject(obj_data: Tuple[str, bytes, str | None]) -> None:
        objType, content, baseSha = obj_data

        if objType != "ref_delta":
            
            store = f"{objType} {len(content)}\x00".encode() + content
            sha = hashlib.sha1(store).hexdigest()

            path = os.path.join(gitDir, "objects", sha[:2])
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, sha[2:]), "wb") as f:
                f.write(zlib.compress(store))

            processedObjects.add(sha)
            return sha

        else:
            if baseSha not in processedObjects:
                for obj in objects:
                    if (
                        obj[0] != "ref_delta"
                        and hashlib.sha1(
                            f"{obj[0]} {len(obj[1])}\x00".encode() + obj[1]
                        ).hexdigest()
                        == baseSha
                    ):
                        processObject(obj)
                        break

            with open(f"{gitDir}/objects/{baseSha[:2]}/{baseSha[2:]}", "rb") as f:
                baseContent = zlib.decompress(f.read())
            baseType = baseContent.split(b" ")[0].decode()
            baseContent = baseContent.split(b"\x00", 1)[1]

            delta = content
            _, delta = next_size(delta)  
            _, delta = next_size(delta)  

            result = b""
            while delta:
                cmd = delta[0]
                if cmd & 0b10000000:  
                    pos = 1
                    offset = 0
                    size = 0

                    for i in range(4):
                        if cmd & (1 << i):
                            offset |= delta[pos] << (i * 8)
                            pos += 1

                    for i in range(3):
                        if cmd & (1 << (4 + i)):
                            size |= delta[pos] << (i * 8)
                            pos += 1

                    result += baseContent[offset : offset + size]
                    delta = delta[pos:]
                else:  
                    size = cmd
                    result += delta[1 : size + 1]
                    delta = delta[size + 1 :]

            store = f"{baseType} {len(result)}\x00".encode() + result
            sha = hashlib.sha1(store).hexdigest()

            path = os.path.join(gitDir, "objects", sha[:2])
            os.makedirs(path, exist_ok=True)
            with open(os.path.join(path, sha[2:]), "wb") as f:
                f.write(zlib.compress(store))

            processedObjects.add(sha)
            return sha 
    for obj in objects:
        processObject(obj)
