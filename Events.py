import inspect

downloadErrorCallbacks = {}
songPlayedCallbacks = {}
songEndCallbacks = {}
songSkipCallbacks = {}
songSkipCallbacks = {}
disconnectCallbacks = {}
pauseCallbacks = {}
unpauseCallbacks = {}
shuffleEnableCallbacks = {}
shuffleDisableCallbacks = {}
loadingCompleteCallbacks = {}

class Generic:
    def addCallback(guildID, callback, callbackDict):
        if not guildID in callbackDict.keys(): callbackDict[guildID] = []
        callbackDict[guildID].append(callback)
    def removeCallback(guildID, callback, callbackDict):
        if not guildID in callbackDict.keys(): return
        callbackDict[guildID].remove(callback)
    async def call(player, guildID, callbackDict, ctx=None):
        if not guildID in callbackDict.keys(): return
        for callback in callbackDict[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, ctx)   
                else: callback(player, ctx)

class DownloadError:
    def addCallback(guildID, callback):
        if not guildID in downloadErrorCallbacks.keys(): downloadErrorCallbacks[guildID] = []
        downloadErrorCallbacks[guildID].append(callback)
    def removeCallback(guildID, callback):
        if not guildID in downloadErrorCallbacks.keys(): return
        downloadErrorCallbacks[guildID].remove(callback)
    async def call(player, guildID, unloadedSong, ctx = None):
        if not guildID in downloadErrorCallbacks.keys(): return
        for callback in downloadErrorCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback, ctx): await callback(player, unloadedSong)   
                else: callback(player, unloadedSong, ctx)

class SongPlaybackStart:
    def addCallback(guildID, callback):
        if not guildID in songPlayedCallbacks.keys(): songPlayedCallbacks[guildID] = []
        songPlayedCallbacks[guildID].append(callback)
    def removeCallback(guildID, callback):
        if not guildID in songPlayedCallbacks.keys(): return
        songPlayedCallbacks[guildID].remove(callback)
    async def call(player, guildID, songPlayer):
        if not guildID in songPlayedCallbacks.keys(): return
        for callback in songPlayedCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, songPlayer)   
                else: callback(player, songPlayer)

class SongEnd:
    def addCallback(guildID, callback):
        if not guildID in songEndCallbacks.keys(): songEndCallbacks[guildID] = []
        songEndCallbacks[guildID].append(callback)
    def removeCallback(guildID, callback):
        if not guildID in songEndCallbacks.keys(): return
        songEndCallbacks[guildID].remove(callback)
    async def call(player, guildID, e):
        if not guildID in songEndCallbacks.keys(): return
        for callback in songEndCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, e)   
                else: callback(player, e)

class SongSkip:
    def addCallback(guildID, callback):
        if not guildID in songSkipCallbacks.keys(): songSkipCallbacks[guildID] = []
        songSkipCallbacks[guildID].append(callback)
    def removeCallback(guildID, callback):
        if not guildID in songSkipCallbacks.keys(): return
        songSkipCallbacks[guildID].remove(callback)
    async def call(player, guildID, oldPlayer, ctx=None):
        if not guildID in songSkipCallbacks.keys(): return
        for callback in songSkipCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, oldPlayer, ctx)   
                else: callback(player, oldPlayer, ctx)

class Disconnect:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, disconnectCallbacks)
    def removeCallback(guildID, callback):
        Generic.removeCallback(guildID, callback, disconnectCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, disconnectCallbacks, ctx)

class Pause:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, pauseCallbacks)
    def removeCallback(guildID, callback):
        Generic.removeCallback(guildID, callback, pauseCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, pauseCallbacks, ctx)

class Unpause:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, unpauseCallbacks)
    def removeCallback(guildID, callback):
        Generic.removeCallback(guildID, callback, unpauseCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, unpauseCallbacks, ctx)

class ShuffleEnable:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, shuffleEnableCallbacks)
    def removeCallback(guildID, callback):
        Generic.removeCallback(guildID, callback, shuffleEnableCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, shuffleEnableCallbacks, ctx)

class ShuffleDisable:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, shuffleDisableCallbacks)
    def removeCallback(guildID, callback):
        Generic.removeCallback(guildID, callback, shuffleDisableCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, shuffleDisableCallbacks, ctx)

class LoadingComplete:
    def addCallback(guildID, callback):
        if not guildID in loadingCompleteCallbacks.keys(): loadingCompleteCallbacks[guildID] = []
        loadingCompleteCallbacks[guildID].append(callback)
    def removeCallback(guildID, callback):
        if not guildID in loadingCompleteCallbacks.keys(): return
        loadingCompleteCallbacks[guildID].remove(callback)
    async def call(player, guildID, count, title, playThisNext=False, ctx=None):
        if not guildID in loadingCompleteCallbacks.keys(): return
        for callback in loadingCompleteCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, count, playThisNext=playThisNext, title=title, ctx=ctx)
                else: callback(player, count, playThisNext=playThisNext, title=title, ctx=ctx)