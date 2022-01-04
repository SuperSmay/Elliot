import json
import pathlib
import os

master = {}
output = open(pathlib.Path('interactionCountDict'), 'w+')

for path in pathlib.Path('InteractionCount').iterdir():

    with open(path, "r") as file:
        master[os.path.basename(file.name)] = json.load(file)

json.dump(master, output)
output.close()