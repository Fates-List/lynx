var wsUp = false
var ws = null
var startingWs = false;
var wsFatal = false
var wsContentResp = new Set([])
var wsContentSpecial = new Set([])

const log = (...args) => {
    if(args[0] == "error" || args[0] == "warn") {
        try {
            wsSend({"request": "spld", "e": "T", "data": args}, true)
        } catch(e) {
            error("StarClan", e)
        }
    }

    console[args[0]](`%c[WORKER ${Date.now()}]%c[${args[1]}]%c`, "color:red;font-weight:bold;", "color:purple;font-weight:bold;", "", ...args.slice(2))
}

// Custom logger for our worker
["log", "debug", "info", "warn", "error"].forEach((method) => {
    self[method] = function(...args) {
        args.unshift(method)
        log(...args)
    }
})

importScripts('https://cdn.jsdelivr.net/npm/@msgpack/msgpack@2.7.2/dist.es5+umd/msgpack.min.js', 'https://cdn.jsdelivr.net/npm/pako@1.0.10/dist/pako.min.js')

onmessage = function (event) {
    if(event.data == "restart") {
        restartWs()
    } else if(event.data == "start") {
        wsStart()
    } else if(event.data == "setup") {
        startSetup()
    } else {
        wsSend(event.data, lazy=event.data.lazy || false)
    }
}

async function wsSend(data, lazy = false) {
    if(!wsUp) {
        info("Nightheart", "Waiting for ws to come up to start sending messages")
        if(!lazy) {
            wsStart()
        }
        return
    }

    if(ws.readyState === ws.OPEN) {
        ws.send(pako.deflate(MessagePack.encode(data)))
    } else {
        if(!lazy) {
            restartWs()
        }
    }
}

function restartWs() {
    // Restarts websocket properly
    if(wsFatal) {
        return
    }
    info("Nightheart", "WS is not open, restarting ws")
    wsUp = false
    startingWs = false
    postMessage("down")
    wsStart()
    return
}

async function wsStart() {
    // Starts a websocket connection
    if(startingWs) {
        error("Nightheart", "Not starting WS when already starting or critically aborted")
        return
    }

    postMessage("Starting websocket...")
    postMessage("starting")

    startingWs = true

    // Select the client
    let cliExt = Date.now()

    function getNonce() {
        // Protect against simple regexes with this
        return ("Co" + "nf".repeat(0) + "mf".repeat(1) + "r".repeat(0)) + "r" + "0".repeat(0) + "e".repeat(1) + "y" + "t".repeat(0) + "".repeat(2) + "0" + "s".repeat(1) + (1 + 1 + 0 + 1 + 0 + 0 + 1 + 1 + 0 + -1 + 2 + 1)
    }    
    
    ws = new WebSocket(`wss://lynx.fateslist.xyz/_ws?cli=${getNonce()}@${cliExt}&plat=WEB`)
    ws.binaryType = "arraybuffer";
    ws.onopen = function (event) {
        info("Nightheart", "WS connection opened. Started promise to send initial handshake")
        if(ws.readyState === ws.CONNECTING) {
            info("Nightheart", "Still connecting not sending")
            return
        }

        wsUp = true
        postMessage("up")
    }

    ws.onclose = function (event) {
        if(event.code == 4008) {
            // Token error
            error("Nightheart", "Token/Client error, requesting a login")
            wsUp = true;
            startingWs = true;
            wsFatal = true;
            postMessage("Invalid token/client, login again using Login button in sidebar or refreshing your page")
            return
        }

        postMessage("Websocket unexpectedly closed, likely server maintenance")
        error("Nightheart", "WS closed due to an error", { event })
        wsUp = false
        startingWs = false
        return
    }

    ws.onerror = function (event) {
        postMessage("Websocket unexpectedly closed, likely server maintenance")
        error("Nightheart", "WS closed (errored) due to an error", { event })
        wsUp = false
        startingWs = false
        return
    }

    ws.onmessage = async function (event) {
        debug("Nightheart", "Got new response over ws, am decoding: ", { event })
        let pakoData = pako.inflate(event.data)
        debug("Nightheart", "Decoded data: ", { pakoData })
        var data = MessagePack.decode(pakoData)
        debug("Nightheart", "Got new WS message: ", { data })
        postMessage(data)
    }      
}

async function startSetup() {
    if(!wsUp) {
        info("Nightheart", "Waiting for ws to come up to start setup")
        wsStart()
        return
    }

    if(ws.readyState !== ws.OPEN) {
        if(wsFatal) {
            return
        }
        info("Nightheart", "WS is not open, restarting ws")
        wsUp = false
        startingWs = false
        wsStart()
        return
    }
}