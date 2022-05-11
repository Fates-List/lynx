import pathlib
import sys
from base64 import b64decode
import io
import os
import textwrap
import asyncio
import datetime
import hashlib
import signal
import time
from http import HTTPStatus
from typing import Any, Union
import enum
import secrets
import string
import math

import asyncpg
import bleach
import discord
import orjson
import requests
from dateutil import parser
from pydantic import BaseModel
import enums

import aiohttp
import aioredis
import msgpack
import orjson
from discord import Embed
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse, ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import HTTPException
from piccolo.apps.user.tables import BaseUser
from piccolo.engine import engine_finder
from piccolo_admin.endpoints import create_admin
from starlette.concurrency import iterate_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.routing import Mount
from jinja2 import Environment, FileSystemLoader, select_autoescape
from colour import Color
from PIL import Image, ImageDraw, ImageFont
import staffapps
import zlib
from experiments import Experiments, exp_props

import inspect
import tables
import piccolo

_tables = []

tables_dict = vars(tables)

for obj in tables_dict.values():
    if obj == tables.Table:
        continue
    if inspect.isclass(obj) and isinstance(obj, piccolo.table.TableMetaclass):
        _tables.append(obj)

print(_tables)

debug = False

limited_view = ["reviews", "review_votes", "bot_packs", "vanity", "leave_of_absence", "user_vote_table",
                "lynx_surveys", "lynx_survey_responses"]

limited_view_api = tuple(map(lambda el: f"/_admin/api/tables/{el}", limited_view))


class SPLDEvent(enum.Enum):
    maint = "M"
    refresh_needed = "RN"
    missing_perms = "MP"
    out_of_date = "OD"
    unsupported = "U"
    verify_needed = "VN"
    ping = "P"
    telemetry = "T"
    not_found = "NF"

async def fetch_user(user_id: int):
    async with aiohttp.ClientSession() as sess:
        async with sess.get(f"http://localhost:1234/getch/{user_id}") as resp:
            if resp.status == 404:
                return {
                    "id": "",
                    "username": "Unknown User",
                    "avatar": "https://cdn.discordapp.com/embed/avatars/0.png",
                    "disc": "0000"
                }
            return await resp.json()

async def send_message(msg: dict):
    msg["channel_id"] = int(msg["channel_id"])
    msg["embed"] = msg["embed"].to_dict()
    if not msg.get("mention_roles"):
        msg["mention_roles"] = []
    async with aiohttp.ClientSession() as sess:
        async with sess.post(f"http://localhost:1234/messages", json=msg) as res:
            return res

docs_template = requests.get("https://api.fateslist.xyz/_docs_template").text

with open("api-docs/endpoints.md", "w") as f:
    f.write(docs_template)

enums_docs_template = requests.get("https://api.fateslist.xyz/_enum_docs_template").text

with open("api-docs/enums-ref.md", "w") as f:
    f.write(enums_docs_template)


# Experiment sanity check
exps_in_api = requests.get("https://api.fateslist.xyz/experiments").json()

exps_found = []

for user_exp in exps_in_api["user_experiments"]:
    try:
        e = Experiments(user_exp["value"])
    except:
        print(f"[Lynx] User experiment sanity check failure (not found in Lynx): {user_exp['name']} ({user_exp['value']})")
        sys.exit(0)
    exps_found.append(e)

for exp in list(Experiments):
    if exp not in exps_found:
        print(f"[Lynx] User experiment sanity check failure (not found in API): {exp.name} ({exp.value})")
        sys.exit(0)
    elif not exp_props.get(exp.name):
        print(f"[Lynx] User experiment sanity check failure (not found in exp_props): {exp.name} ({exp.value})")
        sys.exit(0)
# End of experiment sanity check


def get_token(length: int) -> str:
    secure_str = ""
    for _ in range(0, length):
        secure_str += secrets.choice(string.ascii_letters + string.digits)
    return secure_str


with open("/home/meow/FatesList/config/data/discord.json") as json:
    json = orjson.loads(json.read())
    bot_logs = json["channels"]["bot_logs"]
    main_server = json["servers"]["main"]
    staff_server = json["servers"]["staff"]
    access_granted_role = json["roles"]["staff_server_access_granted_role"]
    bot_developer = json["roles"]["bot_dev_role"]
    certified_developer = json["roles"]["certified_dev_role"]
    certified_bot = json["roles"]["certified_bots_role"]

with open("/home/meow/FatesList/config/data/secrets.json") as json:
    file = json.read()
    main_bot_token = orjson.loads(file)["token_main"]
    metro_key = orjson.loads(file)["metro_key"]

with open("/home/meow/FatesList/config/data/staff_roles.json") as json:
    staff_roles = orjson.loads(json.read())


async def add_role(server, member, role, reason):
    print(f"[LYNX] AddRole: {role = }, {member = }, {server = }, {reason = }")
    url = f"https://discord.com/api/v10/guilds/{server}/members/{member}/roles/{role}"
    async with aiohttp.ClientSession() as sess:
        async with sess.put(url, headers={
            "Authorization": f"Bot {main_bot_token}",
            "X-Audit-Log-Reason": f"[LYNX] {reason}"
        }) as resp:
            if resp.status == HTTPStatus.NO_CONTENT:
                return None
            return await resp.json()


async def del_role(server, member, role, reason):
    print(f"[LYNX] RemoveRole: {role = }, {member = }, {server = }, {reason = }")
    url = f"https://discord.com/api/v10/guilds/{server}/members/{member}/roles/{role}"
    async with aiohttp.ClientSession() as sess:
        async with sess.delete(url, headers={
            "Authorization": f"Bot {main_bot_token}",
            "X-Audit-Log-Reason": f"[LYNX] {reason}"
        }) as resp:
            if resp.status == HTTPStatus.NO_CONTENT:
                return None
            return await resp.json()


async def ban_user(server, member, reason):
    url = f"https://discord.com/api/v10/guilds/{server}/bans/{member}"
    async with aiohttp.ClientSession() as sess:
        async with sess.put(url, headers={
            "Authorization": f"Bot {main_bot_token}",
            "X-Audit-Log-Reason": f"[LYNX] Bot Banned: {reason[:14] + '...'}"
        }) as resp:
            if resp.status == HTTPStatus.NO_CONTENT:
                return None
            return await resp.json()


async def unban_user(server, member, reason):
    url = f"https://discord.com/api/v10/guilds/{server}/bans/{member}"
    async with aiohttp.ClientSession() as sess:
        async with sess.delete(url, headers={
            "Authorization": f"Bot {main_bot_token}",
            "X-Audit-Log-Reason": f"[LYNX] Bot Unbanned: {reason[:14] + '...'}"
        }) as resp:
            if resp.status == HTTPStatus.NO_CONTENT:
                return None
            return await resp.json()

def code_check(code: str, user_id: int):
    expected = hashlib.sha3_384()
    expected.update(
        f"Baypaw/Flamepaw/Sunbeam/Lightleap::{user_id}+Mew".encode()
    )
    expected = expected.hexdigest()
    if code != expected:
        print(f"[LYNX] CodeCheckMismatch {expected = }, {code = }")
        return False
    return True

class Unknown:
    username = "Unknown"

# Staff Permission Checks

class StaffMember(BaseModel):
    """Represents a staff member in Fates List"""
    name: str
    id: Union[str, int]
    perm: int
    staff_id: Union[str, int]

async def is_staff_unlocked(bot_id: int, user_id: int, redis: aioredis.Connection):
    return await redis.exists(f"fl_staff_access-{user_id}:{bot_id}")


async def is_staff(user_id: int, base_perm: int) -> Union[bool, int, StaffMember]:
    if user_id < 0:
        staff_perm = None
    else:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(f"http://localhost:1234/perms/{user_id}") as res:
                staff_perm = await res.json()
    if not staff_perm:
        staff_perm = {"fname": "Unknown", "id": "0", "staff_id": "0", "perm": 0}
    sm = StaffMember(name=staff_perm["fname"], id=staff_perm["id"], staff_id=staff_perm["staff_id"],
                     perm=staff_perm["perm"])  # Initially
    rc = sm.perm >= base_perm
    return rc, sm.perm, sm

with open("api-docs/staff-guide.md") as f:
    staff_guide_md = f.read()

admin = create_admin(
   _tables,
    allowed_hosts=["lynx.fateslist.xyz"],
    production=True,
    site_name="Lynx Admin"
)

async def auth_user_cookies(request: Request):
    if request.cookies.get("sunbeam-session:warriorcats"):
        request.scope["sunbeam_user"] = orjson.loads(b64decode(request.cookies.get("sunbeam-session:warriorcats")))
        check = await app.state.db.fetchval(
            "SELECT user_id FROM users WHERE user_id = $1 AND api_token = $2",
            int(request.scope["sunbeam_user"]["user"]["id"]),
            request.scope["sunbeam_user"]["token"]
        )
        if not check:
            print("Undoing login due to relogin requirement")
            del request.scope["sunbeam_user"]
            return

        _, _, member = await is_staff(int(request.scope["sunbeam_user"]["user"]["id"]), 2)

        request.state.member = member
    else:
        request.state.member = StaffMember(name="Unknown", id=0, perm=1, staff_id=0)

    if request.state.member.perm >= 2:
        staff_verify_code = await app.state.db.fetchval(
            "SELECT staff_verify_code FROM users WHERE user_id = $1",
            int(request.scope["sunbeam_user"]["user"]["id"])
        )

        request.state.is_verified = True

        if not staff_verify_code or not code_check(staff_verify_code, int(request.scope["sunbeam_user"]["user"]["id"])):
            request.state.is_verified = False


