// Minify using https://jscompress.com/ and ES2022

// Not a module, should never be loaded as one

const log = (...args) => {
    console[args[0]](`%c[${Date.now()}]%c[${args[1]}]%c`, "color:red;font-weight:bold;", "color:purple;font-weight:bold;", "", ...args.slice(2))
}

// Custom logger
["log", "debug", "info", "warn", "error"].forEach((method) => {
    window[method] = function(...args) {
        args.unshift(method)
        log(...args)
    }
})

// Module loader
modulesLoaded = []
modules = {}

function readyModule(name) {
    info("StarClan", `Module: ${name} has loaded successfully!`)
    modulesLoaded.push(name)
}

function loadModule(name, path, callback = () => {}) {
    if(modulesLoaded.includes(name)) return;
    modules[name] = path
    info("StarClan", `Loading module ${name} (path=${path})`)
    let script = document.createElement("script")
    script.src = path
    script.async = false
    document.body.appendChild(script)

    setInterval(function(){
        if(modulesLoaded.includes(name)) {
            callback()
            clearInterval(this)
        }
    })
}

// Load launcher
loadModule("launcher", "/_static/launcher.js?v=m1")
