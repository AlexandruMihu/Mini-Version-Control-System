import os, time, zlib, hashlib

def commitTree(treeHash, parentHash, message, author="You <you@example.com>"):
    timeStamp = int(time.time())
    timeZone = time.strftime("%z")
    authorTime = f"{author} {timeStamp} {timeZone}"

    commitContent = (
        f"tree {treeHash}\n"
        + (f"parent {parentHash}\n" if parentHash else "")
        + f"author {authorTime}\n"
        + f"committer {authorTime}\n\n"
        + f"{message}\n"
    )

    commitBytes = commitContent.encode("utf-8")
    header = f"commit {len(commitBytes)}\x00".encode("utf-8")
    storedData = header + commitBytes

    sha1Hash = hashlib.sha1(storedData).hexdigest()
    compressedData = zlib.compress(storedData)

    dirPath = f".git/objects/{sha1Hash[:2]}"
    os.makedirs(dirPath, exist_ok=True)
    with open(f"{dirPath}/{sha1Hash[2:]}", "wb") as objFile:
        objFile.write(compressedData)

    return sha1Hash