class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.url.path in ("/widgets", "/widgets"):
            return RedirectResponse("/widgets/docs")

        if request.url.path == "/_ws" or request.url.path.startswith("/widgets"):
            return await call_next(request)
        
        if (not request.headers.get("X-Lynx-Site") and request.url.path not in ("/_admin", "/_admin/")) and not request.url.path.endswith((".css", ".js", ".js.map")):
            return ORJSONResponse({"detail": "Not in lynx site"}, status_code=401)

        print("[LYNX] Admin request. Middleware started")

        await auth_user_cookies(request)

        if not request.scope.get("sunbeam_user"):
            return RedirectResponse(f"https://fateslist.xyz/frostpaw/herb?redirect={request.url}")

        member: StaffMember = request.state.member
        perm = member.perm

        # Before erroring, ensure they are perm of at least 2 and have no staff_verify_code set
        if member.perm < 2: 
            return RedirectResponse("/missing-perms?perm=2")
        elif not request.state.is_verified:
            return RedirectResponse("/staff-verify")

        # Perm check

        if request.url.path.startswith("/_admin/api"):
            if request.url.path == "/_admin/api/tables/" and perm < 5:
                return ORJSONResponse(limited_view)
            elif request.url.path == "/_admin/api/tables/users/ids/" and request.method == "GET":
                pass
            elif request.url.path in (
                    "/_admin/api/forms/", "/_admin/api/user/", "/_admin/api/openapi.json") or request.url.path.startswith(
                "/_admin/api/docs"):
                pass
            elif perm < 4:
                if request.url.path.startswith("/_admin/api/tables/vanity"):
                    if request.method != "GET":
                        return ORJSONResponse({"error": "You do not have permission to update vanity"}, status_code=403)

                elif request.url.path.startswith("/_admin/api/tables/bot_packs"):
                    if request.method != "GET":
                        return ORJSONResponse({"error": "You do not have permission to update bot packs"},
                                              status_code=403)

                elif request.url.path.startswith("/_admin/api/tables/leave_of_absence/") and request.method in (
                        "PATCH", "DELETE"):
                    ids = request.url.path.split("/")
                    loa_id = None
                    for id in ids:
                        if id.isdigit():
                            loa_id = int(id)
                            break
                    else:
                        return ORJSONResponse({"error": "Invalid leave of absence ID"}, status_code=403)

                    user_id = await app.state.db.fetchval("SELECT user_id::text FROM leave_of_absence WHERE id = $1",
                                                          loa_id)
                    if user_id != request.scope["sunbeam_user"]["user"]["id"]:
                        return ORJSONResponse({"error": "You do not have permission to update this leave of absence"},
                                              status_code=403)

                elif not request.url.path.startswith(limited_view_api):
                    return ORJSONResponse({"error": "You do not have permission to access this page"}, status_code=403)

        key = "rl:%s" % request.scope["sunbeam_user"]["user"]["id"]
        check = await app.state.redis.get(key)
        if not check:
            rl = await app.state.redis.set(key, "0", ex=30)
        if request.method != "GET":
            rl = await app.state.redis.incr(key)
            if int(rl) > 10:
                expire = await app.state.redis.ttl(key)
                await app.state.db.execute("UPDATE users SET api_token = $1 WHERE user_id = $2", get_token(128),
                                           int(request.scope["sunbeam_user"]["user"]["id"]))
                return ORJSONResponse({"detail": f"[LYNX] RatelimitError: {expire=}; API_TOKEN_RESET"},
                                      status_code=429)

        if request.url.path.startswith("/meta"):
            return ORJSONResponse({"piccolo_admin_version": "0.1a1", "site_name": "Lynx Admin"})

        request.state.user_id = int(request.scope["sunbeam_user"]["user"]["id"])

        response = await call_next(request)

        await app.state.db.execute(
            "INSERT INTO lynx_logs (user_id, method, url, status_code) VALUES ($1, $2, $3, $4)",
            int(request.scope["sunbeam_user"]["user"]["id"]),
            request.method,
            str(request.url),
            response.status_code
        )

        if not response.status_code < 400:
            return response

        try:
            print(request.user.user.username)
        except:
            request.scope["user"] = Unknown()

        if request.url.path.startswith("/_admin/api/tables/leave_of_absence") and request.method == "POST":
            response_body = [section async for section in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            content = response_body[0]
            content_dict = orjson.loads(content)
            await app.state.db.execute("UPDATE leave_of_absence SET user_id = $1 WHERE id = $2",
                                       int(request.scope["sunbeam_user"]["user"]["id"]), content_dict[0]["id"])
            return ORJSONResponse(content_dict)

        if request.url.path.startswith("/_admin/api/tables/bots") and request.method == "PATCH":
            print("Got bot edit, sending message")
            path = request.url.path.rstrip("/")
            bot_id = int(path.split("/")[-1])
            print("Got bot id: ", bot_id)
            owner = await app.state.db.fetchval("SELECT owner FROM bot_owner WHERE bot_id = $1", bot_id)
            embed = Embed(
                title="Bot Edited Via Lynx",
                description=f"Bot <@{bot_id}> has been edited via Lynx by user {request.user.user.username}",
                color=0x00ff00,
                url=f"https://fateslist.xyz/bot/{bot_id}"
            )
            await send_message({"content": f"<@{owner}>", "embed": embed, "channel_id": bot_logs})

        return response

async def server_error(request, exc):
    return HTMLResponse(content="Error", status_code=exc.status_code)


app = FastAPI(routes=[
    Mount("/_admin", admin),
],
    title="Lynx Widgets API",
    description="This is the public widgets API for Fates List",
    docs_url=None,
    redoc_url="/widgets/docs",
    openapi_url="/widgets/docs/openapi",
    terms_of_service="https://fateslist.xyz/frostpaw/tos",
    license_info={
        "name": "MIT",
        "url": "https://github.com/Fates-List/FatesList/blob/main/LICENSE",
    },
    default_response_class=ORJSONResponse,
)

def bot_select(id: str, bot_list: list[str], reason: bool = False):
    select = f"""
<label for='{id}'>Choose a bot</label><br/>
<select name='{id}' {id=}> 
<option value="" disabled selected>Select your option</option>
    """

    for bot in bot_list:
        select += f"""
<option value="{bot['bot_id']}">{bot['username_cached'] or 'No cached username'} ({bot['bot_id']})</option>
        """

    select += "</select><br/>"

    # Add a input for bot id instead of select
    select += f"""
<div class="form-group">
<label for="{id}-alt">Or enter a Bot ID</label><br/>
<input class="form-control" type="number" id="{id}-alt" name="{id}-alt" placeholder="Bot ID..."/>
</div>
<br/>
    """

    if reason:
        select += f"""
<div class="form-group">
<label for="{id}-reason">Reason</label><br/>
<textarea 
    class="form-control"
    type="text" 
    id="{id}-reason" 
    name="{id}-reason"
    placeholder="Enter reason and feedback for improvement here"
></textarea>
</div>
<br/>
        """

    return select

class ActionWithReason(BaseModel):
    bot_id: str
    owners: list[dict] | None = None  # This is filled in by action decorator
    main_owner: int | None = None  # This is filled in by action decorator
    context: Any | None = None
    reason: str


app.state.bot_actions = {}


def action(
        name: str,
        states: list[enums.BotState],
        min_perm: int = 2,
        action_log: enums.UserBotAction | None = None
):
    async def state_check(bot_id: int):
        bot_state = await app.state.db.fetchval("SELECT state FROM bots WHERE bot_id = $1", bot_id)
        return (bot_state in states) or len(states) == 0

    async def _core(ws: WebSocket, data: ActionWithReason):
        if ws.state.member.perm < min_perm:
            return {
                "detail": f"PermError: {min_perm=}, {ws.state.member.perm=}"
            }

        if not data.bot_id.isdigit():
            return {
                "detail": "Bot ID is invalid"
            }

        data.bot_id = int(data.bot_id)

        if not await state_check(data.bot_id):
            return {
                "detail": replace_if_web(f"Bot state check error: {states=}", ws)
            }

        data.owners = await app.state.db.fetch("SELECT owner, main FROM bot_owner WHERE bot_id = $1", data.bot_id)

        for owner in data.owners:
            if owner["main"]:
                data.main_owner = owner["owner"]
                break
    
    def decorator(function):
        async def wrapper(ws: WebSocket, data: ActionWithReason):
            if _data := await _core(ws, data):
                return _data # Already sent ws message, ignore
            if len(data.reason) < 5:
                return {
                    "detail": "Reason must be more than 5 characters"
                }

            ws.state.user_id = int(ws.state.user["id"])

            res = await function(ws, data)  # Fake Websocket as Request for now TODO: Make this not fake
            
            err = res.get("err", False)
            
            if action_log and not err:
                await app.state.db.execute("INSERT INTO user_bot_logs (user_id, bot_id, action, context) VALUES ($1, $2, $3, $4)", ws.state.user_id, data.bot_id, action_log.value, data.reason)

            res = jsonable_encoder(res)
            res["resp"] = "bot_action"

            if not err:
                # Tell client that a refresh is needed as a bot action has taken place
                await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/bot-actions"})
            return res

        app.state.bot_actions[name] = wrapper
        return wrapper

    return decorator


@action("claim", [enums.BotState.pending], action_log=enums.UserBotAction.claim)
async def claim(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3",
                               enums.BotState.under_review, request.state.user_id, int(data.bot_id))

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0x00ff00,
        title="Bot Claimed",
        description=f"<@{request.state.user_id}> has claimed <@{data.bot_id}> and this bot is now under review.\n**If all goes well, this bot should be approved (or denied) soon!**\n\nThank you for using Fates List :heart:",
    )

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})
    return {"detail": "Successfully claimed bot!"}


