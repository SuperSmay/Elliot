import pathlib
import json
import asyncio

interactionFile = pathlib.Path('interactionCountDict')
interactionDict = json.load(open(interactionFile, 'r'))

async def saveLoop():
    while True:
        await asyncio.sleep(1800)
        save()    
    
def save():
    saveFile(interactionFile)
    print("Interaction file saved.")

def saveFile(file):
    open_file = open(file, 'w')
    json.dump(interactionDict, open_file)
    open_file.close()