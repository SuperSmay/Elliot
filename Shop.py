from typing import AsyncContextManager
import discord
from globalVariables import client, numberEmoteList
from Menu import menu
from activeMessages import activeMessages
import asyncio

class Shop:
    def __init__(self, message):
        self.message = message
        self.member = message.author
        self.guild = message.guild
        self.pageIndex = -1

    async def send(self):
        self.shopMessage = await self.message.reply(embed= self.getShopPageEmbed(), mention_author= False)
        await self.react()
        activeMessages[self.shopMessage.id] = self
        await self.close()

    async def close(self):  #This is run as a background task once the message is sent 
        await asyncio.sleep(300)  #Waiting for 300 seconds
        await self.shopMessage.edit(content="This message is now inactive")  #Edit the message
        del(activeMessages[self.shopMessage.id])  #Delete the message from the reaction dictionary

    async def edit(self):
        embed = self.getShopPageEmbed()
        await self.shopMessage.edit(embed= embed)
        self.shopMessage = await self.message.channel.fetch_message(self.shopMessage.id)

    async def onReact(self, emoji, member):
        if member.id != self.member.id or (str(emoji) not in numberEmoteList and str(emoji) != "<:back_arrow:866141339480752180>"):
            return
        if self.pageIndex == -1:
            self.pageIndex = self.getPageIndexFromEmoji(emoji)
            await self.edit()
            await self.react()
        else:
            self.buyItem()

    def buyItem(self):
        pass

    def getPageIndexFromEmoji(self, emoji):
        print(str(emoji))
        if str(emoji) == "<:back_arrow:866141339480752180>":
            return -1
        return numberEmoteList.index(str(emoji))

    def getShopPageEmbed(self):
        if self.pageIndex == -1:
            return self.mainPageEmbed()
        return self.menuPageEmbed()

    def mainPageEmbed(self):
        embed = discord.Embed(title= "Café Counter", description= "How can I help you?", color= 7528669)
        for item in menu:
            embed.add_field(name= f"{self.getEmojiNumber(menu.index(item))} {item['name']}", value= item["info"], inline= False)
        embed.add_field(name= "Coming soon...", value= "We're always adding new drinks!", inline= False)
        return embed

    def menuPageEmbed(self):
        embed = discord.Embed(title= menu[self.pageIndex]["pageName"], description= menu[self.pageIndex]["pageInfo"], color= 7528669)
        for item in menu[self.pageIndex]["items"]:
            embed.add_field(name= f"{self.getEmojiNumber(menu[self.pageIndex]['items'].index(item))} {item['emote']} - {item['name']} - ${item['price']}", value= item["info"], inline= False)
        embed.add_field(name= "Coming soon...", value= "New flavors coming soon", inline= False)
        return embed

    async def react(self):
        await self.shopMessage.clear_reactions()
        if self.pageIndex == -1:
            count = len(menu)
        else:
            print(self.pageIndex)
            count = len(menu[self.pageIndex]["items"])
            await self.shopMessage.add_reaction("<:back_arrow:866141339480752180>")
        for i in range(0, count):
            client.loop.create_task(self.shopMessage.add_reaction(self.getEmojiNumber(i)))

    def getEmojiNumber(self, index):
        return numberEmoteList[index]
