import pathlib
import sys
import io
import os
import textwrap
import asyncio
import datetime
import hashlib
import time
from http import HTTPStatus
from typing import Any, Union
import enum
import secrets
import string
import math
import uuid

from base64 import urlsafe_b64encode

import asyncpg
import discord
import orjson
import requests
from dateutil import parser
from pydantic import BaseModel
import enums

import aiohttp
import aioredis
import orjson
from discord import Embed
from fastapi import FastAPI, WebSocket, HTTPException, Request, Response, APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse, ORJSONResponse, PlainTextResponse
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
from experiments import Experiments, exp_props
import jwt
import pyotp

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
    file = orjson.loads(file)
    main_bot_token = file["token_main"]
    metro_key = file["metro_key"]
    supabase_token = file["supabase_token"]
    supabase_jwt_key = file["supabase_jwt_key"]

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
    if request.cookies.get("lynx-session"):
        session = await app.state.redis.get(request.cookies['lynx-session'])
        if session:
            request.scope["sunbeam_user"] = orjson.loads(session)
        else:
            request.scope["sunbeam_user"] = {
                "id": "0",
                "token": "0",
            }

        request.scope["sunbeam_user"]["user"] = {
            "id": request.scope["sunbeam_user"]["id"],
        }

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
        
        if request.method == "OPTIONS":
            if request.headers.get("Origin", "").endswith("fateslist.xyz") or request.headers.get("Origin", "").endswith("selectthegang-fates-list-sunbeam-x5w7vwgvvh96j5-5000.githubpreview.dev"):
                return PlainTextResponse("", headers={
                    "Access-Control-Allow-Origin": request.headers.get("Origin"),
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, Frostpaw-ID, Frostpaw-MFA, BristlefrostXRootspringXShadowsight, X-Cloudflare-For, Alert-Law-Enforcement",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                })

        if not (request.url.path.startswith("/_admin") and (request.url.path not in ("/_admin", "/_admin/") and not request.url.path.endswith((".css", ".js", ".js.map")))):
            response = await call_next(request)
            if request.headers.get("Origin", "").endswith("fateslist.xyz") or request.headers.get("Origin", "").endswith("selectthegang-fates-list-sunbeam-x5w7vwgvvh96j5-5000.githubpreview.dev"):
                response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin")
            return response

        print("[LYNX] Admin request. Middleware started")

        await auth_user_cookies(request)

        if not request.scope.get("sunbeam_user"):
            return ORJSONResponse({"detail": "Invalid nonce"}, status_code=400)

        member: StaffMember = request.state.member
        perm = member.perm

        # Before erroring, ensure they are perm of at least 2 and have no staff_verify_code set
        if member.perm < 2: 
            return ORJSONResponse({"detail": "Not staff"}, status_code=400)
        elif not request.state.is_verified:
            return ORJSONResponse({"detail": "Not staff verified"}, status_code=400)

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

private = APIRouter(include_in_schema=False)

public = APIRouter(include_in_schema=True)

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
                "detail": f"Bot state check error: {states=}"
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
    return {"detail": "Successfully claimed bot!", "ok": True}


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
    return {"detail": "Successfully unclaimed bot", "ok": True}


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

    return {"detail": "Successfully approved bot", "guild_id": str(main_server), "bot_id": str(data.bot_id), "ok": True}


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

    return {"detail": "Successfully denied bot", "ok": True}


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

    return {"detail": "Successfully banned bot", "ok": True}


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

    return {"detail": "Successfully unbanned bot", "ok": True}


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

    return {"detail": "Successfully certified bot", "ok": True}


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

    return {"detail": "Successfully uncertified bot", "ok": True}


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

    return {"detail": "Successfully unverified bot", "ok": True}


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

    return {"detail": "Successfully requeued bot", "ok": True}


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

    return {"detail": "Successfully reset bot votes", "ok": True}

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

    return {"detail": "Successfully reset all bot votes", "ok": True}


@action("set-flag", [], min_perm=3)
async def set_flag(request: Request, data: ActionWithReason):
    try:
        data.context = int(data.context)
    except ValueError:
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

    return {"detail": "Successfully set flag", "ok": True}


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

    return {"detail": "Successfully unset flag", "ok": True}

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

    return {"detail": f"Pushed controlled roll out to {data['limit']} users"}

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
                "detail": f"User state check error: {states=}"
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
    engine = engine_finder()
    app.state.engine = engine
    app.state.redis = aioredis.from_url("redis://localhost:1001", db=1)
    app.state.db = await asyncpg.create_pool()
    app.state.discord = discord.Client(intents=discord.Intents(guilds=True, members=True))
    asyncio.create_task(app.state.discord.start(main_bot_token))
    await engine.start_connection_pool()

    # Do db sanity check
    bots = await app.state.db.fetch("SELECT bot_id FROM bots")
    for bot in bots:
        owner = await app.state.db.fetch("SELECT bot_id FROM bot_owner WHERE bot_id = $1 AND main = true", bot["bot_id"])
        if not owner:
            print(f"DB ERROR: {bot}")

# Quailfeather API
class Loa(BaseModel):
    reason: str
    duration: str

@private.get("/_quailfeather/ap-login", tags=["Internal"])
async def ap_login(nonce: str):
    nonce_info = await app.state.redis.get(nonce)
    if not nonce_info:
        return PlainTextResponse("Invalid nonce")
    return HTMLResponse("""
<meta http-equiv = "refresh" content = "2; url = /_admin" />
<a href = "/_admin">Redirecting to admin panel...</a>
    """, headers={
        "Set-Cookie": f"lynx-session={nonce}; SameSite=Strict; Secure; HttpOnly; Path=/",
    })

@private.get("/_quailfeather/nonce", tags=["Internal"])
async def get_otp(request: Request):
    if auth := await _auth(request, request.headers.get("Frostpaw-ID", "")):
        return auth

    if request.state.member.perm < 2:
        return ORJSONResponse({"reason": "You are not staff"}, status_code=400)

    if not request.state.is_verified:
        return ORJSONResponse({
            "staff_verify": True
        }, status_code=400)
    
    nonce = get_token(512)

    await app.state.redis.set(nonce, orjson.dumps({
        "token": request.headers["Authorization"],
        "id": int(request.headers["Frostpaw-ID"]),
    }), ex=60*15)

    return {"nonce": nonce}

@private.post("/_quailfeather/staff-apps", tags=["Internal"])
async def staff_apps(request: Request, user_id: int):
    if auth := await _auth(request, user_id):
        return auth
    
    data = await request.json()

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
        user_id,
        orjson.dumps(jsonable_encoder(staffapps.questions)).decode(),
        orjson.dumps(data["answers"]).decode(),
        3
    )

    return {"detail": "Successfully applied for staff!"}


@private.get("/_quailfeather/staff-apps/questions", tags=["Internal"])
def get_staff_apps():
    return {"questions": jsonable_encoder(staffapps.questions), "can_apply": staffapps.can_apply}

@private.get("/_quailfeather/staff-apps", tags=["Internal"])
async def get_staff_apps(request: Request, user_id: int):
    if auth := await _auth(request, user_id):
        return auth

    if request.state.member.perm < 2:
        # Get only users apps
        staff_apps = await app.state.db.fetch(
            "SELECT user_id, app_id, questions, answers, created_at FROM lynx_apps ORDER BY created_at DESC WHERE user_id = $1", user_id)
    else:
        staff_apps = await app.state.db.fetch(
            "SELECT user_id, app_id, questions, answers, created_at FROM lynx_apps ORDER BY created_at DESC")

    apps = []

    for staff_app in staff_apps:
        user = await fetch_user(staff_app['user_id'])

        questions = orjson.loads(staff_app["questions"])
        answers = orjson.loads(staff_app["answers"])
    
        apps.append({
            "user": user,
            "questions": questions,
            "answers": answers,
        })
    
    return apps


@private.post("/_quailfeather/reset", tags=["Internal"])
async def reset_creds(request: Request, user_id: int):
    if auth := await _auth(request, user_id):
        return auth

    await app.state.db.execute(
        "UPDATE users SET api_token = $1, staff_verify_code = NULL WHERE user_id = $2",
        get_token(132),
        user_id
    )
    await app.state.db.execute(
        "DELETE FROM piccolo_user WHERE username = $1",
        (await fetch_user(user_id))["username"]
    )
    return {}

@private.post("/_quailfeather/loa", tags=["Internal"])
async def send_loa(request: Request, user_id: int, loa: Loa):
    if auth := await _auth(request, user_id):
        return auth

    if request.state.member.perm < 2:
        return ORJSONResponse({"reason": "You are not staff"}, status_code=400)
    try:
        date = parser.parse(loa.duration)
    except:
        return {"reason": "You did not fill out the form correctly"}
    if date.year - datetime.datetime.now().year not in (0, 1):
        return {"reason": "Duration must be in within this year"}

    await app.state.db.execute(
        "INSERT INTO leave_of_absence (user_id, reason, estimated_time, start_date) VALUES ($1, $2, $3, $4)",
        user_id,
        loa.reason,
        date - datetime.datetime.now(),
        datetime.datetime.now(),
    )

    return {"reason": "Submitted LOA successfully"}


@private.post("/_quailfeather/staff-verify", tags=["Internal"])
async def staff_verify(request: Request, user_id: int, code: str):
    if auth := await _auth(request, user_id):
        return auth
    
    if request.state.is_verified:
        return ORJSONResponse({
            "reason": "You are already verified"
        }, status_code=400)

    if not code_check(code, user_id):
        return ORJSONResponse({"reason": "Invalid code"}, status_code=400)
    else:
        username = (await fetch_user(user_id))["username"]
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
            return ORJSONResponse({"reason": "Failed to create user on lynx. Please contact Rootspring#6701"}, status_code=400)

        hashed_pwd = hashlib.blake2b(password.encode()).hexdigest()

        await app.state.db.execute(
            "UPDATE users SET staff_verify_code = $1, staff_password = $2 WHERE user_id = $3",
            code,
            hashed_pwd,
            user_id,
        )

        await add_role(staff_server, user_id, access_granted_role, "Access granted to server")
        await add_role(staff_server, user_id, request.state.member.staff_id, "Gets corresponding staff role")

        totp_key = pyotp.random_base32()

        await app.state.db.execute(
            "UPDATE users SET totp_shared_key = $1 WHERE user_id = $2",
            totp_key,
            user_id,
        )

        return {"reason": "Successfully verified staff member", "pass": password, "totp_key": totp_key}


@private.get("/_quailfeather/requests", tags=["Internal"])
async def request_log():
    return await app.state.db.fetch("SELECT user_id, method, url, status_code, request_time from lynx_logs")

@private.get("/_quailfeather/doctree", tags=["Internal"], deprecated=True)
def doctree():
    docs = []

    for path in pathlib.Path("api-docs").rglob("*.md"):
        proper_path = str(path).replace("api-docs/", "")
        
        docs.append(proper_path.split("/"))
    
    # We are forced to inject a script to the end to force hljs render
    return docs

@private.get("/_quailfeather/docs/{page:path}", tags=["Internal"], deprecated=True)
def docs(page: str):
    if page.endswith(".md"):
        page = f"/docs/{page[:-3]}"

    elif not page or page == "/docs":
        page = "/index"

    if not page.replace("-", "").replace("_", "").replace("/", "").replace("!", "").isalnum():
        return ORJSONResponse({"detail": "Invalid page"}, status_code=404)

    try:
        with open(f"api-docs/{page}.md", "r") as f:
            md_data = f.read()
    except FileNotFoundError as exc:
        return ORJSONResponse({"detail": f"api-docs/{page}.md not found -> {exc}"}, status_code=404)
    
    try:
        with open(f"api-docs/{page}.js", "r") as f:
            js = f.read()
    except FileNotFoundError as exc:
        js = ""
    
    return {"data": md_data, "js": js}

class BotData(BaseModel):
    id: str
    user_id: str
    action: str
    reason: str
    context: Any

class Feedback(BaseModel):
    feedback: str
    user_id: str
    page: str

# To remove (one day)
class FakeWsState():
    def __init__(self):
        self.plat = "SQUIRREL"
        self.user = None
        self.memebr = None

class FakeWsKitty():
    def __init__(self, reviewer: str, member: StaffMember):
        self.state = FakeWsState()
        self.state.user = {"id": reviewer, "username": "Unknown User"}
        self.state.member = member

async def _auth(request: Request, user_id: int | str) -> ORJSONResponse:
    try:
        user_id = int(user_id)
    except:
        return ORJSONResponse({"reason": "user_id invalid"}, status_code=401)

    # If moved to official api-v3, ensure a check for starts_with Frostpaw. is made to block custom clients
    check = await app.state.db.fetchval(
        "SELECT user_id FROM users WHERE user_id = $1 AND api_token = $2",
        user_id,
        request.headers.get("Authorization", "INVALID_AUTH")
    )
    if not check:
        return ORJSONResponse({"reason": "Unauthorized"}, status_code=401)

    staff_verify_code = await app.state.db.fetchval(
        "SELECT staff_verify_code FROM users WHERE user_id = $1",
        user_id
    )

    request.state.is_verified = True

    if not staff_verify_code or not code_check(staff_verify_code, user_id):
        request.state.is_verified = False
    
    _, _, request.state.member = await is_staff(user_id, 2)


class DataAction(enums.Enum):
    request = "request"
    delete = "delete"

@private.get("/_quailfeather/data", tags=["Internal"], deprecated=True)
async def data_request_delete(request: Request, requested_id: int, origin_user_id: int, act: DataAction):
    if auth := await _auth(request, origin_user_id):
        return auth

    if origin_user_id != requested_id:
        if request.state.is_verified:
            return {"detail": "You are not verified"}
        member = request.state.member

        if isinstance(member, ORJSONResponse):
            return member

        if member.perm < 7:
            return ORJSONResponse({
                "reason": "You must either have permission level 7 or greater or the user id requested must be the same as your logged in user id."
            }, status_code=400)
    
    try:
        user_id = int(requested_id)
    except:
        return ORJSONResponse({
            "reason": "Invalid User ID"
        }, status_code=400)

    if act == DataAction.request:
        id = str(uuid.uuid4())

        long_running_tasks[id] = {"detail": "still_running"}

        async def _task_run():
            long_running_tasks[id] = await request_data_task(user_id)
        
        asyncio.create_task(_task_run())

        return {
            "task_id": id,
        }
    else:
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

long_running_tasks = {}

@private.get("/_quailfeather/long-running/{tid}", tags=["Internal"], deprecated=True)
async def long_running(tid: uuid.UUID):
    tid = str(tid)
    print(f"Long running task {long_running_tasks.keys()}")
    id = long_running_tasks.get(tid)
    if id:
        if isinstance(id, dict) and id.get("detail") == "still_running":
            return ORJSONResponse({"detail": "Task still running"}, status_code=404)
        long_running_tasks.pop(tid)
        return id
    return ORJSONResponse({"detail": "Task not found"}, status_code=404)

async def request_data_task(user_id: int):
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

    return ddr_parse(jsonable_encoder(data))

@private.post("/_quailfeather/eternatus", tags=["Internal"], deprecated=True)
async def post_feedback(request: Request, data: Feedback):
    if data.user_id:
        if auth := await _auth(request, data.user_id):
            return auth
        
        user_id = int(data.user_id)
        username = (await fetch_user(user_id))["username"]
    else:
        user_id = None
        username = "Anonymous"


    if len(data.feedback.replace(" ", "").replace("\n", "").replace("\r", "")) < 5:
        return ORJSONResponse({"reason": "Feedback must be greater than 10 characters long!"}, status_code=400)

    if not data.page.startswith("/"):
        return ORJSONResponse({"reason": "Unexpected page!"}, status_code=400)

    await app.state.db.execute(
        "INSERT INTO lynx_ratings (feedback, page, username_cached, user_id) VALUES ($1, $2, $3, $4)",
        data.feedback,
        data.page,
        username,
        user_id
    )

    return {}

@private.get("/_quailfeather/dhs-trip")
async def redress_user(request: Request, no_fly_list: int):
    """Returns supabase secret"""

    if request.headers.get("BristlefrostXRootspringXShadowsight") != "cicada3301" or request.headers.get("X-Cloudflare-For") != "false":
        await app.state.db.execute("UPDATE users SET api_token = $1 WHERE user_id = $2", get_token(128), no_fly_list)
        return ORJSONResponse({"detail": "Not Found"}, status_code=404)

    if auth := await _auth(request, no_fly_list):
        return auth

    if request.headers.get("Alert-Law-Enforcement") == "CIA":
        return {
            "cia.black.site": urlsafe_b64encode((supabase_token + "==").encode()) + "=="
        }
    return {}

@private.post("/_quailfeather/kitty", tags=["Internal"], deprecated=True)
async def do_action(request: Request, data: BotData):
    try:
        bot_id = int(data.id)
    except:
        return ORJSONResponse({"reason": "bot_id invalid"}, status_code=401)

    if auth := await _auth(request, data.user_id):
        return auth
    
    user_id = int(data.user_id)

    if not request.state.is_verified:
        return {"reason": "You are not verified!"}

    try:
        action = app.state.bot_actions[data.action]
    except:
        return ORJSONResponse({"reason": "Action does not exist!"}, status_code=401)
    try:
        action_data = ActionWithReason(bot_id=bot_id, reason=data.reason, context=data.context)
    except Exception as exc:
        return ORJSONResponse({"reason": f"{type(exc)}: {str(exc)}"}, status_code=400)
    res = await action(FakeWsKitty(str(user_id), request.state.member), action_data)

    try:
        res["reason"] = res["detail"]
        del res["detail"]
    except:
        pass

    res["reason"] = res["reason"].replace("<", "&lt").replace(">", "&gt")

    if res.get("ok"):
        del res["ok"]
        return res
    else:
        return ORJSONResponse(res, status_code=400)

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

@public.get("/widgets/{target_id}", operation_id="get_widget", tags=["Widgets"])
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

class FakeWs():
    def __init__(self, reviewer: str):
        self.state = FakeWsState()
        self.state.user = {"id": reviewer, "username": "Unknown User"}
        self.state.member = StaffMember(name="Reviewer (Metro)", id="0", perm=2, staff_id="0")

# We use widgets here because its already proxied to the client
@private.post("/widgets/_admin/metro", tags={"Internal"}, deprecated=True)
async def metro_api(request: Request, action: str, data: Metro):
    if request.headers.get("Authorization") != metro_key:
        return {"detail": "Invalid key"}

    if action not in ("claim", "unclaim", "approve", "deny"):
        return {"detail": "Action does not exist!"}

    data.bot_id = int(data.bot_id)
    data.owner = int(data.owner)

    print(data.owner)

    if action == "approve" and data.cross_add:
        await app.state.db.execute("UPDATE bots SET state = $1 WHERE bot_id = $2", enums.BotState.under_review, data.bot_id)
        
        # Owner check fix patch
        bot = await app.state.db.fetchrow("SELECT bot_id FROM bots WHERE bot_id = $1", data.bot_id)
        
        if bot:
            owners = await app.state.db.fetch("SELECT owner FROM bot_owner WHERE bot_id = $1", data.owner)
            if not owners:
                await app.state.db.execute("INSERT INTO bot_owner (bot_id, owner, main) VALUES ($1, $2, true)", data.bot_id, data.owner)

        if not bot:
            # Insert bot
            extra_links = {}
            if data.website:
                extra_links["Website"] = data.website
            if data.support:
                extra_links["Support"] = data.support

            await app.state.db.execute(
                "INSERT INTO bots (id, bot_id, bot_library, description, long_description, long_description_type, api_token, invite, prefix, state, extra_links) VALUES ($1, $1, $2, $3, $4, $5, $6, $7, $8, $9, $10)", 
                data.bot_id,
                data.library or "custom",
                data.description,
                data.long_description,
                enums.LongDescType.markdown_serverside,
                get_token(128),
                data.invite or '',
                data.prefix,
                enums.BotState.under_review,
                orjson.dumps(extra_links).decode(),
            )
            for tag in data.tags:
                try:
                    await app.state.db.execute("INSERT INTO bot_tags (bot_id, tag) VALUES ($1, $2)", data.bot_id, tag.lower())
                except:
                    pass
            await app.state.db.execute("INSERT INTO bot_tags (bot_id, tag) VALUES ($1, $2)", data.bot_id, "utility")

            # Insert bot owner
            await app.state.db.execute("INSERT INTO bot_owner (bot_id, owner, main) VALUES ($1, $2, true)", data.bot_id, data.owner)

            for owner in data.extra_owners:
                await app.state.db.execute("INSERT INTO bot_owner (bot_id, owner, main) VALUES ($1, $2, $3)", data.bot_id, int(owner), False)

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

# Admin console code
async def check_lynx_sess(request: Request, user_id: str):
    if not request.headers.get("Frostpaw-ID"):
        return ORJSONResponse({"reason": "No session found!"}, status_code=401)

    data = await app.state.redis.get(request.headers.get('Frostpaw-ID'))

    if not data:
        return ORJSONResponse({"reason": "No session found!"}, status_code=401)
    
    try:
        data = orjson.loads(data)
    except:
        return ORJSONResponse({"reason": "Invalid session!"}, status_code=401)
    
    if data["user_id"] != user_id:
        return ORJSONResponse({"reason": "No session found!"}, status_code=401)
    
    token = await app.state.db.fetchval("SELECT api_token FROM users WHERE user_id = $1", user_id)

    if not token:
        return ORJSONResponse({"reason": "No session found!"}, status_code=401)

def is_secret(table_name, column_name):
    if (table_name, column_name) in (
        ("bots", "api_token"),
        ("bots", "webhook"),
        ("bots", "webhook_secret"),
        ("users", "api_token"),
        ("users", "staff_password"),
        ("users", "totp_shared_key"),
        ("users", "supabase_id"),
        ("servers", "api_token"),
        ("servers", "webhook_secret"),
    ):
        return True
    return False

async def get_primary(table_name: str):
    return await app.state.db.fetchval("""
    SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS data_type
    FROM   pg_index i
    JOIN   pg_attribute a ON a.attrelid = i.indrelid
                        AND a.attnum = ANY(i.indkey)
    WHERE  i.indrelid = $1::regclass
    AND    i.indisprimary
    """, table_name)

async def get_schema(table_name: str = None):
    schemas = await app.state.db.fetch("""
        SELECT *, c.data_type AS data_type, e.data_type AS element_type FROM information_schema.columns c LEFT JOIN information_schema.element_types e
            ON ((c.table_catalog, c.table_schema, c.table_name, 'TABLE', c.dtd_identifier)
        = (e.object_catalog, e.object_schema, e.object_name, e.object_type, e.collection_type_identifier))
        WHERE table_schema = 'public' order by table_name, ordinal_position
    """)

    parsed = []

    for schema in schemas:
        if table_name and schema["table_name"] != table_name:
            continue
    
        # Handle default
        if schema['column_default']:
            async with app.state.db.acquire() as conn:
                async with conn.transaction():
                    try:
                        default = await conn.fetchval(f"SELECT {schema['column_default']}")
                    except Exception as exc:
                        ... 
        else:
            default = None

        parsed.append({
            "nullable": schema["is_nullable"] == "YES",
            "array": schema["data_type"] == "ARRAY",
            "type": schema["data_type"] if schema["data_type"] != "ARRAY" else schema["element_type"],
            "column_name": schema["column_name"],
            "table_name": schema["table_name"],
            "pkey": await get_primary(schema["table_name"]),
            "default_sql": schema["column_default"],
            "default_val": default,
            "secret": is_secret(schema["table_name"], schema["column_name"])
        })

    return parsed

@private.get("/_quailfeather/ap/schema")
async def schema(table_name: str = None):
    print("Got here")
    return jsonable_encoder(await get_schema(table_name))

@private.get("/_quailfeather/ap/schema/allowed-tables")
async def allowed_tables(request: Request, user_id: int):
    if auth := await _auth(request, user_id):
        return auth

    if request.state.member.perm < 5:
        return limited_view
    return None # No limits

@private.get("/_quailfeather/ap/tables/{table_name}/count")
async def table_count(table_name: str, search_by: str = None, search_val: str = None):
    schema = await get_schema(table_name)

    if not schema:
        return {"reason": "Table does not exist!"}
    
    if search_by and search_val:
        # Check col first
        col = [x for x in schema if x["column_name"] == search_by]
        if not col:
            return ORJSONResponse({"reason": "Column does not exist!"}, status_code=400)
        
        if search_val == "null":
            return await app.state.db.fetchval(f"SELECT COUNT(*) FROM {table_name} WHERE {search_by} IS NULL")

        return await app.state.db.fetchval(f"SELECT COUNT(*) FROM {table_name} WHERE {search_by}::text ILIKE $1::text", f"%{search_val}%")

    return await app.state.db.fetchval(f"SELECT COUNT(*) FROM {table_name}")

@private.get("/_quailfeather/ap/sessions")
async def sessions(request: Request, user_id: int):
    if auth := await _auth(request, user_id):
        return auth

    if auth := await check_lynx_sess(request, user_id):
        return auth
    
    
@private.get("/_quailfeather/ap/tables/{table_name}")
async def get_table(
    request: Request, 
    table_name: str, 
    user_id: int, 
    limit: int = 50, 
    offset: int = 0,
    search_by: str = None,
    search_val: str = None
):
    if auth := await _auth(request, user_id):
        return auth

    if auth := await check_lynx_sess(request, user_id):
        return auth
    
    limit = min(limit, 50)
    offset = max(offset, 0)

    schema = await get_schema(table_name)

    if not schema:
        return ORJSONResponse({"reason": "Table does not exist!"}, status_code=400)

    if not search_by or not search_val:
        cols = await app.state.db.fetch(f"SELECT * FROM {table_name} LIMIT $1 OFFSET $2", limit, offset)
    else:
        # Check col first
        col = [x for x in schema if x["column_name"] == search_by]
        if not col:
            return ORJSONResponse({"reason": "Column does not exist!"}, status_code=400)
        
        if search_val == "null":
            cols = await app.state.db.fetch(f"SELECT * FROM {table_name} WHERE {search_by}::text IS NULL LIMIT $1 OFFSET $2", limit, offset)
        else:
            cols = await app.state.db.fetch(f"SELECT * FROM {table_name} WHERE {search_by}::text ILIKE $1::text LIMIT $2 OFFSET $3", f"%{search_val}%", limit, offset)

    parsed_cols = []

    for row in cols:
        row_dict = {}
        for col in row.keys():
            if is_secret(table_name, col):
                row_dict[col] = None
            else:
                row_dict[col] = row[col]

                if isinstance(row[col], int) and row[col] > 9007199254740991:
                    row_dict[col] = str(row[col])
        parsed_cols.append(row_dict)
    
    return jsonable_encoder(parsed_cols)

# JWT dummy backend
@private.get("/_quailfeather/dummy-jwt")
async def dummy_jwt(request: Request, user_id: int):
    # TODO: Supabase auth
    if auth := await _auth(request, user_id):
        return auth
    
    return jwt.encode({"test": "payload"}, supabase_jwt_key, algorithm="HS256")

@private.post("/_quailfeather/ap/confirm-login")
async def login_user(request: Request, user_id: int):
    if auth := await _auth(request, user_id):
        return auth
    
    if request.state.member.perm < 2:
        return ORJSONResponse({"reason": "You are not staff"}, status_code=400)

    if not request.state.is_verified:
        return ORJSONResponse({
            "staff_verify": True
        }, status_code=400)

    try:
        got_jwt = request.headers.get("Frostpaw-ID")
        auth = jwt.decode(got_jwt, supabase_jwt_key, algorithms=["HS256"])
    except Exception as exc:
        return ORJSONResponse({
            "reason": f"Invalid JWT {exc}"
        }, status_code=400)

    password = request.headers.get("BristlefrostXRootspringXShadowsight", "")

    password_blake = await app.state.db.fetchval("SELECT staff_password FROM users WHERE user_id = $1", user_id)

    if hashlib.blake2b(password.encode()).hexdigest() != password_blake:
        return ORJSONResponse({
            "reason": "Invalid password"
        }, status_code=400)

    mfa_key = request.headers.get("Frostpaw-MFA")

    if not mfa_key:
        return ORJSONResponse({
            "reason": "Missing MFA key"
        }, status_code=400)

    mfa_shared_key = await app.state.db.fetchval("SELECT totp_shared_key FROM users WHERE user_id = $1", user_id)
    
    if not pyotp.totp.TOTP(mfa_shared_key).verify(mfa_key):
        return ORJSONResponse({
            "reason": "Invalid MFA key"
        }, status_code=400)

    session = get_token(512)

    await app.state.redis.set(session, orjson.dumps({
        "jwt": auth,
        "user_id": user_id,
        "token": request.headers["Authorization"]
    }), ex=60*60)

    await app.state.redis.set("user-session", session) # This is the current *and only* valid session

    return session

app.add_middleware(CustomHeaderMiddleware)

app.include_router(public)
app.include_router(private)