@action("unclaim", [enums.BotState.under_review], action_log=enums.UserBotAction.unclaim)
async def unclaim(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1 WHERE bot_id = $2", enums.BotState.pending, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0x00ff00,
        title="Bot Unclaimed",
        description=f"<@{request.state.user_id}> has stopped testing <@{data.bot_id}> for now and this bot is now pending review from another bot reviewer.\n**This is perfectly normal. All bot reviewers need breaks too! If all goes well, this bot should be approved (or denied) soon!**\n\nThank you for using Fates List :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})
    return {"detail": "Successfully unclaimed bot"}


@action("approve", [enums.BotState.under_review], action_log=enums.UserBotAction.approve)
async def approve(request: Request, data: ActionWithReason):
    # Get approximate guild count
    async with aiohttp.ClientSession() as sess:
        async with sess.get(f"https://japi.rest/discord/v1/application/{data.bot_id}") as resp:
            if resp.status != 200:
                return ORJSONResponse({
                    "detail": f"Bot does not exist or japi.rest is down. Got status code {resp.status}"
                }, status_code=400)
            japi = await resp.json()
            approx_guild_count = japi["data"]["bot"]["approximate_guild_count"]

    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2, guild_count = $3 WHERE bot_id = $4",
                               enums.BotState.approved, request.state.user_id, approx_guild_count, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0x00ff00,
        title="Bot Approved!",
        description=f"<@{request.state.user_id}> has approved <@{data.bot_id}>\nCongratulations on your accompishment and thank you for using Fates List :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)
    embed.add_field(name="Guild Count (approx)", value=str(approx_guild_count))

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    for owner in data.owners:
        asyncio.create_task(add_role(main_server, owner["owner"], bot_developer, "Bot Approved"))

    return {"detail": "Successfully approved bot", "guild_id": str(main_server), "bot_id": str(data.bot_id)}


@action("deny", [enums.BotState.under_review], action_log=enums.UserBotAction.deny)
async def deny(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3", enums.BotState.denied,
                               request.state.user_id, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Denied",
        description=f"<@{request.state.user_id}> has denied <@{data.bot_id}>!\n**Once you've fixed what we've asked you to fix, please resubmit your bot by going to `Bot Settings`.**\n\nThank you for using Fates List :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully denied bot"}


@action("ban", [enums.BotState.approved], min_perm=4, action_log=enums.UserBotAction.ban)
async def ban(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3", enums.BotState.banned,
                               request.state.user_id, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Banned",
        description=f"<@{request.state.user_id}> has banned <@{data.bot_id}>!\n**Once you've fixed what we've need you to fix, please appeal your ban by going to `Bot Settings`.**\n\nThank you for using Fates List :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    asyncio.create_task(ban_user(main_server, data.bot_id, data.reason))

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully banned bot"}


@action("unban", [enums.BotState.banned], min_perm=4, action_log=enums.UserBotAction.unban)
async def unban(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3", enums.BotState.approved,
                               request.state.user_id, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0x00ff00,
        title="Bot Unbanned",
        description=f"<@{request.state.user_id}> has unbanned <@{data.bot_id}>!\n\nThank you for using Fates List again and sorry for any inconveniences caused! :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    asyncio.create_task(unban_user(main_server, data.bot_id, data.reason))

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully unbanned bot"}


@action("certify", [enums.BotState.approved], min_perm=5, action_log=enums.UserBotAction.certify)
async def certify(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3", enums.BotState.certified,
                               request.state.user_id, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0x00ff00,
        title="Bot Certified",
        description=f"<@{request.state.user_id}> has certified <@{data.bot_id}>.\n**Good Job!!!**\n\nThank you for using Fates List :heart:",
    )

    embed.add_field(name="Feedback", value=data.reason)

    for owner in data.owners:
        asyncio.create_task(
            add_role(main_server, owner["owner"], certified_developer, "Bot certified - owner gets role"))

    # Add certified bot role to bot
    asyncio.create_task(add_role(main_server, data.bot_id, certified_bot, "Bot certified - add bots role"))

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully certified bot"}


@action("uncertify", [enums.BotState.certified], min_perm=5, action_log=enums.UserBotAction.uncertify)
async def uncertify(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1 WHERE bot_id = $2", enums.BotState.approved, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Uncertified",
        description=f"<@{request.state.user_id}> has uncertified <@{data.bot_id}>.\n\nThank you for using Fates List but this was a necessary action :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    for owner in data.owners:
        asyncio.create_task(
            del_role(main_server, owner["owner"], certified_developer, "Bot uncertified - Owner gets role"))

    # Add certified bot role to bot
    asyncio.create_task(del_role(main_server, data.bot_id, certified_bot, "Bot uncertified - Bots Role"))

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully uncertified bot"}


@action("unverify", [enums.BotState.approved], min_perm=3, action_log=enums.UserBotAction.unverify)
async def unverify(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3", enums.BotState.pending,
                               request.state.user_id, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Unverified",
        description=f"<@{request.state.user_id}> has unverified <@{data.bot_id}> due to some issues we are looking into!\n\nThank you for using Fates List and we thank you for your patience :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully unverified bot"}


@action("requeue", [enums.BotState.banned, enums.BotState.denied], min_perm=3, action_log=enums.UserBotAction.requeue)
async def requeue(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET state = $1, verifier = $2 WHERE bot_id = $3", enums.BotState.pending,
                               request.state.user_id, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0x00ff00,
        title="Bot Requeued",
        description=f"<@{request.state.user_id}> has requeued <@{data.bot_id}> for re-review!\n\nThank you for using Fates List and we thank you for your patience :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully requeued bot"}


@action("reset-votes", [], min_perm=3)
async def reset_votes(request: Request, data: ActionWithReason):
    await app.state.db.execute("UPDATE bots SET votes = 0 WHERE bot_id = $1", data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Votes Reset",
        description=f"<@{request.state.user_id}> has force resetted <@{data.bot_id}> votes due to abuse!\n\nThank you for using Fates List and we are sorry for any inconveniences caused :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully reset bot votes"}


@action("reset-all-votes", [], min_perm=5)
async def reset_all_votes(request: Request, data: ActionWithReason):
    if data.reason == "STUB_REASON":
        data.reason = "Monthly Vote Reset"

    async with app.state.db.acquire() as conn:
        top_voted = await conn.fetch("SELECT bot_id, username_cached, votes, total_votes FROM bots WHERE state = 0 OR "
                                     "state = 6 ORDER BY votes DESC, total_votes DESC LIMIT 7")
        async with conn.transaction():
            bots = await app.state.db.fetch("SELECT bot_id, votes FROM bots")
            for bot in bots:
                await conn.execute("INSERT INTO bot_stats_votes_pm (bot_id, epoch, votes) VALUES ($1, $2, $3)",
                                   bot["bot_id"], time.time(), bot["votes"])
            await conn.execute("UPDATE bots SET votes = 0")
            await conn.execute("DELETE FROM user_vote_table")

    embed = Embed(
        url="https://fateslist.xyz",
        title="All Bot Votes Reset",
        color=0x00ff00,
        description=f"<@{request.state.user_id}> has resetted all votes!\n\nThank you for using Fates List :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    top_voted_str = ""
    i = 1
    for bot in top_voted:
        add = f"**#{i}.** [{bot['username_cached'] or 'Uncached User'}](https://fateslist.xyz/bot/{bot['bot_id']}) - {bot['votes']} votes this month and {bot['total_votes']} total votes. GG!\n"
        if len(top_voted_str) + len(add) > 2048:
            break
        else:
            top_voted_str += add
        i += 1

    embed.add_field(name="Top Voted", value=top_voted_str)

    await send_message({"content": "", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully reset all bot votes"}


@action("set-flag", [], min_perm=3)
async def set_flag(request: Request, data: ActionWithReason):
    if not isinstance(data.context, int):
        return {"detail": "Flag must be an integer", "err": True}
    try:
        flag = enums.BotFlag(data.context)
    except:
        return {"detail": "Flag must be of enum Flag", "err": True}

    existing_flags = await app.state.db.fetchval("SELECT flags FROM bots WHERE bot_id = $1", data.bot_id)
    existing_flags = existing_flags or []
    existing_flags = set(existing_flags)
    existing_flags.add(int(flag))

    try:
        existing_flags.remove(int(enums.BotFlag.unlocked))
    except:
        pass

    existing_flags = list(existing_flags)
    existing_flags.sort()
    await app.state.db.fetchval("UPDATE bots SET flags = $1 WHERE bot_id = $2", existing_flags, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Flag Updated",
        description=f"<@{request.state.user_id}> has modified the flags of <@{data.bot_id}> with addition of {flag.name} ({flag.value})!\n\nThank you for using Fates List and we are sorry for any inconveniences caused :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully set flag"}


@action("unset-flag", [], min_perm=3)
async def unset_flag(request: Request, data: ActionWithReason):
    if not isinstance(data.context, int):
        return {"detail": "Flag must be an integer", "err": True}
    try:
        flag = enums.BotFlag(data.context)
    except:
        return {"detail": "Flag must be of enum Flag", "err": True}

    existing_flags = await app.state.db.fetchval("SELECT flags FROM bots WHERE bot_id = $1", data.bot_id)
    existing_flags = existing_flags or []
    existing_flags = set(existing_flags)
    try:
        existing_flags.remove(int(flag))
    except:
        return {"detail": "Flag not on this bot", "err": True}

    try:
        existing_flags.remove(int(enums.BotFlag.unlocked))
    except:
        pass

    existing_flags = list(existing_flags)
    existing_flags.sort()
    await app.state.db.fetchval("UPDATE bots SET flags = $1 WHERE bot_id = $2", existing_flags, data.bot_id)

    embed = Embed(
        url=f"https://fateslist.xyz/bot/{data.bot_id}",
        color=0xe74c3c,
        title="Bot Flag Updated",
        description=f"<@{request.state.user_id}> has modified the flags of <@{data.bot_id}> with removal of {flag.name} ({flag.value})!\n\nThank you for using Fates List and we are sorry for any inconveniences caused :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.main_owner}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully unset flag"}

# Lynx base websocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict | list, websocket: WebSocket):
        ## REMOVE WHEN SQUIRREL SUPPORTS SPLD LIKE WEB DOES
        if websocket.state.plat == "SQUIRREL" and message.get("resp") == "spld":
            # Not supported by squirrel yet
            message = {"resp": "index", "detail": f"{message.get('e', 'Unknown SPLD event')}"}
        
        try:
            if websocket.state.debug:
                print(f"Sending message: {websocket.client.host=}, {message=}")
                await websocket.send_json(jsonable_encoder(message))
            else:
                try:
                    await websocket.send_bytes(zlib.compress(msgpack.packb(message)))
                except:
                    await websocket.send_bytes(zlib.compress(msgpack.packb(jsonable_encoder(message))))
        except RuntimeError as e:
            try:
                await websocket.close(1008)
            except:
                return False
        return True

    async def broadcast(self, message: dict | list):
        for connection in self.active_connections:
            await manager.send_personal_message(message, connection)
    
manager = ConnectionManager()

ws_action_dict = {
}

def ws_action(name: str):
    def decorator(func):
        ws_action_dict[name] = func
        return func
    return decorator

# Checks which approved and denied bots are on the site but not on support server
@ws_action("ss_check")
async def ss_check(websocket: WebSocket, _: dict):
    exc_bots = [536991182035746816]

    bots = await app.state.db.fetch("SELECT bot_id FROM bots WHERE state = $1 OR state = $2", enums.BotState.approved, enums.BotState.certified)

    count = await app.state.db.fetchval("SELECT COUNT(1) FROM bots")
    in_ss = 0
    error_bots = []

    for bot in bots:
        if bot["bot_id"] in exc_bots:
            continue
        guild = app.state.discord.get_guild(int(main_server))
        member = guild.get_member(bot["bot_id"])
        if member:
            in_ss += 1
        else:
            error_bots.append(str(bot["bot_id"]) + ": " + f"https://discord.com/api/oauth2/authorize?client_id={bot['bot_id']}&permissions=0&scope=bot%20applications.commands")
    
    return {
        "resp": "ss_check",
        "total_count": count,
        "approved_count": len(bots),
        "in_ss": in_ss + len(exc_bots),
        "error_bots": error_bots,
    }

@ws_action("spld")
async def spld(ws: WebSocket, data: dict):    
    try:
        event = SPLDEvent(data.get("e"))
    except:
        return await unsupported(ws)

    if event == SPLDEvent.telemetry:
        # We may collect telemetry logs for errors in the future
        print(f"[LYNX] Message from JS: {data.get('data')}")
    else:
        return await unsupported(ws)

@ws_action("exp_rollout_menu")
async def exp_rollout_menu(ws: WebSocket, _: dict):
    # Possible remove on experiment over
    if Experiments.LynxExperimentRolloutView not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    if ws.state.member.perm < 5:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    exp_initial = """
| Name | Value | Count | Users |
| :--- | :--- | :-- | :-- |
"""

    exp_details = ""

    for exp in list(Experiments):
        exp_prop = exp_props.get(exp.name)
        if exp_prop:
            exp_details += f"""
#### {exp.name}
- Description: **{exp_prop.description}**
- Status: **{exp_prop.status.name} ({exp_prop.status.value})**
- Minimum Perm Filter (does not apply to full/controlled rollouts): **{exp_prop.min_perm}**
- Rollout Allowed (only applies to mass/controlled roll outs): **{exp_prop.rollout_allowed}**
"""

        users = await app.state.db.fetch("SELECT user_id FROM users WHERE experiments && $1", [exp.value])

        user_txt = "User count too low/high to display or rollout already complete"

        if len(users) < 7 and len(users) > 0:
            user_txt = []
            for user in users:
                user_txt.append(str(user["user_id"]))
            user_txt = ", ".join(user_txt)

        exp_initial += f"{exp.name} | {exp.value} | {len(users)} | {user_txt} |\n"

    return {
        "resp": "index",
        "title": "Experiment Rollout",
        "data": f"""
## Overview

{exp_initial}

## Experiments

{exp_details}

## Add User To Experiment

<div class="form-group">
    <label for="exp_add-value">Experiment Value</label>
    <input type="number" class="form-control" id="exp_add-value" placeholder="Experiment Value">
    <label for="exp_add-id">User ID</label>
    <input type="number" class="form-control" id="exp_add-id" placeholder="User ID">
    <button onclick="addUserToExp()">Add</button>
</div>

## Remove User From Experiment

<div class="form-group">
    <label for="exp_del-value">Experiment Value</label>
    <input type="number" class="form-control" id="exp_del-value" placeholder="Experiment Value">
    <label for="exp_del-id">User ID</label>
    <input type="number" class="form-control" id="exp_del-id" placeholder="User ID">
    <button onclick="delUserFromExp()">Remove</button>
</div>

## Controlled Rollout Experiment

<div class="form-group">
    <label for="exp_rollout_controlled-value">Experiment Value</label>
    <input type="number" class="form-control" id="exp_rollout_controlled-value" placeholder="Experiment Value">
    <label for="exp_rollout_controlled-limit">Rollout Limit (suffix with % for percentage)</label>
    <input type="text" class="form-control" id="exp_rollout_controlled-limit" placeholder="Experiment Limit">
    <button onclick="rolloutControlled()">Rollout</button>
</div>

## Rollout Experiment

<div class="form-group">
    <label for="exp_rollout-value">Experiment Value</label>
    <input type="number" class="form-control" id="exp_rollout-value" placeholder="Experiment Value">
    <button onclick="rolloutExp()">Rollout</button>
</div>

## Undo Rollout Experiment

<div class="form-group">
    <label for="exp_rollout_undo-value">Experiment Value</label>
    <input type="number" class="form-control" id="exp_rollout_undo-value" placeholder="Experiment Value">
    <button onclick="rolloutExpUndo()">Undo</button>
</div>
        """,
        "ext_script": "exp-rollout"
    }

@ws_action("exp_rollout_add")
async def exp_rollout_add(ws: WebSocket, data: dict):
    # Possible remove on experiment over
    if Experiments.LynxExperimentRolloutView not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    if ws.state.member.perm < 5:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}
    
    try:
        exp = Experiments(int(data["exp"]))
        exp_prop = exp_props[exp.name]

        if exp_prop.min_perm > 0:
            # Check permission of new user
            _, _, sm = await is_staff(int(data["id"]), 1)
            if sm.perm < exp_prop.min_perm:
                return  {"detail": "Invalid user perm of new user"}

        # remove old and add
        await app.state.db.execute("UPDATE users SET experiments = array_remove(experiments, $1) WHERE user_id = $2", int(data["exp"]), int(data["id"]))
        await app.state.db.execute("UPDATE users SET experiments = array_append(experiments, $1) WHERE user_id = $2", int(data["exp"]), int(data["id"]))
    except:
        return {"detail": "Invalid experiment data"}

    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/exp-rollout"})
    return {"detail": "Added"}

@ws_action("exp_rollout_del")
async def exp_rollout_add(ws: WebSocket, data: dict):
    # Possible remove on experiment over
    if Experiments.LynxExperimentRolloutView not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    if ws.state.member.perm < 5:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}
    
    try:
        await app.state.db.execute("UPDATE users SET experiments = array_remove(experiments, $1) WHERE user_id = $2", int(data["exp"]), int(data["id"]))
    except:
        return {"detail": "Invalid experiment data"}

    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/exp-rollout"})
    return {"detail": "Removed"}

@ws_action("exp_rollout_all")
async def exp_rollout_all(ws: WebSocket, data: dict):
    if Experiments.LynxExperimentRolloutView not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    if ws.state.member.perm < 7:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    try:
        exp = Experiments(int(data["exp"]))
        exp_prop = exp_props[exp.name]
        if not exp_prop.rollout_allowed:
            return {"detail": "Rollout not allowed for this experiment"}
    except:
        return {"detail": "Invalid experiment data"}

    await app.state.db.execute("UPDATE lynx_data SET default_user_experiments = array_remove(default_user_experiments, $1)", int(data["exp"]))
    await app.state.db.execute("UPDATE lynx_data SET default_user_experiments = array_append(default_user_experiments, $1)", int(data["exp"]))

    await app.state.db.execute("UPDATE users SET experiments = array_remove(experiments, $1)", int(data["exp"]))
    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/exp-rollout"})
    return {"detail": "Rolled out"}

@ws_action("exp_rollout_undo")
async def exp_rollout_all(ws: WebSocket, data: dict):
    if Experiments.LynxExperimentRolloutView not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    if ws.state.member.perm < 7:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    await app.state.db.execute("UPDATE users SET experiments = array_remove(experiments, $1)", int(data["exp"]))

    await app.state.db.execute("UPDATE lynx_data SET default_user_experiments = array_remove(default_user_experiments, $1)", int(data["exp"]))

    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/exp-rollout"})
    return {"detail": "Rolled out undone"}

@ws_action("exp_rollout_controlled")
async def exp_rollout_all(ws: WebSocket, data: dict):
    if Experiments.LynxExperimentRolloutView not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    if ws.state.member.perm < 7:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    try:
        exp = Experiments(int(data["exp"]))
        exp_prop = exp_props[exp.name]
        if not exp_prop.rollout_allowed:
            return {"detail": "Rollout not allowed for this experiment"}
    except:
        return {"detail": "Invalid experiment data"}

    # Check percent prefix
    try:
        if data["limit"].endswith("%"):     
            user_count = await app.state.db.fetchval("SELECT COUNT(1) FROM users")
            data["limit"] = math.ceil((float(data["limit"][:-1]) / 100) * user_count)
    except:
        return {"detail": "Invalid limit data"}

    users = await app.state.db.fetch("SELECT user_id, experiments FROM users WHERE NOT (experiments && $1) ORDER BY RANDOM() LIMIT $2", [int(data["exp"])], int(data["limit"]))        

    for fetch in users:
        await app.state.db.execute("UPDATE users SET experiments = array_append(experiments, $1) WHERE user_id = $2", int(data["exp"]), fetch["user_id"])

    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/exp-rollout"})
    return {"detail": f"Pushed controlled roll out to {data['limit']} users"}

@ws_action("admin")
async def admin(ws: WebSocket, _: dict):
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    return {
        "title": "Admin Console",
        "data": """

<blockquote class="quote">

### Important Information

All things done on the admin console are logged

**Please don't be stupid**

Username is your discord account username and password is the password given to you when you first verified

Use https://lynx.fateslist.xyz/reset to reset your admin password

</blockquote>

<iframe id="admin-iframe" data-src="https://lynx.fateslist.xyz/_admin" style="min-height: 1000px;" width="100%" height="100%" frameborder="0"></iframe>
        """,
        "ext_script": "admin-iframe"
    }


@ws_action("apply_staff")
async def apply_staff(ws: WebSocket, data: dict):
    if ws.state.member.perm == -1:
        return {"detail": "You must be logged in to create staff applications!"}

    for pane in staffapps.questions:
        for question in pane.questions:
            answer = data["answers"].get(question.id)
            if not answer:
                return {"detail": f"Missing answer for question {question.id}"}
            elif len(answer) < question.min_length:
                return {"detail": f"Answer for question {question.id} is too short"}
            elif len(answer) > question.max_length:
                return {"detail": f"Answer for question {question.id} is too long"}
    
    await app.state.db.execute(
        "INSERT INTO lynx_apps (user_id, questions, answers, app_version) VALUES ($1, $2, $3, $4)",
        int(ws.state.user["id"]),
        orjson.dumps(jsonable_encoder(staffapps.questions)).decode(),
        orjson.dumps(data["answers"]).decode(),
        3
    )

    return {"detail": "Successfully applied for staff!"}

@ws_action("get_sa_questions")
async def get_sa_questions(ws: WebSocket, _):
    """Get staff app questions"""
    return {"questions": jsonable_encoder(staffapps.questions)}


@ws_action("loa")
async def loa(ws: WebSocket, _):
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    return {
        "title": "Leave Of Absense",
        "pre": "/links",
        "data": f"""
::: warning

Please don't abuse this by spamming LOA's non-stop or you **will** be demoted!

:::

There are *two* ways of creating a LOA.

### Simple Form

<form class="needs-validation" novalidate>
    <div class="form-group">
        <label for="reason">Reason</label>
        <textarea class="form-control question" id="reason" name="reason" placeholder="Reason for LOA" required aria-required="true"></textarea>
        <div class="valid-feedback">
            Looks good!
        </div>
        <div class="invalid-feedback">
            Reason is either missing or too long!
        </div>
    </div>
    <div class="form-group">
        <label for="duration">Duration</label>
        <input type="datetime-local" class="form-control question" id="duration" name="duration" placeholder="Duration of LOA" required aria-required="true"/>
        <div class="valid-feedback">
            Looks good!
        </div>
        <div class="invalid-feedback">
            Duration is either missing or too long!
        </div>
    </div>
    <button type="submit" id="loa-btn">Submit</button>
</form>

### Piccolo Admin

<ol>
    <li>Login to Lynx Admin</li>
    <li>Click Leave Of Absense</li>
    <li>Click 'Add Row'</li>
    <li>Fill out the nessesary fields</li>
    <li>Click 'Save'</li>
</ol>
    """,
    "ext_script": "apply",    
    }

@ws_action("send_loa")
async def send_loa(ws: WebSocket, data: dict):
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    if not data.get("answers"):
        return {"detail": "You did not fill out the form correctly"}
    if not data["answers"]["reason"]:
        return {"detail": "You did not fill out the form correctly"}
    if not data["answers"]["duration"]:
        return {"detail": "You did not fill out the form correctly"}
    try:
        date = parser.parse(data["answers"]["duration"])
    except:
        return {"detail": "You did not fill out the form correctly"}
    if date.year - datetime.datetime.now().year not in (0, 1):
        return {"detail": "Duration must be in within this year"}

    await app.state.db.execute(
        "INSERT INTO leave_of_absence (user_id, reason, estimated_time, start_date) VALUES ($1, $2, $3, $4)",
        int(ws.state.user["id"]),
        data["answers"]["reason"],
        date - datetime.datetime.now(),
        datetime.datetime.now(),
    )

    return {"detail": "Submitted LOA successfully"}

@ws_action("staff_apps")
async def staff_apps(ws: WebSocket, data: dict):
    # Get staff application list
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    staff_apps = await app.state.db.fetch(
        "SELECT user_id, app_id, questions, answers, created_at FROM lynx_apps ORDER BY created_at DESC")
    app_html = ""

    for staff_app in staff_apps:
        if str(staff_app["app_id"]) == data.get("open", ""):
            open_attr = "open"
        else:
            open_attr = ""
        user = await fetch_user(staff_app['user_id'])
        user["username"] = bleach.clean(user["username"])

        questions = orjson.loads(staff_app["questions"])
        answers = orjson.loads(staff_app["answers"])

        questions_html = ""

        for pane in questions:
            questions_html += f"<h3>{pane['title']}</h3><strong>Prelude</strong>: {pane['description']}<br/>"
            for question in pane["questions"]:
                questions_html += f"""
                    <h4>{question['title']}</h4>
                    <pre class="pre">
                        <strong>ID:</strong> {question['id']}
                        <strong>Minimum Length:</strong> {question['min_length']}
                        <strong>Maximum Length:</strong> {question['max_length']}
                        <strong>Question:</strong> {question['question']}
                        <strong>Answer:</strong> {bleach.clean(answers[question['id']])}
                    </pre>
                """

        app_html += f"""
        <details {open_attr}>
            <summary>{staff_app['app_id']}</summary>
            <a href='/user-actions?add_staff_id={user['id']}'"><button>Accept</button></a>
            <button onclick="deleteAppByUser('{user['id']}')">Delete</button>
            <h2>User Info</h2>
            <p><strong><em>Created At:</em></strong> {staff_app['created_at']}</p>
            <p><strong><em>User:</em></strong> {bleach.clean(user['username'])} ({user['id']})</p>
            <h2>Application:</h2> 
            {questions_html}
            <br/>
            <a href='/user-actions?add_staff_id={user['id']}'"><button>Accept</button></a>
            <button onclick="deleteAppByUser('{user['id']}')">Delete</button>
        </details>
        """

    return {
        "title": "Staff Application List",
        "pre": "/links",
        "data": f"""
<p>Please verify applications fairly</p>
{app_html}
<br/>
        """,
        "ext_script": "user-actions",
    }

@ws_action("user_actions")
async def user_actions(ws: WebSocket, data: dict):
    data = data.get("data", {})
    # Easiest way to block cross origin is to just use a hidden input
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms, "min_perm": 2}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    user_state_select = """
<label for='user_state_select'>New State</label><br/>
<select name='user_state_select' id='user_state_select'> 
    """

    for state in list(enums.UserState):
        user_state_select += f"""
<option value={state.value}>{state.name} ({state.value})</option>
        """
    user_state_select += "</select>"

    return {
        "title": "User Actions",
        "data": f"""
## For refreshers, the staff guide is here:

{staff_guide_md}

<hr/>

Now that we're all caught up with the staff guide, here are the list of actions you can take:

::: action-addstaff

### Add Staff

- Head Admin+ only
- Definition: user => bot_reviewer

<div class="form-group">
<label for="staff_user_id">User ID</label>
<input class="form-control" id="staff_user_id" name="staff_user_id" placeholder='user id here' type="number" value="{data.get("add_staff_id") or ''}" />
<button onclick="addStaff()">Add</button>
</div>

:::

::: action-removestaff

### Remove Staff

- Head Admin+ only
- Definition: staff => user

<div class="form-group">
<label for="staff_remove_user_id">User ID</label>
<input class="form-control" id="staff_remove_user_id" name="staff_remove_user_id" placeholder='user id here' type="number" />
</div>

<div class="form-group">
<label for="staff_remove_reason">Reason</label>
<textarea 
class="form-control"
type="text" 
id="staff_remove_reason" 
name="staff_remove_reason"
placeholder="Enter reason for removal of staff here!"
></textarea>
</div>

<button onclick="removeStaff()">Remove</button>

:::

::: action-setflag

### Set/Unset Staff Flag

- Bot Reviewer+ only
- Definition: flag => ~flag 

<div class="form-check">
<input class="form-check-input" type="checkbox" id="is_staff_public" name="is_staff_public" />
<label class="form-check-label" for="is_staff_public">Staff Flag Mode (unchecked = Set)</label>
</div>

<button onclick="modStaffFlag()">Update</button>

:::

::: action-userstate

### Set User State

- Admin+ only
- Definition: state => $user_state

<div class="form-group">
<label for="user_state_id">User ID</label>
<input class="form-control" id="user_state_id" name="user_state_id" placeholder='user id here' type="number" />
</div>

{user_state_select}

<div class="form-group">
<label for="user_state_reason">Reason</label>
<textarea 
class="form-control"
type="text" 
id="user_state_reason" 
name="user_state_reason"
placeholder="Enter reason for state change here!"
></textarea>
</div>

<button onclick="setUserState()">Set State</button>

:::
        """,
        "ext_script": "user-actions",
    }

@ws_action("bot_actions")
async def bot_actions(ws: WebSocket, _):
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    elif not ws.state.verified:
        return {"resp": "spld", "e": SPLDEvent.verify_needed}

    queue = await app.state.db.fetch(
        "SELECT bot_id, username_cached, description, prefix, created_at FROM bots WHERE state = $1 ORDER BY created_at ASC",
        enums.BotState.pending)

    queue_select = bot_select("queue", queue)

    under_review = await app.state.db.fetch("SELECT bot_id, username_cached FROM bots WHERE state = $1",
                                            enums.BotState.under_review)

    under_review_select_approved = bot_select("under_review_approved", under_review, reason=True)
    under_review_select_denied = bot_select("under_review_denied", under_review, reason=True)
    under_review_select_claim = bot_select("under_review_claim", under_review, reason=True)

    approved = await app.state.db.fetch(
        "SELECT bot_id, username_cached FROM bots WHERE state = $1 ORDER BY created_at DESC",
        enums.BotState.approved)

    ban_select = bot_select("ban", approved, reason=True)
    certify_select = bot_select("certify", approved, reason=True)
    unban_select = bot_select("unban",
                                await app.state.db.fetch("SELECT bot_id, username_cached FROM bots WHERE state = $1",
                                                        enums.BotState.banned), reason=True)
    unverify_select = bot_select("unverify", await app.state.db.fetch(
        "SELECT bot_id, username_cached FROM bots WHERE state = $1", enums.BotState.approved), reason=True)
    requeue_select = bot_select("requeue", await app.state.db.fetch(
        "SELECT bot_id, username_cached FROM bots WHERE state = $1 OR state = $2", enums.BotState.denied,
        enums.BotState.banned), reason=True)

    uncertify_select = bot_select("uncertify", await app.state.db.fetch(
        "SELECT bot_id, username_cached FROM bots WHERE state = $1", enums.BotState.certified), reason=True)

    reset_bot_votes_select = bot_select("reset-votes", await app.state.db.fetch(
        "SELECT bot_id, username_cached FROM bots WHERE state = $1 OR state = $2", enums.BotState.approved,
        enums.BotState.certified), reason=True)

    flag_list = list(enums.BotFlag)
    flags_select = "<label>Select Flag</label><select id='flag' name='flag'>"
    for flag in flag_list:
        flags_select += f"<option value={flag.value}>{flag.name} ({flag.value})</option>"
    flags_select += "</select>"

    flags_bot_select = bot_select("set-flag", await app.state.db.fetch("SELECT bot_id, username_cached FROM bots"),
                                    reason=True)

    queue_md = ""

    for bot in queue:
        owners = await app.state.db.fetch("SELECT owner, main FROM bot_owner WHERE bot_id = $1", bot["bot_id"])

        owners_md = ""

        for owner in owners:
            user = await fetch_user(owner["owner"])
            owners_md += f"""\n     - {user['username']}  ({owner['owner']}) |  main -> {owner["main"]}"""

        queue_md += f"""
{bot['username_cached']} | [Site Page](https://fateslist.xyz/bot/{bot['bot_id']})

- Prefix: {bot['prefix'] or '/'}
- Description: {bleach.clean(bot['description'])}
- Owners: {owners_md}
- Created At: {bot['created_at']}

"""

    return {
        "title": "Bot Actions",
        "pre": "/links",
        "data": f"""
## For refreshers, the staff guide is here:

{staff_guide_md}

<hr/>

Now that we're all caught up with the staff guide, here are the list of actions you can take:

## Bot Queue

::: info 

Please check site pages before approving/denying. You can save lots of time by doing this!

:::

{queue_md}

## Actions

::: action-claim

### Claim Bot

- Only claim bots you have the *time* to review
- Please unclaim bots whenever you are no longer actively reviewing them
- Definition: pending => under_review

{queue_select}
<button onclick="claim()">Claim</button>

:::

::: action-unclaim

### Unclaim Bot

- Please unclaim bots whenever you are no longer actively reviewing them
- Definition: under_review => pending

{under_review_select_claim}
<button onclick="unclaim()">Unclaim</button>

:::

::: action-approve

### Approve Bot 

<span id='approve-invite'></span>

- You must claim this bot before approving and preferrably before testing
- Definition: under_review => approved

{under_review_select_approved}

<button onclick="approve()">Approve</button>

:::

::: action-deny

### Deny Bot

- You must claim this bot before denying and preferrably before testing
- Definition: under_review => deny

{under_review_select_denied}
<button onclick="deny()">Deny</button>

:::

::: action-ban

### Ban Bot 

- Admin+ only
- Must be approved and *not* certified
- Definition: approved => banned

{ban_select}
<button onclick="ban()">Ban</button>

:::

::: action-unban

### Unban Bot

- Admin+ only
- Must *already* be banned
- Definition: banned => approved

{unban_select}
<button onclick="unban()">Unban</button>

:::

::: action-certify

### Certify Bot

- Head Admin+ only
- Definition: approved => certified

{certify_select}
<button onclick="certify()">Certify</button>

:::

::: action-uncertify

### Uncertify Bot

- Head Admin+ only
- Definition: certified => approved

{uncertify_select}
<button onclick="uncertify()">Uncertify</button>

:::

::: action-unverify

### Unverify Bot

- Moderator+ only
- Definition: approved => under_review

{unverify_select}
<button onclick="unverify()">Unverify</button>

:::

::: action-requeue

### Requeue Bot

- Moderator+ only
- Definition: denied | banned => under_review

{requeue_select}
<button onclick="requeue()">Requeue</button>

:::

::: action-reset-votes

### Reset Bot Votes

- Moderator+ only
- Definition: votes => 0

{reset_bot_votes_select}
<button onclick="resetVotes()">Reset</button>

:::

::: action-reset-all-votes

### Reset All Votes

- Head Admin+ only
- Definition: votes => 0 %all%

<div class="form-group">
<textarea
class = "form-control"
id="reset-all-votes-reason"
placeholder="Reason for resetting all votes. Defaults to 'Monthly Votes Reset'"
></textarea>
</div>

<button onclick="resetAllVotes()">Reset All</button>

:::

::: action-setflag

### Set/Unset Bot Flag

- Moderator+ only
- Definition: flag => flags.intersection(flag)

{flags_bot_select}

{flags_select}

<div class="form-check">
<input class="form-check-input" type="checkbox" id="unset" name="unset" />
<label class="form-check-label" for="unset">Unset Flag (unchecked = Set)</label>
</div>

<button onclick="setFlag()">Update</button>

:::
""",
        "ext_script": "bot-actions",
    }

@ws_action("staff_verify")
async def staff_verify(ws: WebSocket, _):
    if ws.state.member.perm < 2:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}
    return {
        "title": "Fates List Staff Verification",
        "data": """
<h3>In order to continue, you will need to make sure you are up to date with our rules</h3>
<pre>
<strong>You can find our staff guide <a href="https://lynx.fateslist.xyz/staff-guide">here</a></strong>

- The code is somewhere in the staff guide so please read the full guide
- Look up terms you do not understand on Google!
<strong>Once you complete this, you will automatically recieve your roles in the staff server</strong>
</pre>

<div style="margin-left: auto; margin-right: auto; text-align: center;">
<div class="form-group">
<textarea class="form-control" id="staff-verify-code"
placeholder="Enter staff verification code here"
></textarea>
</div>
</div>
<strong>
By continuing, you agree to:
<ul>
<li>Abide by Discord ToS</li>
<li>Abide by Fates List ToS</li>
<li>Agree to try and be at least partially active on the list</li>
<li>Be able to join group chats (group DMs) if required by Fates List Admin+</li>
</ul>
If you disagree with any of the above, you should stop now and consider taking a 
Leave Of Absence or leaving the staff team though we hope it won't come to this...
<br/><br/>

Please <em>read</em> the staff guide carefully. Do NOT just Ctrl-F. If you ask questions
already in the staff guide, you will just be told to reread the staff guide!
</strong>
<br/>
<div id="verify-parent">
<button id="verify-btn" onclick="verify()">Verify</button>
</div>""",
        "script": """
async function verify() {
    document.querySelector("#verify-btn").innerText = "Verifying...";
    let code = document.querySelector("#staff-verify-code").value

    wsSend({request: "cosmog", code: code})
}
"""
    }

async def notifs(ws: WebSocket):
    notifs_sent = []
    notifs_sent_times = 0

    while True:
        notifs = await app.state.db.fetch("SELECT id, acked_users, message, type, staff_only FROM lynx_notifications")
        _send_notifs = []
        for notif in notifs:
            if notif["id"] in notifs_sent and notifs_sent_times >= 3:
                # Don't keep sending same message over and over again, give a buffer of 3 times
                continue

            if notif["staff_only"]:
                if ws.state.member.perm >= 2:
                    _send_notifs.append(notif)
                    notifs_sent.append(notif["id"])
            elif notif["acked_users"]:
                if ws.state.user and int(ws.state.user["id"]) in notif["acked_users"]:
                    _send_notifs.append(notif)
                    notifs_sent.append(notif["id"])
            else:
                _send_notifs.append(notif)
                notifs_sent.append(notif["id"])
        
        if len(_send_notifs) > 0:
            res = await manager.send_personal_message({"resp": "notifs", "data": _send_notifs}, ws)
            if not res:
                return

        res = await manager.send_personal_message({"resp": "spld", "e": SPLDEvent.ping}, ws)
        notifs_sent_times += 1
        if not res:
            return

        await asyncio.sleep(5)

@ws_action("docs")
async def docs(ws: WebSocket, data: dict):
    page = data.get("path", "/").split("#")[0]
    source = data.get("source", False)

    if page.endswith(".md"):
        page = f"/docs/{page[:-3]}"

    elif not page or page == "/docs":
        page = "/index"

    if not page.replace("-", "").replace("_", "").replace("/", "").replace("!", "").isalnum():
        return {"detail": "Invalid page"}

    try:
        with open(f"api-docs/{page}.md", "r") as f:
            md_data = f.read()
    except FileNotFoundError as exc:
        return {"detail": f"api-docs/{page}.md not found -> {exc}"}

    if source:
        return {
            "title": page.split('/')[-1].replace('-', ' ').title() + " (Source)",
            "data": f"""
    <pre>{md_data.replace('<', '&lt').replace('>', '&gt')}</pre>
            """ if ws.state.plat != "DOCREADER" else md_data,
            "source": True
        }
    
    return {
        "title": page.split('/')[-1].replace('-', ' ').title(),
        "data": md_data,
        "source": False,
        "page": page
    }

@ws_action("eternatus")
async def docs_feedback(ws: WebSocket, data: dict):
    if len(data.get("feedback", "")) < 5:
        return {"detail": "Feedback must be greater than 10 characters long!"}

    if ws.state.user:
        user_id = int(ws.state.user["id"])
        username = ws.state.user["username"]
    else:
        user_id = None
        username = "Anonymous"

    if not data.get("page", "").startswith("/"):
        return {"detail": "Unexpected page!"}

    await app.state.db.execute(
        "INSERT INTO lynx_ratings (feedback, page, username_cached, user_id) VALUES ($1, $2, $3, $4)",
        data["feedback"],
        data["page"],
        username,
        user_id
    )

    return {"detail": "Successfully rated"}

@ws_action("cosmog")
async def verify_code(ws: WebSocket, data: dict):
    code = data.get("code", "")

    if not ws.state.user:
        return

    if ws.state.verified:
        return {
            "detail": "You are already verified"
        }

    if not code_check(code, int(ws.state.user["id"])):
        return {"detail": "Invalid code"}
    else:
        username = ws.state.user["username"]
        password = get_token(96)

        try:
            await app.state.db.execute("DELETE FROM piccolo_user WHERE username = $1", username)
            await BaseUser.create_user(
                username=username,
                password=password,
                email=username + "@fateslist.xyz",
                active=True,
                admin=True
            )
        except:
            return {"detail": "Failed to create user on lynx. Please contact Rootspring#6701"}

        await app.state.db.execute(
            "UPDATE users SET staff_verify_code = $1 WHERE user_id = $2",
            code,
            int(ws.state.user["id"]),
        )

        await add_role(staff_server, ws.state.user["id"], access_granted_role, "Access granted to server")
        await add_role(staff_server, ws.state.user["id"], ws.state.member.staff_id, "Gets corresponding staff role")

        return {"detail": "Successfully verified staff member", "pass": password}

@ws_action("index")
async def index(_, __):
    return {
        "title": "Welcome To Lynx", 
        "data": """
Welcome to Lynx. This page provides our API documentation, privacy policies, terms of service and is our admin console for staff members!

By continuing, you agree to:

- Abide by Discord ToS</li>
- Abide by Fates List ToS available [here](/privacy)

### Notes for staff members

- If you are a staff member and you disagree with any of the above, you should stop now and consider taking a Leave Of Absence or leaving the staff team though we hope it won't come to this...

- If you are a staff member at Fates List, you must be able to join group chats (group DMs) if required by Fates List Admin+

- Please <em>read</em> the staff guide carefully. Do NOT just Ctrl-F. If you ask questions already in the staff guide, you will just be told to reread the staff guide!

- In case, you haven't went through staff verification and you somehow didn't get redirected to it, click <a href="/staff-verify">here</a> 
<br/><br/>
<a href="/links">Some Useful Links!</a>
                """}

@ws_action("perms")
async def perms(ws: WebSocket, _):
    return {"data": ws.state.member.dict()}

@ws_action("reset")
async def reset(ws: WebSocket, _):
    # Remove from db
    if ws.state.user:
        await app.state.db.execute(
            "UPDATE users SET api_token = $1, staff_verify_code = NULL WHERE user_id = $2",
            get_token(132),
            int(ws.state.user["id"])
        )
        await app.state.db.execute(
            "DELETE FROM piccolo_user WHERE username = $1",
            ws.state.user["username"]
        )
        return {}

@ws_action("reset_page")
async def reset_page(_, __):
    return {
        "title": "Lynx Credentials Reset",
        "pre": "/links",
        "data": f"""
<p>If you're locked out of your discord account or otherwise need to reset your credentials, just click the 'Reset' button. It will do the same
thing as <strong>/lynxreset</strong> used to</p>

<div id="verify-parent">
    <button id="verify-btn" onclick="reset()">Reset</button>
</div>
        """,
        "script": """
            async function reset() {
                document.querySelector("#verify-btn").innerText = "Resetting...";

                wsSend({request: "reset"})
            }
        """
    }

@ws_action("links")
async def links(ws: WebSocket, _):
    if ws.state.member.perm > 2:
        return {
            "title": "Some Useful Links",
            "data": f"""
<blockquote class="quote">
    <h5>Some Nice Links</h5>
    <a href="/my-perms">My Permissions</a><br/>
    <a href="/reset">Lynx Credentials Reset</a><br/>
    <a href="/loa">Leave Of Absense</a><br/>
    <a href="/staff-apps">Staff Applications</a><br/>
    <a href="/links">Some Useful Links</a><br/>
    <a href="/staff-verify">Staff Verification</a> (in case you need it)<br/>
    <a href="/staff-guide">Staff Guide</a><br/>
    <a href="/docs/roadmap">Our Roadmap</a><br/>
    <a href="/bot-actions">Bot Actions</a><br/>
    <a href="/user-actions">User Actions</a><br/>
    <a href="/requests">Requests</a><br/>
</blockquote>
<blockquote class="quote">
    <h5 id="credits">Credits</h5>
    <p>Special Thanks to <strong><a href="https://adminlte.io/">AdminLTE</a></strong> for thier awesome contents!
    </p>
</blockquote>
        """}
    else:
        return {
            "title": "Some Useful Links",
            "data": f"""
<blockquote class="quote">
    <h5>Some Nice Links</h5>
    <strong>Some links hidden as you are not logged in or are not staff</strong>
    <a href="/my-perms">My Permissions</a><br/>
    <a href="/links">Some Useful Links</a><br/>
    <a href="/staff-guide">Staff Guide</a><br/>
    <a href="/docs/roadmap">Our Roadmap</a><br/>
    <a href="/requests">Requests</a><br/>
</blockquote>
<blockquote class="quote">
    <h5 id="credits">Credits</h5>
    <p>Special Thanks to <strong><a href="https://adminlte.io/">AdminLTE</a></strong> for thier awesome contents!
    </p>
</blockquote>
        """}

@ws_action("user_action")
async def user_action(ws: WebSocket, data: dict):
    try:
        action = app.state.user_actions[data["action"]]
    except:
        return {"detail": "Action does not exist!"}
    try:
        action_data = UserActionWithReason(**data["action_data"])
    except Exception as exc:
        return {"detail": f"{type(exc)}: {str(exc)}"}
    return await action(ws, action_data)

@ws_action("bot_action")
async def bot_action(ws: WebSocket, data: dict):
    try:
        action = app.state.bot_actions[data["action"]]
    except:
        return {"detail": "Action does not exist!"}
    try:
        action_data = ActionWithReason(**data["action_data"])
    except Exception as exc:
        return {"detail": f"{type(exc)}: {str(exc)}"}
    return await action(ws, action_data)

@ws_action("request_logs")
async def request_logs(ws: WebSocket, _):
    requests = await app.state.db.fetch("SELECT user_id, method, url, status_code, request_time from lynx_logs")
    requests_html = ""
    for request in requests:
        requests_html += f"""
<p>{request["user_id"]} - {request["method"]} - {request["url"]} - {request["status_code"]} - {request["request_time"]}</p>
        """

    return {
        "title": "Lynx Request Logs",
        "pre": "/links",
        "data": f"""
{requests_html}
        """
    }

@ws_action("data_request")
async def data_request(ws: WebSocket, data: dict):
    user_id = data.get("user", None)

    if not ws.state.user:
        return {
            "detail": "You must be logged in first!"
        }

    if ws.state.member.perm < 7 and ws.state.user["id"] != user_id:
        return {
            "detail": "You must either have permission level 7 or greater or the user id requested must be the same as your logged in user id."
        }

    try:
        user_id = int(user_id)
    except:
        return {
            "detail": "Invalid User ID"
        }

    user = await app.state.db.fetchrow("select * from users where user_id = $1", user_id)
    owners = await app.state.db.fetch("SELECT * FROM bot_owner WHERE owner = $1", user_id)

    # handle all fk key cases
    fk_keys = await app.state.db.fetch("""
SELECT sh.nspname AS table_schema,
  tbl.relname AS table_name,
  col.attname AS column_name,
  referenced_sh.nspname AS foreign_table_schema,
  referenced_tbl.relname AS foreign_table_name,
  referenced_field.attname AS foreign_column_name
FROM pg_constraint c
    INNER JOIN pg_namespace AS sh ON sh.oid = c.connamespace
    INNER JOIN (SELECT oid, unnest(conkey) as conkey FROM pg_constraint) con ON c.oid = con.oid
    INNER JOIN pg_class tbl ON tbl.oid = c.conrelid
    INNER JOIN pg_attribute col ON (col.attrelid = tbl.oid AND col.attnum = con.conkey)
    INNER JOIN pg_class referenced_tbl ON c.confrelid = referenced_tbl.oid
    INNER JOIN pg_namespace AS referenced_sh ON referenced_sh.oid = referenced_tbl.relnamespace
    INNER JOIN (SELECT oid, unnest(confkey) as confkey FROM pg_constraint) conf ON c.oid = conf.oid
    INNER JOIN pg_attribute referenced_field ON (referenced_field.attrelid = c.confrelid AND referenced_field.attnum = conf.confkey)
WHERE c.contype = 'f'""")

    related_data = {}

    for fk in fk_keys:
        if fk["foreign_table_name"] == "users":
            related_data[fk["table_name"]] = await app.state.db.fetch(f"SELECT * FROM {fk['table_name']} WHERE {fk['column_name']} = $1", user_id)


    lynx_notifications = await app.state.db.fetch("SELECT * FROM lynx_notifications, unnest(acked_users) AS "
                                                    "user_id WHERE user_id = $1", user_id)

    data = {"user": user, 
            "owners": owners, 
            "lynx_notifications": lynx_notifications,
            "owned_bots": [],
            "fk_keys": fk_keys,
            "related_data": related_data,
            "privacy": "Fates list does not profile users or use third party cookies for tracking other than what "
                        "is used by cloudflare for its required DDOS protection"}

    for bot in data["owners"]:
        data["owned_bots"].append(await app.state.db.fetch("SELECT * FROM bots WHERE bot_id = $1", bot["bot_id"]))

    def ddr_parse(d: dict | object):
        if isinstance(d, int):
            if d > 9007199254740991:
                return str(d)
            return d
        elif isinstance(d, list):
            return [ddr_parse(i) for i in d]
        elif isinstance(d, dict):
            nd = {} # New dict
            for k, v in d.items():
                nd[k] = ddr_parse(v)
            return nd
        else:
            return d        

    return {
        "user": str(user_id),
        "data": orjson.dumps(ddr_parse(jsonable_encoder(data)))
    }

@ws_action("dev_portal")
async def dev_portal(ws: WebSocket, data: dict):
    if Experiments.DevPortal not in ws.state.experiments:
        return {"resp": "spld", "e": SPLDEvent.missing_perms}

    user_connections = await app.state.db.fetch("SELECT client_id, expires_on FROM user_connections WHERE user_id = $1", int(ws.state.user["id"]))

    return {
        "connections": user_connections
    }

@ws_action("data_deletion")
async def data_deletion(ws: WebSocket, data: dict):
    user_id = data.get("user", None)

    if not ws.state.user:
        return {
            "detail": "You must be logged in first!"
        }

    if ws.state.member.perm < 7 and ws.state.user["id"] != user_id:
        return {
            "detail": "You must either have permission level 7 or greater or the user id requested must be the same as your logged in user id."
        }

    try:
        user_id = int(user_id)
    except:
        return {
            "detail": "Invalid User ID"
        }
    
    # Some sanity checks before allowing a DDR
    votes_check = await app.state.db.fetchrow("SELECT expires_on FROM user_vote_table WHERE user_id = $1", user_id)
    if votes_check and votes_check["expires_on"] > datetime.datetime.now():
        return {
            "detail": "You cannot delete data for a user who has a vote for a bot that has not expired yet. Please wait until all bot votes have expired before making a request"
        }

    votes_check = await app.state.db.fetchrow("SELECT expires_on FROM user_server_vote_table WHERE user_id = $1", user_id)
    if votes_check and votes_check["expires_on"] > datetime.datetime.now():
        return {
            "detail": "You cannot delete data for a user who has a vote for a server that has not expired yet. Please wait until all server votes have expired before making a request"
        }

    print("[LYNX] Wiping user info in db")
    await app.state.db.execute("DELETE FROM users WHERE user_id = $1", user_id)

    bots = await app.state.db.fetch(
        """SELECT DISTINCT bots.bot_id FROM bots 
        INNER JOIN bot_owner ON bot_owner.bot_id = bots.bot_id 
        WHERE bot_owner.owner = $1 AND bot_owner.main = true""",
        user_id,
    )
    for bot in bots:
        await app.state.db.execute("DELETE FROM bots WHERE bot_id = $1", bot["bot_id"])
        await app.state.db.execute("DELETE FROM vanity WHERE redirect = $1", bot["bot_id"])

    votes = await app.state.db.fetch(
        "SELECT bot_id from bot_voters WHERE user_id = $1", user_id)
    for vote in votes:
        await app.state.db.execute(
            "UPDATE bots SET votes = votes - 1 WHERE bot_id = $1",
            vote["bot_id"])

    await app.state.db.execute("DELETE FROM bot_voters WHERE user_id = $1", user_id)

    print("[LYNX] Clearing redis info on user...")
    await app.state.redis.hdel(str(user_id), "cache")
    await app.state.redis.hdel(str(user_id), "ws")

    await app.state.redis.close()

    return {
        "detail": "All found user data deleted"
    }

@ws_action("survey_list")
async def survey(ws: WebSocket, _):
    surveys = await app.state.db.fetch("SELECT id, title, questions FROM lynx_surveys")
    surveys_html = ""
    for survey in surveys:
        questions = orjson.loads(survey["questions"])

        if not isinstance(questions, list):
            continue

        questions_html = ''
        question_ids = []
        for question in questions:
            if not question.get("question") or not question.get("type") or not question.get("id") or not question.get("textarea"):
                continue
            questions_html += f"""
<div class="form-group">
<label id="{question["id"]}-label">{question["question"]}</label>
<{"input" if not question["textarea"] else "textarea"} class="form-control" placeholder="Minimum of 6 characters" minlength="6" required="true" aria-required="true" id="{question["id"]}" type="{question["type"]}" name="{question["id"]}"></{"input" if not question["textarea"] else "textarea"}>
</div>
            """
            question_ids.append(str(question["id"]))

        surveys_html += f"""
::: survey

### {survey["title"]}

{questions_html}

<button onclick="submitSurvey('{str(survey["id"])}', {question_ids})">Submit</button>

:::
    """

    return {"title": "Survey List", "pre": "/links", "data": surveys_html, "ext_script": "surveys"}

@ws_action("survey")
async def submit_survey(ws: WebSocket, data: dict):
    id = data.get("id", "0")
    answers = data.get("answers", {})

    questions = await app.state.db.fetchval("SELECT questions FROM lynx_surveys WHERE id = $1", id)
    if not questions:
        return {"detail": "Survey not found"}
    
    questions = orjson.loads(questions)

    if len(questions) != len(answers):
        return {"detail": "Invalid survey. Refresh and try again"}

    await app.state.db.execute(
        "INSERT INTO lynx_survey_responses (survey_id, questions, answers, user_id, username_cached) VALUES ($1, $2, $3, $4, $5)",
        id,
        orjson.dumps(questions).decode(),
        orjson.dumps(answers).decode(),
        int(ws.state.user["id"]) if ws.state.user else None,
        ws.state.user["username"] if ws.state.user else "Anonymous"
    )
    return {"detail": "Submitted survey"}

print(ws_action_dict)

async def do_task_and_send(f, ws, data):
    start_time = time.time()

    ret = await f(ws, data)

    if not ret:
        return

    if not ret.get("resp"):
        ret["resp"] = data.get("request", "")
    
    if ws.state.plat == "WEB":
        await js_log("Tawnypelt", f"Time taken for server handler: {(time.time() - start_time)*1000} ms", ws=ws)

    await manager.send_personal_message(ret, ws)

async def out_of_date(ws):
    await manager.connect(ws)
    await manager.send_personal_message({"resp": "spld", "e": SPLDEvent.out_of_date}, ws)
    await asyncio.sleep(0.3)
    await ws.close(4008)

async def unsupported(ws):
    await manager.send_personal_message({"resp": "spld", "e": SPLDEvent.unsupported}, ws)
    await asyncio.sleep(0.3)
    await ws.close(4008)

async def js_log(*log, ws):
    await manager.send_personal_message({"resp": "spld", "e": SPLDEvent.telemetry, "data": log}, ws)

def replace_if_web(msg, ws):
    if ws.state.plat == "WEB":
        return msg.replace("<", "&lt").replace(">", "&gt")
    return msg    

# Cli = client, plat = platform (WEB or SQUIRREL)
@app.websocket("/_ws")
async def ws(ws: WebSocket, cli: str, plat: str):
    if ws.headers.get("Origin") != "https://lynx.fateslist.xyz" and plat != "DOCREADER":
        print(f"Ignoring malicious websocket request with origin {ws.headers.get('Origin')}")
        return
    
    if plat not in ("WEB", "SQUIRREL", "DOCREADER"):
        print("Client out of date, invalid platform")

        ws.state.debug = False
        return await out_of_date(ws)
    
    if plat in ("SQUIRREL", "DOCREADER"):
        ws.state.debug = True # Squirrel and docreader doesnt support no-debug mode *yet*
    else:
        ws.state.debug = False
    
    ws.state.cli = cli
    ws.state.plat = plat

    try:
        cli, _time = cli.split("@")
    except:
        print("Client out of date, invalid cli")

        ws.state.debug = False
        return await out_of_date(ws)

    # Check nonce to ensure client is up to date
    if (ws.state.plat == "WEB" and cli != "Comfrey0s7"  # TODO, obfuscate/hide nonce in core.js and app.py
        or (ws.state.plat == "SQUIRREL" and cli != "BurdockRoot")
        or (ws.state.plat == "DOCREADER" and cli != "Quailfeather")
    ):
        print("Client out of date, nonce incorrect")

        ws.state.debug = False
        return await out_of_date(ws)
    
    if ws.state.plat in ("WEB", "DOCREADER"):
        if not _time.isdigit():
            print("Client out of date, nonce incorrect")

            ws.state.debug = False
            return await out_of_date(ws)
        elif time.time() - int(_time) > 20:
            print("Network connection too slow!")

            ws.state.debug = False
            return await out_of_date(ws)


    ws.state.user = None
    ws.state.member = StaffMember(name="Unknown", id=0, perm=-1, staff_id=0)
    ws.state.token = "Unknown"

    await manager.connect(ws)

    if ws.cookies.get("sunbeam-session:warriorcats") and ws.state.plat != "DOCREADER":
        print(f"WS Cookies: {ws.cookies}")
        try:
            sunbeam_user = orjson.loads(b64decode(ws.cookies.get("sunbeam-session:warriorcats")))
            data = await app.state.db.fetchrow(
                "SELECT api_token, staff_verify_code FROM users WHERE user_id = $1 AND api_token = $2",
                int(sunbeam_user["user"]["id"]),
                sunbeam_user["token"]
            )
            if not data:
                await ws.close(4008)
                return

            ws.state.token = data["api_token"]
            if not ws.state.token:
                await ws.close(4008)
                return

            ws.state.user = await fetch_user(int(sunbeam_user["user"]["id"]))

            _, _, ws.state.member = await is_staff(int(sunbeam_user["user"]["id"]), 2)
            ws.state.verified = True

            if not code_check(data["staff_verify_code"], int(sunbeam_user["user"]["id"])) and ws.state.member.perm >= 2:
                await manager.send_personal_message({"resp": "spld", "e": SPLDEvent.verify_needed}, ws)  # Request staff verify
                ws.state.verified = False

        except Exception as exc:
            # Let them stay unauthenticated
            print(exc)
            pass

    if ws.state.user:
        experiments = await app.state.db.fetchval("SELECT experiments FROM users WHERE user_id = $1", int(ws.state.user["id"]))   
    else:
        experiments = []

    default_exp = await app.state.db.fetchval("SELECT default_user_experiments FROM lynx_data")
    if not default_exp:
        default_exp = []
    
    for el in default_exp:
        if el not in experiments:
            experiments.append(el)

    print(f"Experiments: {experiments}")

    ws.state.experiments = experiments

    print(ws.state.experiments)

    if ws.state.plat in ("WEB", "DOCREADER"):
        docs = []

        for path in pathlib.Path("api-docs").rglob("*.md"):
            proper_path = str(path).replace("api-docs/", "")
            
            docs.append(proper_path.split("/"))

        await manager.send_personal_message({
            "resp": "cfg", 
            "assets": {
                "bot-actions": "75",
                "user-actions": "76",
                "surveys": "73",
                "apply": "81",
                "admin-nav": "m8",
                "admin-iframe": "m3823",
                "admin-console": "m37",
                "exp-rollout": "m3298",
            },
            "sidebar": [["login", "fa-arrow-right-to-bracket", "loginUser()"], ["status", "fa-gear"], ["privacy", "fa-shield"], ["surveys", "fa-shield"], ["staff-guide", "fa-rectangle-list"], ["apply-for-staff", "fa-rectangle-list"], ["links", "fa-link"]],
            "responses": ['docs', 'links', 'staff_guide', 'index', "request_logs", "reset_page", "staff_apps", "loa", "user_actions", "bot_actions", "staff_verify", "survey_list", "admin"],
            "actions": ['user_action', 'bot_action', 'eternatus', 'survey', 'data_deletion', 'apply_staff', 'send_loa', 'exp_rollout_add', 'exp_rollout_del', 'exp_rollout_all', 'exp_rollout_undo', 'exp_rollout_controlled'],
            "tree": docs,
            "experiments": ws.state.experiments
        }, ws)

        if ws.state.plat == "WEB":
            await manager.send_personal_message({"resp": "perms", "data": ws.state.member.dict()}, ws)
            await manager.send_personal_message({"resp": "user_info", "user": ws.state.user}, ws)

    try:
        if ws.state.plat == "WEB":
            # Start notifs
            asyncio.create_task(notifs(ws))

        while True:
            try:
                if ws.state.debug:
                    data = await ws.receive_json()
                else:
                    data = msgpack.unpackb(zlib.decompress(await ws.receive_bytes()))

                # Recompute user experiment list
                old_feature_list = ws.state.experiments
                if ws.state.user:
                    ws.state.experiments = await app.state.db.fetchval("SELECT experiments FROM users WHERE user_id = $1", int(ws.state.user["id"]))   
                else:
                    ws.state.experiments = []

                default_exp = await app.state.db.fetchval("SELECT default_user_experiments FROM lynx_data")
                if not default_exp:
                    default_exp = []
                
                for el in default_exp:
                    if el not in ws.state.experiments:
                        ws.state.experiments.append(el)

                if ws.state.experiments != old_feature_list:
                    await manager.send_personal_message({"resp": "experiments", "experiments": ws.state.experiments}, ws)

            except Exception as exc:
                if isinstance(exc, RuntimeError):
                    return
                print(f"{type(exc)}: {exc}")
                continue
        
            if ws.state.debug or data.get("request") not in ("notifs",):
                print(data)

            if ws.state.user is not None:
                # Check perms as this user is logged in
                check = await app.state.db.fetchrow(
                    "SELECT user_id, staff_verify_code FROM users WHERE user_id = $1 AND api_token = $2",
                    int(ws.state.user["id"]),
                    ws.state.token
                )
                if not check:
                    print("Invalid token")
                    await ws.close(code=1008)
                    return

                _, _, member = await is_staff(int(ws.state.user["id"]), 2)

                if ws.state.member.perm != member.perm:
                    ws.state.member = member
                    await manager.send_personal_message({"resp": "perms", "data": ws.state.member.dict()}, ws)

                if ws.state.verified and not code_check(check["staff_verify_code"], int(sunbeam_user["user"]["id"])):
                    ws.state.verified = False
            
            try:
                if ws.state.plat == "SQUIRREL" and data.get("request") not in ("bot_action", "user_action"):
                    print("[LYNX] Error: Unsupported squirrel action")
                    return await unsupported(ws)
                elif ws.state.plat == "DOCREADER" and data.get("request") not in ("docs",):
                    print("[LYNX] Error: Unsupported docreader action")
                    return await unsupported(ws)

                f = ws_action_dict.get(data.get("request"))
                if not f:
                    print(f"could not find {data}")
                    await manager.send_personal_message({"resp": "spld", "e": SPLDEvent.not_found}, ws)
                else:
                    asyncio.create_task(do_task_and_send(f, ws, data))
            except Exception as exc:
                print(exc)

    except WebSocketDisconnect:
        manager.disconnect(ws)


class UserActionWithReason(BaseModel):
    user_id: str
    initiator: int | None = None
    reason: str
    context: Any | None = None


app.state.user_actions = {}


def user_action(
        name: str,
        states: list[enums.UserState],
        min_perm: int = 2,
):
    async def state_check(bot_id: int):
        user_state = await app.state.db.fetchval("SELECT state FROM users WHERE user_id = $1", bot_id)
        return (user_state in states) or len(states) == 0

    async def _core(ws: WebSocket, data: UserActionWithReason):
        if ws.state.member.perm < min_perm:
            return {
                "detail": f"PermError: {min_perm=}, {ws.state.member.perm=}"
            }
        
        data.initiator = int(ws.state.user["id"])

        if not data.user_id.isdigit():
            return {
                "detail": "User ID is invalid"
            }

        data.user_id = int(data.user_id)

        if not await state_check(data.user_id):
            return {
                "detail": replace_if_web(f"User state check error: {states=}", ws)
            }

    def decorator(function):
        async def wrapper(ws, data: UserActionWithReason):
            if _data := await _core(ws, data):
                return _data # Exit if true, we've already sent
            if len(data.reason) < 5:
                return {
                    "detail": "Reason must be more than 5 characters"
                }
            res = await function(data)
            res = jsonable_encoder(res)
            res["resp"] = "user_action"

            err = res.get("err", False)

            if not err:
                spl = res.get("spl", True)

                if spl:
                    # Tell client that a refresh is needed as a user action has taken place
                    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/user-actions"})


            return res

        app.state.user_actions[name] = wrapper
        return wrapper

    return decorator


### Client should lie here and give a generic reason for add_staff

@user_action("add_staff", [enums.UserState.normal], min_perm=5)
async def add_staff(data: UserActionWithReason):
    await add_role(main_server, data.user_id, staff_roles["community_staff"]["id"], "New staff member")
    await add_role(main_server, data.user_id, staff_roles["bot_reviewer"]["id"], "New staff member")

    # Check if DMable by attempting to send a message
    async with aiohttp.ClientSession() as sess:
        async with sess.post(
                "https://discord.com/api/v10/users/@me/channels",
                json={"recipient_id": str(data.user_id)},
                headers={"Authorization": f"Bot {main_bot_token}"}) as res:
            if res.status != 200:
                json = await res.json()
                return {
                    "detail": f"User is not DMable {json}",
                    "err": True
                }
            json = await res.json()
            channel_id = json["id"]

        embed = Embed(
            color=0xe74c3c,
            title="Staff Application Accepted",
            description=f"You have been accepted into the Fates List Staff Team!",
        )

        res = await send_message({
            "channel_id": channel_id,
            "embed": embed,
            "content": """
Please join our staff server first of all: https://fateslist.xyz/staffserver/invite

Then head on over to https://lynx.fateslist.xyz to read our staff guide and get started!
            """
        })

        if not res.ok:
            return {
                "detail": f"Failed to send message (possibly blocked): {res.status}",
                "err": True
            }
        
    await app.state.db.execute("UPDATE users SET flags = array_remove(flags, $1) WHERE user_id = $2", enums.UserFlag.Staff, data.user_id)
    await app.state.db.execute("UPDATE users SET flags = array_append(flags, $1) WHERE user_id = $2", enums.UserFlag.Staff, data.user_id)

    return {"detail": "Successfully added staff member"}

@user_action("remove_staff", [], min_perm=5)
async def remove_staff_member(data: UserActionWithReason):
    for role in staff_roles.keys():
        await del_role(main_server, data.user_id, staff_roles[role]["id"], data.reason)
    await app.state.db.execute("UPDATE users SET flags = array_remove(flags, $1) WHERE user_id = $2", enums.UserFlag.Staff, data.user_id)

    embed = Embed(
        url=f"https://fateslist.xyz/profile/{data.user_id}",
        color=0xe74c3c,
        title="User Demoted",
        description=f"<@{data.initiator}> has demoted <@{data.user_id}>.\n\n We are sorry, but we had to do this.",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.user_id}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully removed staff member"}

### Client should lie here and give a generic reason for ack_staff_app

@user_action("ack_staff_app", [], min_perm=4)
async def ack_staff_app(data: UserActionWithReason):
    await app.state.db.execute("DELETE FROM lynx_apps WHERE user_id = $1", data.user_id)
    # Special broadcast for Acking
    await manager.broadcast({"resp": "spld", "e": SPLDEvent.refresh_needed, "loc": "/staff-apps"})
    return {"detail": "Acked", "spl": False}


@user_action("set_user_state", [], min_perm=4)
async def set_user_state(data: UserActionWithReason):
    if not isinstance(data.context, int):
        return {"detail": "State must be an integer", "err": True}
    try:
        state = enums.UserState(data.context)
    except:
        return {"detail": "State must be of enum UserState", "err": True}

    await app.state.db.fetchval("UPDATE users SET state = $1 WHERE user_id = $2", state, data.user_id)

    embed = Embed(
        url=f"https://fateslist.xyz/profile/{data.user_id}",
        color=0xe74c3c,
        title="User State Updated",
        description=f"<@{data.initiator}> has modified the state of <@{data.user_id}> with new state of {state.name} ({state.value})!\n\nThank you for using Fates List and we are sorry for any inconveniences caused :heart:",
    )

    embed.add_field(name="Reason", value=data.reason)

    await send_message({"content": f"<@{data.user_id}>", "embed": embed, "channel_id": bot_logs})

    return {"detail": "Successfully set user state"}

@user_action("mod_staff_flag", [], min_perm=2)
async def set_flags(data: UserActionWithReason):
    if data.context:
        await app.state.db.execute("UPDATE users SET flags = array_remove(flags, $1) WHERE user_id = $2", enums.UserFlag.Staff, data.initiator)
        await app.state.db.execute("UPDATE users SET flags = array_append(flags, $1) WHERE user_id = $2", enums.UserFlag.Staff, data.initiator)
    else:
        await app.state.db.execute("UPDATE users SET flags = array_remove(flags, $1) WHERE user_id = $2", enums.UserFlag.Staff, data.initiator)
    return {"detail": "Successfully set staff flag"}

print(app.state.user_actions)
print(app.state.bot_actions)


@app.on_event("startup")
async def startup():
    signal.signal(signal.SIGINT, handle_kill)
    engine = engine_finder()
    app.state.engine = engine
    app.state.redis = aioredis.from_url("redis://localhost:1001", db=1)
    app.state.db = await asyncpg.create_pool()
    app.state.discord = discord.Client(intents=discord.Intents(guilds=True, members=True))
    asyncio.create_task(app.state.discord.start(main_bot_token))
    await engine.start_connection_pool()


def handle_kill(*args, **kwargs):
    async def _close():
        await asyncio.sleep(0)
        await manager.broadcast({"resp": "spld", "e": SPLDEvent.maint})
        await asyncio.sleep(0)
        await app.state.engine.close_connection_pool()

    def _gohome(_):
        task.cancel()
        sys.exit(0)

    print("Broadcasting maintenance")
    task = asyncio.create_task(_close())
    task.add_done_callback(_gohome)

# Widget Server

# Load in static assets for bot widgets
static_assets = {}
fl_path = (os.environ.get("HOME") or "/home/meow") + "/FatesList"
with open(f"{fl_path}/data/static/botlisticon.webp", mode="rb") as res:
    static_assets["fates_img"] = io.BytesIO(res.read())

with open(f"{fl_path}/data/static/votes.png", mode="rb") as res:
    static_assets["votes_img"] = io.BytesIO(res.read())

with open(f"{fl_path}/data/static/server.png", mode="rb") as res:
    static_assets["server_img"] = io.BytesIO(res.read())

static_assets["fates_pil"] = Image.open(static_assets["fates_img"]).resize(
    (10, 10))
static_assets["votes_pil"] = Image.open(static_assets["votes_img"]).resize(
    (15, 15))
static_assets["server_pil"] = Image.open(
    static_assets["server_img"]).resize((15, 15))

def is_color_like(c):
    try:
        # Converting 'deep sky blue' to 'deepskyblue'
        color = c.replace(" ", "")
        Color(color)
        # if everything goes fine then return True
        return True
    except ValueError: # The color code was not found
        return False 

def human_format(num: int) -> str:
    if abs(num) < 1000:
        return str(abs(num))
    formatter = '{:.3g}'
    num = float(formatter.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        if magnitude == 31:
            num /= 10
        num /= 1000.0
    return '{} {}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T', "Quad.", "Quint.", "Sext.", "Sept.", "Oct.", "Non.", "Dec.", "Tre.", "Quat.", "quindec.", "Sexdec.", "Octodec.", "Novemdec.", "Vigint.", "Duovig.", "Trevig.", "Quattuorvig.", "Quinvig.", "Sexvig.", "Septenvig.", "Octovig.", "Nonvig.", "Trigin.", "Untrig.", "Duotrig.", "Googol."][magnitude])

# Convert hexcode to rgb for pillow
def hex_to_rgb(value):
    value = value.lstrip('H')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

env = Environment(
    loader=FileSystemLoader(searchpath="."),
    autoescape=select_autoescape(),
    enable_async=True,
).get_template("widgets.html", globals={"human_format": human_format})

@app.get("/widgets/{target_id}", operation_id="get_widget")
async def get_widget(
    request: Request, 
    response: Response,
    target_id: int, 
    target_type: enums.WidgetType, 
    format: enums.WidgetFormat,
    bgcolor: str  = 'black', 
    textcolor: str ='white', 
    no_cache: bool | None = False, 
    cd: str | None = None, 
    desc_length: int = 25
):
    """
Returns a widget

**For colors (bgcolor, textcolor), use H for html hex instead of #.\nExample: H123456**

- cd - A custom description you wish to set for the widget

- desc_length - Set this to anything less than 0 to try and use full length (may 500), otherwise this sets the length of description to use.

**Using 0 for desc_length will disable description**

no_cache - If this is set to true, cache will not be used but will still be updated. If using cd, set this option to true and cache the image yourself
Note that no_cache is slow and may lead to ratelimits and/or your got being banned if used excessively
    """
    if not bgcolor:
        bgcolor = "black"
    elif not textcolor:
        textcolor = "black"

    # HTML shouldn't have any changes to bgcolor
    if format != enums.WidgetFormat.html:
        if bgcolor.startswith("H"):
            # Hex code starting with H, make it rgb
            bgcolor = hex_to_rgb(bgcolor)
        else:
            # Converting 'deep sky blue' to 'deepskyblue'
            if not is_color_like(str(bgcolor)):
                return ORJSONResponse({"detail": "Invalid bgcolor"})
            if isinstance(bgcolor, str):
                bgcolor=bgcolor.split('.')[0]
                bgcolor = math.floor(int(bgcolor)) if bgcolor.isdigit() or bgcolor.isdecimal() else bgcolor
        
        # HTML shouldn't have any changes to textcolor
        if textcolor.startswith("H"):
            textcolor = hex_to_rgb(textcolor)
        else:
            if not is_color_like(str(textcolor)):
                return ORJSONResponse({"detail": "Invalid textcolor"})
            if isinstance(textcolor, str):
                textcolor=textcolor.split('.')[0]
                textcolor = math.floor(int(textcolor)) if textcolor.isdigit() or textcolor.isdecimal() else textcolor
    
    cache_key = f"widget-{target_id}-{target_type}-{format.name}-{textcolor}-{bgcolor}-{desc_length}"
    response.headers["ETag"] = f"W/{cache_key}"

    db = app.state.db
    redis = app.state.redis
   
    if target_type == enums.WidgetType.bot:
        col = "bot_id"
        table = "bots"
    else:
        col = "guild_id"
        table = "servers"

    bot = await db.fetchrow(f"SELECT guild_count, votes, description FROM {table} WHERE {col} = $1", target_id)
    if not bot:
        raise HTTPException(status_code=404)
    
    bot = dict(bot)
    
    if target_type == enums.WidgetType.bot:
        data = {"bot": bot, "user": await fetch_user(str(target_id))}
    else:
        data = {"bot": bot, "user": await db.fetchrow("SELECT name_cached AS username, avatar_cached AS avatar FROM servers WHERE guild_id = $1", target_id)}
    bot_obj = data["user"]
    
    if not bot_obj:
        raise HTTPException(status_code=404)

    if format == enums.WidgetFormat.json:
        return data

    if format == enums.WidgetFormat.html:
        rendered = await env.render_async(**{"textcolor": textcolor, "bgcolor": bgcolor, "id": target_id, "type": target_type.name} | data)
        return HTMLResponse(rendered)

    if format in (enums.WidgetFormat.png, enums.WidgetFormat.webp):
        # Check if in cache
        cache = await redis.get(cache_key)
        if cache and not no_cache:
            def _stream():
                with io.BytesIO(cache) as output:
                    yield from output

            return StreamingResponse(_stream(), media_type=f"image/{format.name}")

        widget_img = Image.new("RGBA", (300, 175), bgcolor)
        async with aiohttp.ClientSession() as sess:
            async with sess.get(data["user"]["avatar"]) as res:
                avatar_img = await res.read()

        fates_pil = static_assets["fates_pil"]
        votes_pil = static_assets["votes_pil"]
        server_pil = static_assets["server_pil"]
        avatar_pil = Image.open(io.BytesIO(avatar_img)).resize((100, 100))
        avatar_pil_bg = Image.new('RGBA', avatar_pil.size, (0,0,0))
        
        #pasting the bot image
        try:
            widget_img.paste(Image.alpha_composite(avatar_pil_bg, avatar_pil),(10,widget_img.size[-1]//5))
        except:
            widget_img.paste(avatar_pil,(10,widget_img.size[-1]//5))
        
        def remove_transparency(im, bgcolor):
            if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
                alpha = im.convert('RGBA').split()[-1]
    
                # Create a new background image of our matt color.
                # Must be RGBA because paste requires both images have the same format
                # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
                bg = Image.new("RGBA", im.size, bgcolor)
                bg.paste(im, mask=alpha)
                return bg
            return im
        widget_img.paste(remove_transparency(fates_pil, bgcolor), (10,152))
    
        #pasting servers logo
        widget_img.paste(server_pil, (120, 95) if desc_length != 0 else (120, 30))

        #pasting votes logo
        widget_img.paste(votes_pil, (120, 115) if desc_length != 0 else (120, 50))
    
        font = os.path.join(f"{fl_path}/data/static/LexendDeca-Regular.ttf")

        def get_font(string: str, d):
            return ImageFont.truetype(
                font,
                get_font_size(d.textsize(string)[0]),
                layout_engine=ImageFont.LAYOUT_RAQM
            )
    
        def get_font_size(width: int):
            if width <= 90:
                return 18  
            if width >= 192:
                return 10
            if width == 168:
                return 12
            return 168-width-90
        
        def the_area(str_width: int, image_width: int):
            if str_width < 191:
                new_width=abs(int(str_width-image_width))
                return (new_width//2.5)
            new_width=abs(int(str_width-image_width))
            return (new_width//4.5)
         
            #lists name
        d = ImageDraw.Draw(widget_img)
        d.text(
            (25,150), 
            'Fates List', 
            fill=textcolor,
            font=ImageFont.truetype(
                font,
                10,
                layout_engine=ImageFont.LAYOUT_RAQM
            )
        )

        #Bot name
        d.text(
            (
                the_area(
                    d.textsize(str(bot_obj['username'].encode('latin-1', 'replace').decode('latin-1')))[0],
                    widget_img.size[0]),
            5), 
            str(bot_obj['username']), 
            fill=textcolor,
            font=ImageFont.truetype(
                font,
                16,
                layout_engine=ImageFont.LAYOUT_RAQM)
            )
    
        bot["description"] = bot["description"].encode("ascii", "ignore").decode()

        # description
        if desc_length != 0: 
            wrapper = textwrap.TextWrapper(width=15)
            text = cd or (bot["description"][:desc_length] if desc_length > 0 else bot["description"])
            word_list = wrapper.wrap(text=str(text))
            d.text(
                (120,30), 
                str("\n".join(word_list)), 
                fill=textcolor,
                font=get_font(str("\n".join(word_list)),d)
            )
    
        #server count
        d.text(
            (140,94) if desc_length != 0 else (140,30), 
            human_format(bot["guild_count"]), 
            fill=textcolor,
            font=get_font(human_format(bot["guild_count"]),d)
        )
    
        #votes
        d.text(
            (140,114) if desc_length != 0 else (140,50),
            human_format(bot["votes"]), 
            fill=textcolor,
            font=get_font(human_format(bot['votes']),d)
        )
        
        output = io.BytesIO()
        widget_img.save(output, format=format.name.upper())
        output.seek(0)
        await redis.set(cache_key, output.read(), ex=60*3)
        output.seek(0)

        def _stream():    
            yield from output
            output.close()

        return StreamingResponse(_stream(), media_type=f"image/{format.name}")

# Metro Code
class Metro(BaseModel):
    bot_id: str
    reviewer: str
    username: str
    description: str
    long_description: str
    nsfw: bool
    tags: list[str]
    owner: str
    reason: str | None = "STUB_REASON"
    extra_owners: list[str]
    website: str | None = None
    github: str | None = None # May be added later
    support: str | None = None
    donate: str | None = None
    library: str | None = None
    prefix: str | None = None
    invite: str | None = None
    cross_add: bool | None = True

class FakeWsState():
    def __init__(self):
        self.plat = "SQUIRREL"
        self.user = None
        self.memebr = None

class FakeWs():
    def __init__(self, reviewer: str):
        self.state = FakeWsState()
        self.state.user = {"id": reviewer, "username": "Unknown User"}
        self.state.member = StaffMember(name="Reviewer (Metro)", id="0", perm=2, staff_id="0")

# We use widgets here because its already proxied to the client
@app.post("/widgets/_admin/metro", include_in_schema=False)
async def metro_api(request: Request, action: str, data: Metro):
    if request.headers.get("Authorization") != metro_key:
        return {"detail": "Invalid key"}

    if action not in ("claim", "unclaim", "approve", "deny"):
        return {"detail": "Action does not exist!"}

    data.bot_id = int(data.bot_id)

    if action == "approve" and data.cross_add:
        bot = await app.state.db.fetchrow("SELECT bot_id FROM bots WHERE bot_id = $1", data.bot_id)
        if not bot:
            # Insert bot
            await app.state.db.execute(
                "INSERT INTO bots (id, bot_id, bot_library, description, long_description, long_description_type, api_token, invite, website, discord, prefix, state) VALUES ($1, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)", 
                data.bot_id,
                data.library or "custom",
                data.description,
                data.long_description,
                enums.LongDescType.markdown_serverside,
                get_token(128),
                data.invite or '',
                data.website,
                data.support,
                data.prefix,
                enums.BotState.under_review
            )
            for tag in data.tags:
                try:
                    await app.state.db.execute("INSERT INTO bot_tags (bot_id, tag) VALUES ($1, $2)", data.bot_id, tag.lower())
                except:
                    pass
            await app.state.db.execute("INSERT INTO bot_tags (bot_id, tag) VALUES ($1, $2)", data.bot_id, "utility")

            # Insert bot owner
            await app.state.db.execute("INSERT INTO bot_owner (bot_id, owner, main) VALUES ($1, $2, true)", data.bot_id, int(data.owner))

            for owner in data.extra_owners:
                await app.state.db.execute("INSERT INTO bot_owner (bot_id, owner) VALUES ($1, $2)", data.bot_id, int(owner))

            await app.state.db.execute("INSERT INTO vanity (redirect, type, vanity_url) VALUES ($1, 1, $2)", data.bot_id, get_token(32))

    try:
        action = app.state.bot_actions[action]
    except:
        return {"detail": "Action does not exist!"}
    try:
        action_data = ActionWithReason(bot_id=data.bot_id, reason=data.reason)
    except Exception as exc:
        return {"detail": f"{type(exc)}: {str(exc)}"}
    return await action(FakeWs(data.reviewer), action_data)

# End of metro code



app.add_middleware(CustomHeaderMiddleware)
