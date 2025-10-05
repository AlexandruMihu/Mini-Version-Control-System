import sys
import os
import zlib
from hashlib import sha1

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

   # Uncomment this block to pass the first stage
    
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
        
    elif command == "cat-file" and sys.argv[2] == "-p":
        hash = sys.argv[3]
        hashPath = f".git/objects/{hash[0:2]}/{hash[2:]}"
        with open(hashPath,"rb") as f:
            data = f.read()
            data = zlib.decompress(data)
            headerEnd = data.find(b"\x00")
            content = data[headerEnd + 1:].strip()
            print(content.decode("utf-8"),end="")
            
    elif command == "hash-object" and sys.argv[2] == "-w":
        if not sys.argv[2] == "-w":
            raise RuntimeError(f"Unexpected flag #{sys.argv[2]}")
        
        with open(sys.argv[3],"rb") as f:
            contents = f.read()
            
        header = f"blob {len(contents)}\x00".encode("utf-8")
        hash = sha1(header+contents).hexdigest()
        print(hash)
        dname, fname = hash[:2], hash[2:]
        dname = os.path.join(".git/objects",dname)
        os.mkdir(dname)
        with open(os.path.join(dname,fname),"wb") as f:
            f.write(zlib.compress(header + contents))
            
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
