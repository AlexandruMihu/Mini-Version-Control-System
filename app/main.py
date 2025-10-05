import sys
from .commit import commitTree
from .repo import init,clone
from .objects import catFile,hashObject
from .tree import lsTree,writeTree
   
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
        print(writeTree("."))  
    elif command == "commit-tree":
        treeHash = sys.argv[2]
        parentHash = sys.argv[4] if "-p" in sys.argv else None
        message = sys.argv[6] if "-m" in sys.argv else "No message"
        print(commitTree(treeHash, parentHash, message))
    elif command == "clone":
        clone()
    else:
        raise RuntimeError(f"Unknown command #{command}")

if __name__ == "__main__":
    main()
