from typing import AsyncContextManager
import discord
from discord import embeds
from globalVariables import client, numberEmoteList, prefix
from Menu import menu
from activeMessages import activeMessages
import asyncio
import json
import pathlib
import datetime

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
        if member.id != self.member.id or (str(emoji) not in numberEmoteList and str(emoji) != "<:back_arrow:866161586157649951>"):
            return
        if self.pageIndex == -1 or self.getPageIndexFromEmoji(emoji) == -1:
            self.pageIndex = self.getPageIndexFromEmoji(emoji)
            await self.edit()
            await self.react()
        else:
            itemToBuy = menu[self.pageIndex]['items'][self.getPageIndexFromEmoji(emoji)]
            interaction = ShopInteraction(self.message, itemToBuy)
            await self.message.reply(content= interaction.buyItem(), mention_author= False) 

    def getPageIndexFromEmoji(self, emoji):
        if str(emoji) == "<:back_arrow:866161586157649951>":
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
            count = len(menu[self.pageIndex]["items"])
            await self.shopMessage.add_reaction("<:back_arrow:866161586157649951>")
        for i in range(0, count):
            client.loop.create_task(self.shopMessage.add_reaction(self.getEmojiNumber(i)))

    def getEmojiNumber(self, index):
        return numberEmoteList[index]

class ShopInteraction:

    def __init__(self, message, item):
        self.message = message
        self.member = message.author
        self.guild = message.guild
        self.inventory = self.getInventory()
        self.item = item

    def buyItem(self):
        if self.userCanAfford():
            self.chargeUser()
            self.addItemToInventory()
            self.saveInventory()
            return self.itemBoughtMessage()
        else:
            return self.priceErrorMessage()

    def priceErrorMessage(self):
        return f"Sorry, you only have ${self.inventory['balance']}, but you need ${self.item['price']} to buy that."

    def addItemToInventory(self):
        self.inventory["items"].append(self.item)

    def userCanAfford(self):
        return self.inventory["balance"] >= self.item["price"]

    def getInventory(self):
        path = pathlib.Path(f"Inventory/{self.guild.id}/{self.member.id}")
        if pathlib.Path.exists(path):
            file = open(path, "r")
            inventory = json.load(file)
            file.close()
        else:
            inventory = {"balance" : 0, "items" : []}
            folderPath = pathlib.Path(f"Inventory/{self.guild.id}")
            if not folderPath.exists():
                folderPath.mkdir()
            file = open(path, "w+")
            json.dump(inventory, file)
            file.close()
        return inventory

    def saveInventory(self):
        path = pathlib.Path(f"Inventory/{self.guild.id}/{self.member.id}")
        if pathlib.Path.exists(path):
            file = open(path, "w")
            json.dump(self.inventory, file)
            file.close()
        else:
            inventory = {"balance" : 0, "items" : []}
            path.mkdir()
            file = open(path, "w+")
            json.dump(inventory, file)
            file.close()

    def chargeUser(self):
        self.inventory["balance"] = self.inventory["balance"] - self.item["price"]

    def generateReceipt(self):
        return f"```-------Thank you for your purchase-------\n\nPurchase: {self.item['name']} --     -- ${self.item['price']}\n------------------------------------\nCashier: @{client.user.name}   Date: {datetime.datetime.now().strftime('%m/%d/%y')}```"

    def itemBoughtMessage(self):
        return f"Successfully bought item! Here is your receipt:\n{self.generateReceipt()}"
        
class Inventory:

    def __init__(self, message):
        self.message = message
        self.member = message.author
        self.guild = message.guild
        self.inventory = self.getInventory()

    def getInventory(self):
        path = pathlib.Path(f"Inventory/{self.guild.id}/{self.member.id}")
        if pathlib.Path.exists(path):
            file = open(path, "r")
            inventory = json.load(file)
            file.close()
        else:
            inventory = {"balance" : 0, "items" : []}
            folderPath = pathlib.Path(f"Inventory/{self.guild.id}")
            if not folderPath.exists():
                folderPath.mkdir()
            file = open(path, "w+")
            json.dump(inventory, file)
            file.close()
        return inventory
    
    def inventoryEmbed(self):
        embed = discord.Embed(title= f"{self.member.display_name}'s inventory", description= self.inventoryList(), color= 7528669)
        embed.set_footer(text= f"Buy more items with `{prefix} shop`")
        return embed

    def inventoryList(self):
        inventory = []
        for item in self.inventory["items"]:
            inventory.append(f"**{item['emote']} - {item['name']}**")
        return "\n".join(inventory)

    async def send(self):
        await self.message.reply(embed= self.inventoryEmbed(), mention_author= False)

class Balance:
    def __init__(self, message):
        self.message = message
        self.member = message.author
        self.guild = message.guild
        self.inventory = self.getInventory()

    def getInventory(self):
        path = pathlib.Path(f"Inventory/{self.guild.id}/{self.member.id}")
        if pathlib.Path.exists(path):
            file = open(path, "r")
            inventory = json.load(file)
            file.close()
        else:
            inventory = {"balance" : 0, "items" : []}
            folderPath = pathlib.Path(f"Inventory/{self.guild.id}")
            if not folderPath.exists():
                folderPath.mkdir()
            file = open(path, "w+")
            json.dump(inventory, file)
            file.close()
        return inventory

    def balanceEmbed(self):
        embed = discord.Embed(title= f"{self.member.display_name}'s balance", description= f"${self.inventory['balance']}", color= 7528669)
        embed.set_footer(text= "Earn more money by talking! (Doesn't work yet!)")
        return embed

    async def send(self):
        await self.message.reply(embed= self.balanceEmbed(), mention_author= False)