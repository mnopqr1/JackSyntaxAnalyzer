from compilationengine import CompilationEngine
import sys
import os


def treatfile(fpath):
    engine = CompilationEngine(fpath)
    engine.compile_class()
    print("XML file written for " + fpath)

thepath = sys.argv[1]
if os.path.isfile(thepath):
    treatfile(thepath)
else:
    for fpath in os.listdir(thepath + "/"):
        if fpath[-5:] == ".jack":
            treatfile("./" + thepath + "/" + fpath)
