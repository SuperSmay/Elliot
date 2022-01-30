import inspect

downloadErrorCallbacks = {}
songPlayedCallbacks = {}
songEndCallbacks = {}
songSkipCallbacks = {}
songSkipCallbacks = {}
disconnectCallbacks = {}
resetCallbacks = {}
pauseCallbacks = {}
unpauseCallbacks = {}
shuffleEnableCallbacks = {}
shuffleDisableCallbacks = {}
loadingCompleteCallbacks = {}

class Generic:
    def addCallback(guildID, callback, callbackDict):
        if not guildID in callbackDict.keys(): callbackDict[guildID] = []
        if callback not in callbackDict[guildID]: callbackDict[guildID].append(callback)
    def removeCallbacks(guildID, callbackDict):
        if not guildID in callbackDict.keys(): return
        callbackDict[guildID] = []
    async def call(player, guildID, callbackDict, ctx=None):
        if not guildID in callbackDict.keys(): return
        for callback in callbackDict[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, ctx)   
                else: callback(player, ctx)

class DownloadError:
    def addCallback(guildID, callback):
        if not guildID in downloadErrorCallbacks.keys(): downloadErrorCallbacks[guildID] = []
        if callback not in downloadErrorCallbacks[guildID]: downloadErrorCallbacks[guildID].append(callback)
    def removeCallbacks(guildID):
        if not guildID in downloadErrorCallbacks.keys(): return
        downloadErrorCallbacks[guildID] = []
    async def call(player, guildID, unloadedSong, e, ctx = None):
        if not guildID in downloadErrorCallbacks.keys(): return
        for callback in downloadErrorCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, unloadedSong, e, ctx)   
                else: callback(player, unloadedSong, e, ctx)

class SongPlaybackStart:
    def addCallback(guildID, callback):
        if not guildID in songPlayedCallbacks.keys(): songPlayedCallbacks[guildID] = []
        if callback not in songPlayedCallbacks[guildID]: songPlayedCallbacks[guildID].append(callback)
    def removeCallbacks(guildID):
        if not guildID in songPlayedCallbacks.keys(): return
        songPlayedCallbacks[guildID] = []
    async def call(player, guildID, songPlayer):
        if not guildID in songPlayedCallbacks.keys(): return
        for callback in songPlayedCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, songPlayer)   
                else: callback(player, songPlayer)

class SongEnd:
    def addCallback(guildID, callback):
        if not guildID in songEndCallbacks.keys(): songEndCallbacks[guildID] = []
        if callback not in songEndCallbacks[guildID]: songEndCallbacks[guildID].append(callback)
    def removeCallbacks(guildID):
        if not guildID in songEndCallbacks.keys(): return
        songEndCallbacks[guildID] = []
    async def call(player, guildID, e):
        if not guildID in songEndCallbacks.keys(): return
        for callback in songEndCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, e)   
                else: callback(player, e)

class SongSkip:
    def addCallback(guildID, callback):
        if not guildID in songSkipCallbacks.keys(): songSkipCallbacks[guildID] = []
        if callback not in songSkipCallbacks[guildID]: songSkipCallbacks[guildID].append(callback)
    def removeCallbacks(guildID):
        if not guildID in songSkipCallbacks.keys(): return
        songSkipCallbacks[guildID] = []
    async def call(player, guildID, oldPlayer, ctx=None):
        if not guildID in songSkipCallbacks.keys(): return
        for callback in songSkipCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, oldPlayer, ctx)   
                else: callback(player, oldPlayer, ctx)

class Disconnect:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, disconnectCallbacks)
    def removeCallbacks(guildID):
        Generic.removeCallbacks(guildID, disconnectCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, disconnectCallbacks, ctx)

class Reset:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, resetCallbacks)
    def removeCallbacks(guildID):
        Generic.removeCallbacks(guildID, resetCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, resetCallbacks, ctx)

class Pause:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, pauseCallbacks)
    def removeCallbacks(guildID):
        Generic.removeCallbacks(guildID, pauseCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, pauseCallbacks, ctx)

class Unpause:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, unpauseCallbacks)
    def removeCallbacks(guildID):
        Generic.removeCallbacks(guildID, unpauseCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, unpauseCallbacks, ctx)

class ShuffleEnable:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, shuffleEnableCallbacks)
    def removeCallbacks(guildID):
        Generic.removeCallbacks(guildID, shuffleEnableCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, shuffleEnableCallbacks, ctx)

class ShuffleDisable:
    def addCallback(guildID, callback):
        Generic.addCallback(guildID, callback, shuffleDisableCallbacks)
    def removeCallbacks(guildID):
        Generic.removeCallbacks(guildID, shuffleDisableCallbacks)
    async def call(player, guildID, ctx=None):
        await Generic.call(player, guildID, shuffleDisableCallbacks, ctx)

class LoadingComplete:
    def addCallback(guildID, callback):
        if not guildID in loadingCompleteCallbacks.keys(): loadingCompleteCallbacks[guildID] = []
        loadingCompleteCallbacks[guildID].append(callback)
    def removeCallbacks(guildID):
        if not guildID in loadingCompleteCallbacks.keys(): return
        loadingCompleteCallbacks[guildID] = []
    async def call(player, guildID, count, title, playThisNext=False, ctx=None):
        if not guildID in loadingCompleteCallbacks.keys(): return
        for callback in loadingCompleteCallbacks[guildID]:
            if callable(callback):
                if inspect.iscoroutinefunction(callback): await callback(player, count, playThisNext=playThisNext, title=title, ctx=ctx)
                else: callback(player, count, playThisNext=playThisNext, title=title, ctx=ctx)