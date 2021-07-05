from discord import message
import Interactions
import discord
from globalVariables import client
from fnmatch import fnmatch

# def interactionCommand(message):
#     messageItems = message.content.split(" ")
#     authorName = message.author.name
#     otherNames = []
#     includedMessage = []
#     if len(messageItems) < 3:
#         type = "solo"
#     else:
#         type = "multi"
#         for item in messageItems[2:]:
#             if fnmatch(item, "<@*>"):  #If item is a plain ping
#                 id = item.replace("<", "").replace(">", "").replace("@", "").replace("!", "")  #Remove everything except the id
#                 if id in [user.id for user in message.guild.users]:
#                     try: 
#                         user = client.fetch_user(id)
#                         if user != None:
#                             otherNames.append(user.name)
#                     except:
#                         pass
#             if otherNames == []:
#                 message.channel.send(f"I couldn't find user `{messageItems[3]}`")
#                 return
#     interaction = messageItems[2]
    

    
