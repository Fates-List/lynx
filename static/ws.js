// Base WS library handlling the websocket protocol

var wsUp = false
var startingWs = false;
var wsFatal = false
var wsContentResp = new Set([])
var wsContentSpecial = new Set([])

// Load in web worker
var _worker = new Worker("/_static/__ws_worker.js?v=1800251LUNA")
_worker.onmessage = function (event) {
    if(typeof event.data === "string" || event.data instanceof String) {
        if(event.data == "fatal") {
            wsFatal = true
        } else if(event.data == "starting") {
            startingWs = true
        } else if(event.data == "up") {
            wsUp = true
        } else if(event.data == "down") {
            wsUp = false
            startingWs = false
        } else {
            $("#ws-info").html(event.data)
        }
    } else {
        // Its then a ws message
        info("Nightheart", "Got ws message", event.data)
        f = actions[event.data.resp]
        if(f) {
            f(event.data)
        }
        if(wsContentResp.has(event.data.resp)) {
            info("Nightheart", `Got content response ${event.data.resp}`)   
            setData(event.data)
        } else if(wsContentSpecial.has(event.data.resp)) {
            info("Nightheart", `Got special content resp ${event.data.resp}`)
            alert("special-status-upd", "Status Update!", event.data.detail)
            if(event.data.resp == "bot_action" && event.data.guild_id) {
                // Now put the invite to the bot
                window.open(`https://discord.com/api/oauth2/authorize?client_id=${event.data.bot_id}&scope=bot&application.command&guild_id=${event.data.guild_id}`, "_blank")
                alert("invite-approve", "Almost there...", "Now invite bot to main server")
            }
        }
    }
}

async function wsSend(data, lazy = false) {
    data.lazy = lazy
    info("Sending {ws}")
    _worker.postMessage(data)
}

function restartWs() {
    _worker.postMessage("restart")
}

async function wsStart() {
    _worker.postMessage("start")
}

async function startSetup() {
    _worker.postMessage("setup")
}

readyModule("ws")