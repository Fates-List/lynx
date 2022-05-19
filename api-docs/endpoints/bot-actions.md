
**API URL**: ``https://api.fateslist.xyz``

**Widgets Documentation:** ``https://lynx.fateslist.xyz/widgets`` (docs for widgets available at https://lynx.fateslist.xyz/widgets)

## Authorization

- **Bot:** These endpoints require a bot token. 
You can get this from Bot Settings. Make sure to keep this safe and in 
a .gitignore/.env. A prefix of `Bot` before the bot token such as 
`Bot abcdef` is supported and can be used to avoid ambiguity but is not 
required. The default auth scheme if no prefix is given depends on the
endpoint: Endpoints which have only one auth scheme will use that auth 
scheme while endpoints with multiple will always use `Bot` for 
backward compatibility

- **Server:** These endpoints require a server
token which you can get using ``/get API Token`` in your server. 
Same warnings and information from the other authentication types 
apply here. A prefix of ``Server`` before the server token is 
supported and can be used to avoid ambiguity but is not required.

- **User:** These endpoints require a user token. You can get this 
from your profile under the User Token section. If you are using this 
for voting, make sure to allow users to opt out! A prefix of `User` 
before the user token such as `User abcdef` is supported and can be 
used to avoid ambiguity but is not required outside of endpoints that 
have both a user and a bot authentication option such as Get Votes. 
In such endpoints, the default will always be a bot auth unless 
you prefix the token with `User`. **A access token (for custom clients)
can also be used on *most* endpoints as long as the token is prefixed with 
``Frostpaw``**

## Base Response

A default API Response will be of the below format:

```json
{
    done: false | true,
    reason: "" | null,
    context: "" | null
}
```

## Post Stats
### POST `https://api.fateslist.xyz`/bots/{id}/stats

Post stats to the list

Example:
```py
import requests

# On dpy, guild_count is usually the below
guild_count = len(client.guilds)

# If you are using sharding
shard_count = len(client.shards)
shards = client.shards.keys()

# Optional: User count (this is not accurate for larger bots)
user_count = len(client.users) 

def post_stats(bot_id: int, guild_count: int):
    res = requests.post(f"{api_url}/bots/{bot_id}/stats", json={"guild_count": guild_count})
    json = res.json()
    if res.status != 200:
        # Handle an error in the api
        ...
    return json
```

**Path Parameters**

- **id** => i64 [default/example = 0]




**Request Body**

- **guild_count** => i64 [default/example = 3939]
- **shard_count** => (Optional) i64 [default/example = 48484]
- **shards** => (Optional) (Array) i32 [default/example = 149]i32 [default/example = 22020]
- **user_count** => (Optional) i64 [default/example = 39393]



**Request Body Example**

```json
{
    "guild_count": 3939,
    "shard_count": 48484,
    "shards": [
        149,
        22020
    ],
    "user_count": 39393
}
```


**Response Body**

- **done** => bool [default/example = false]
- **reason** => None (unknown value type)
- **context** => None (unknown value type)



**Response Body Example**

```json
{
    "done": false,
    "reason": null,
    "context": null
}
```


**Authorization Needed** | [Bot](#authorization)


## Get Bot
### GET `https://api.fateslist.xyz`/bots/{id}

Fetches bot information given a bot ID. If not found, 404 will be returned. 

This endpoint handles both bot IDs and client IDs

- ``long_description/css`` is sanitized with ammonia by default, use `long_description_raw` if you want the unsanitized version
- All responses are cached for a short period of time. There is *no* way to opt out at this time
- Some fields have been renamed or removed from API v2 (such as ``promos`` which may be readded at a later date)

This API returns some empty fields such as ``webhook``, ``webhook_secret``, ``api_token`` and more. 
This is to allow reuse of the Bot struct in Get Bot Settings which *does* contain this sensitive data. 

**Set the Frostpaw header if you are a custom client. Send Frostpaw-Invite header on invites**
                

**Path Parameters**

- **id** => i64 [default/example = 0]





**Response Body**

- **user** => Struct User 
	- **id** => string [default/example = ""]
	- **username** => string [default/example = ""]
	- **disc** => string [default/example = ""]
	- **avatar** => string [default/example = ""]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]



- **description** => string [default/example = ""]
- **tags** => (Array) 
- **created_at** => string [default/example = "1970-01-01T00:00:00Z"]
- **last_updated_at** => string [default/example = "1970-01-01T00:00:00Z"]
- **last_stats_post** => string [default/example = "1970-01-01T00:00:00Z"]
- **long_description** => string [default/example = "blah blah blah"]
- **long_description_raw** => string [default/example = "blah blah blah unsanitized"]
- **long_description_type** => i32 [default/example = 1]
- **guild_count** => i64 [default/example = 0]
- **shard_count** => i64 [default/example = 493]
- **user_count** => i64 [default/example = 0]
- **shards** => (Array) 
- **prefix** => (Optional) string [default/example = "Some prefix, null = slash command"]
- **library** => string [default/example = ""]
- **invite** => (Optional) string [default/example = "Raw invite, null = auto-generated. Use invite_link instead"]
- **invite_link** => string [default/example = "https://discord.com/api/oauth2/authorize...."]
- **invite_amount** => i32 [default/example = 48]
- **owners** => (Array) Struct BotOwner 
	- **user** => Struct User 
		- **id** => string [default/example = ""]
		- **username** => string [default/example = ""]
		- **disc** => string [default/example = ""]
		- **avatar** => string [default/example = ""]
		- **bot** => bool [default/example = false]
		- **status** => string [default/example = "Unknown"]



	- **main** => bool [default/example = false]



- **features** => (Array) Struct Feature 
	- **id** => string [default/example = ""]
	- **name** => string [default/example = ""]
	- **viewed_as** => string [default/example = ""]
	- **description** => string [default/example = ""]



- **state** => i32 [default/example = 0]
- **page_style** => i32 [default/example = 1]
- **extra_links** => Map (key/value)  
	- **key**
 => string [default/example = "value"]



- **css** => string [default/example = "<style></style>"]
- **css_raw** => string [default/example = "unsanitized css"]
- **votes** => i64 [default/example = 0]
- **total_votes** => i64 [default/example = 0]
- **vanity** => string [default/example = ""]
- **banner_card** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
- **banner_page** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
- **client_id** => string [default/example = ""]
- **flags** => (Array) 
- **action_logs** => (Array) Struct ActionLog 
	- **user_id** => string [default/example = ""]
	- **bot_id** => string [default/example = ""]
	- **action** => i32 [default/example = 0]
	- **action_time** => string [default/example = "1970-01-01T00:00:00Z"]
	- **context** => (Optional) string [default/example = "Some context as to why the action happened"]



- **vpm** => (Optional) (Array) Struct VotesPerMonth 
	- **votes** => i64 [default/example = 0]
	- **ts** => string [default/example = "1970-01-01T00:00:00Z"]



- **uptime_checks_total** => (Optional) i32 [default/example = 30]
- **uptime_checks_failed** => (Optional) i32 [default/example = 19]
- **commands** => (Array) Struct BotCommand 
	- **cmd_type** => i32 [default/example = 0]
	- **groups** => (Array) 
	- **name** => string [default/example = ""]
	- **vote_locked** => bool [default/example = false]
	- **description** => string [default/example = ""]
	- **args** => (Array) 
	- **examples** => (Array) 
	- **premium_only** => bool [default/example = false]
	- **notes** => (Array) 
	- **doc_link** => None (unknown value type)
	- **id** => None (unknown value type)
	- **nsfw** => bool [default/example = false]



- **webhook** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]
- **webhook_secret** => (Optional) string [default/example = "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint"]
- **webhook_type** => None (unknown value type)
- **webhook_hmac_only** => None (unknown value type)
- **api_token** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]



**Response Body Example**

```json
{
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "description": "",
    "tags": [],
    "created_at": "1970-01-01T00:00:00Z",
    "last_updated_at": "1970-01-01T00:00:00Z",
    "last_stats_post": "1970-01-01T00:00:00Z",
    "long_description": "blah blah blah",
    "long_description_raw": "blah blah blah unsanitized",
    "long_description_type": 1,
    "guild_count": 0,
    "shard_count": 493,
    "user_count": 0,
    "shards": [],
    "prefix": "Some prefix, null = slash command",
    "library": "",
    "invite": "Raw invite, null = auto-generated. Use invite_link instead",
    "invite_link": "https://discord.com/api/oauth2/authorize....",
    "invite_amount": 48,
    "owners": [
        {
            "user": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            },
            "main": false
        }
    ],
    "features": [
        {
            "id": "",
            "name": "",
            "viewed_as": "",
            "description": ""
        }
    ],
    "state": 0,
    "page_style": 1,
    "extra_links": {
        "key": "value"
    },
    "css": "<style></style>",
    "css_raw": "unsanitized css",
    "votes": 0,
    "total_votes": 0,
    "vanity": "",
    "banner_card": "https://api.fateslist.xyz/static/botlisticon.webp",
    "banner_page": "https://api.fateslist.xyz/static/botlisticon.webp",
    "client_id": "",
    "flags": [],
    "action_logs": [
        {
            "user_id": "",
            "bot_id": "",
            "action": 0,
            "action_time": "1970-01-01T00:00:00Z",
            "context": "Some context as to why the action happened"
        }
    ],
    "vpm": [
        {
            "votes": 0,
            "ts": "1970-01-01T00:00:00Z"
        }
    ],
    "uptime_checks_total": 30,
    "uptime_checks_failed": 19,
    "commands": [
        {
            "cmd_type": 0,
            "groups": [],
            "name": "",
            "vote_locked": false,
            "description": "",
            "args": [],
            "examples": [],
            "premium_only": false,
            "notes": [],
            "doc_link": null,
            "id": null,
            "nsfw": false
        }
    ],
    "webhook": "This will be redacted for Get Bot endpoint",
    "webhook_secret": "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint",
    "webhook_type": null,
    "webhook_hmac_only": null,
    "api_token": "This will be redacted for Get Bot endpoint"
}
```


**Authorization Needed** | None


## Gets Bot Settings
### GET `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}/settings

Returns the bot settings.

The ``bot`` here is equivalent to a Get Bot response with the following
differences:

- Sensitive fields (see examples) like ``webhook``, ``api_token``, 
``webhook_secret`` and others are filled out here
- This API only allows bot owners (not even staff) to use it, otherwise it will 400!

Staff members *must* instead use Lynx.

**Path Parameters**

- **user_id** => i64 [default/example = 0]
- **bot_id** => i64 [default/example = 0]





**Response Body**

- **bot** => Struct Bot 
	- **user** => Struct User 
		- **id** => string [default/example = ""]
		- **username** => string [default/example = ""]
		- **disc** => string [default/example = ""]
		- **avatar** => string [default/example = ""]
		- **bot** => bool [default/example = false]
		- **status** => string [default/example = "Unknown"]



	- **description** => string [default/example = ""]
	- **tags** => (Array) 
	- **created_at** => string [default/example = "1970-01-01T00:00:00Z"]
	- **last_updated_at** => string [default/example = "1970-01-01T00:00:00Z"]
	- **last_stats_post** => string [default/example = "1970-01-01T00:00:00Z"]
	- **long_description** => string [default/example = "blah blah blah"]
	- **long_description_raw** => string [default/example = "blah blah blah unsanitized"]
	- **long_description_type** => i32 [default/example = 1]
	- **guild_count** => i64 [default/example = 0]
	- **shard_count** => i64 [default/example = 493]
	- **user_count** => i64 [default/example = 0]
	- **shards** => (Array) 
	- **prefix** => (Optional) string [default/example = "Some prefix, null = slash command"]
	- **library** => string [default/example = ""]
	- **invite** => (Optional) string [default/example = "Raw invite, null = auto-generated. Use invite_link instead"]
	- **invite_link** => string [default/example = "https://discord.com/api/oauth2/authorize...."]
	- **invite_amount** => i32 [default/example = 48]
	- **owners** => (Array) Struct BotOwner 
		- **user** => Struct User 
			- **id** => string [default/example = ""]
			- **username** => string [default/example = ""]
			- **disc** => string [default/example = ""]
			- **avatar** => string [default/example = ""]
			- **bot** => bool [default/example = false]
			- **status** => string [default/example = "Unknown"]



		- **main** => bool [default/example = false]



	- **features** => (Array) Struct Feature 
		- **id** => string [default/example = ""]
		- **name** => string [default/example = ""]
		- **viewed_as** => string [default/example = ""]
		- **description** => string [default/example = ""]



	- **state** => i32 [default/example = 0]
	- **page_style** => i32 [default/example = 1]
	- **extra_links** => Map (key/value)  
		- **key**
 => string [default/example = "value"]



	- **css** => string [default/example = "<style></style>"]
	- **css_raw** => string [default/example = "unsanitized css"]
	- **votes** => i64 [default/example = 0]
	- **total_votes** => i64 [default/example = 0]
	- **vanity** => string [default/example = ""]
	- **banner_card** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
	- **banner_page** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
	- **client_id** => string [default/example = ""]
	- **flags** => (Array) 
	- **action_logs** => (Array) Struct ActionLog 
		- **user_id** => string [default/example = ""]
		- **bot_id** => string [default/example = ""]
		- **action** => i32 [default/example = 0]
		- **action_time** => string [default/example = "1970-01-01T00:00:00Z"]
		- **context** => (Optional) string [default/example = "Some context as to why the action happened"]



	- **vpm** => (Optional) (Array) Struct VotesPerMonth 
		- **votes** => i64 [default/example = 0]
		- **ts** => string [default/example = "1970-01-01T00:00:00Z"]



	- **uptime_checks_total** => (Optional) i32 [default/example = 30]
	- **uptime_checks_failed** => (Optional) i32 [default/example = 19]
	- **commands** => (Array) Struct BotCommand 
		- **cmd_type** => i32 [default/example = 0]
		- **groups** => (Array) 
		- **name** => string [default/example = ""]
		- **vote_locked** => bool [default/example = false]
		- **description** => string [default/example = ""]
		- **args** => (Array) 
		- **examples** => (Array) 
		- **premium_only** => bool [default/example = false]
		- **notes** => (Array) 
		- **doc_link** => None (unknown value type)
		- **id** => None (unknown value type)
		- **nsfw** => bool [default/example = false]



	- **webhook** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]
	- **webhook_secret** => (Optional) string [default/example = "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint"]
	- **webhook_type** => None (unknown value type)
	- **webhook_hmac_only** => None (unknown value type)
	- **api_token** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]



- **context** => Struct BotSettingsContext 
	- **tags** => (Array) Struct Tag 
		- **name** => string [default/example = ""]
		- **iconify_data** => string [default/example = ""]
		- **id** => string [default/example = ""]
		- **owner_guild** => None (unknown value type)



	- **features** => (Array) Struct Feature 
		- **id** => string [default/example = ""]
		- **name** => string [default/example = ""]
		- **viewed_as** => string [default/example = ""]
		- **description** => string [default/example = ""]









**Response Body Example**

```json
{
    "bot": {
        "user": {
            "id": "",
            "username": "",
            "disc": "",
            "avatar": "",
            "bot": false,
            "status": "Unknown"
        },
        "description": "",
        "tags": [],
        "created_at": "1970-01-01T00:00:00Z",
        "last_updated_at": "1970-01-01T00:00:00Z",
        "last_stats_post": "1970-01-01T00:00:00Z",
        "long_description": "blah blah blah",
        "long_description_raw": "blah blah blah unsanitized",
        "long_description_type": 1,
        "guild_count": 0,
        "shard_count": 493,
        "user_count": 0,
        "shards": [],
        "prefix": "Some prefix, null = slash command",
        "library": "",
        "invite": "Raw invite, null = auto-generated. Use invite_link instead",
        "invite_link": "https://discord.com/api/oauth2/authorize....",
        "invite_amount": 48,
        "owners": [
            {
                "user": {
                    "id": "",
                    "username": "",
                    "disc": "",
                    "avatar": "",
                    "bot": false,
                    "status": "Unknown"
                },
                "main": false
            }
        ],
        "features": [
            {
                "id": "",
                "name": "",
                "viewed_as": "",
                "description": ""
            }
        ],
        "state": 0,
        "page_style": 1,
        "extra_links": {
            "key": "value"
        },
        "css": "<style></style>",
        "css_raw": "unsanitized css",
        "votes": 0,
        "total_votes": 0,
        "vanity": "",
        "banner_card": "https://api.fateslist.xyz/static/botlisticon.webp",
        "banner_page": "https://api.fateslist.xyz/static/botlisticon.webp",
        "client_id": "",
        "flags": [],
        "action_logs": [
            {
                "user_id": "",
                "bot_id": "",
                "action": 0,
                "action_time": "1970-01-01T00:00:00Z",
                "context": "Some context as to why the action happened"
            }
        ],
        "vpm": [
            {
                "votes": 0,
                "ts": "1970-01-01T00:00:00Z"
            }
        ],
        "uptime_checks_total": 30,
        "uptime_checks_failed": 19,
        "commands": [
            {
                "cmd_type": 0,
                "groups": [],
                "name": "",
                "vote_locked": false,
                "description": "",
                "args": [],
                "examples": [],
                "premium_only": false,
                "notes": [],
                "doc_link": null,
                "id": null,
                "nsfw": false
            }
        ],
        "webhook": "This will be redacted for Get Bot endpoint",
        "webhook_secret": "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint",
        "webhook_type": null,
        "webhook_hmac_only": null,
        "api_token": "This will be redacted for Get Bot endpoint"
    },
    "context": {
        "tags": [
            {
                "name": "",
                "iconify_data": "",
                "id": "",
                "owner_guild": null
            }
        ],
        "features": [
            {
                "id": "",
                "name": "",
                "viewed_as": "",
                "description": ""
            }
        ]
    }
}
```


**Authorization Needed** | [User](#authorization)


## Random Bot
### GET `https://api.fateslist.xyz`/random-bot

Fetches a random bot on the list

Example:
```py
import requests

def random_bot():
    res = requests.get(api_url"/random-bot")
    json = res.json()
    if res.status != 200:
        # Handle an error in the api
        ...
    return json
```



**Response Body**

- **guild_count** => i64 [default/example = 30]
- **description** => string [default/example = "My description"]
- **banner** => string [default/example = "My banner or default banner url"]
- **votes** => i64 [default/example = 40]
- **state** => i32 [default/example = 3]
- **user** => Struct User 
	- **id** => string [default/example = ""]
	- **username** => string [default/example = ""]
	- **disc** => string [default/example = ""]
	- **avatar** => string [default/example = ""]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]



- **flags** => (Array) 
- **created_at** => string [default/example = "2022-05-19T14:32:40.374251617Z"]



**Response Body Example**

```json
{
    "guild_count": 30,
    "description": "My description",
    "banner": "My banner or default banner url",
    "votes": 40,
    "state": 3,
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "flags": [],
    "created_at": "2022-05-19T14:32:40.374251617Z"
}
```


**Authorization Needed** | None


## New Bot
### POST `https://api.fateslist.xyz`/users/{id}/bots

Creates a new bot. 

Set ``created_at``, ``last_stats_post`` to sometime in the past

Set ``api_token``, ``guild_count`` etc (unknown/not editable fields) to any 
random value of the same type.

With regards to ``extra_owners``, put all of them as a ``BotOwner`` object
containing ``main`` set to ``false`` and ``user`` as a dummy ``user`` object 
containing ``id`` filled in and the rest of a ``user``empty strings. Set ``bot``
to false.

**Path Parameters**

- **id** => i64 [default/example = 0]




**Request Body**

- **user** => Struct User 
	- **id** => string [default/example = ""]
	- **username** => string [default/example = ""]
	- **disc** => string [default/example = ""]
	- **avatar** => string [default/example = ""]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]



- **description** => string [default/example = ""]
- **tags** => (Array) 
- **created_at** => string [default/example = "1970-01-01T00:00:00Z"]
- **last_updated_at** => string [default/example = "1970-01-01T00:00:00Z"]
- **last_stats_post** => string [default/example = "1970-01-01T00:00:00Z"]
- **long_description** => string [default/example = "blah blah blah"]
- **long_description_raw** => string [default/example = "blah blah blah unsanitized"]
- **long_description_type** => i32 [default/example = 1]
- **guild_count** => i64 [default/example = 0]
- **shard_count** => i64 [default/example = 493]
- **user_count** => i64 [default/example = 0]
- **shards** => (Array) 
- **prefix** => (Optional) string [default/example = "Some prefix, null = slash command"]
- **library** => string [default/example = ""]
- **invite** => (Optional) string [default/example = "Raw invite, null = auto-generated. Use invite_link instead"]
- **invite_link** => string [default/example = "https://discord.com/api/oauth2/authorize...."]
- **invite_amount** => i32 [default/example = 48]
- **owners** => (Array) Struct BotOwner 
	- **user** => Struct User 
		- **id** => string [default/example = ""]
		- **username** => string [default/example = ""]
		- **disc** => string [default/example = ""]
		- **avatar** => string [default/example = ""]
		- **bot** => bool [default/example = false]
		- **status** => string [default/example = "Unknown"]



	- **main** => bool [default/example = false]



- **features** => (Array) Struct Feature 
	- **id** => string [default/example = ""]
	- **name** => string [default/example = ""]
	- **viewed_as** => string [default/example = ""]
	- **description** => string [default/example = ""]



- **state** => i32 [default/example = 0]
- **page_style** => i32 [default/example = 1]
- **extra_links** => Map (key/value)  
	- **key**
 => string [default/example = "value"]



- **css** => string [default/example = "<style></style>"]
- **css_raw** => string [default/example = "unsanitized css"]
- **votes** => i64 [default/example = 0]
- **total_votes** => i64 [default/example = 0]
- **vanity** => string [default/example = ""]
- **banner_card** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
- **banner_page** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
- **client_id** => string [default/example = ""]
- **flags** => (Array) 
- **action_logs** => (Array) Struct ActionLog 
	- **user_id** => string [default/example = ""]
	- **bot_id** => string [default/example = ""]
	- **action** => i32 [default/example = 0]
	- **action_time** => string [default/example = "1970-01-01T00:00:00Z"]
	- **context** => (Optional) string [default/example = "Some context as to why the action happened"]



- **vpm** => (Optional) (Array) Struct VotesPerMonth 
	- **votes** => i64 [default/example = 0]
	- **ts** => string [default/example = "1970-01-01T00:00:00Z"]



- **uptime_checks_total** => (Optional) i32 [default/example = 30]
- **uptime_checks_failed** => (Optional) i32 [default/example = 19]
- **commands** => (Array) Struct BotCommand 
	- **cmd_type** => i32 [default/example = 0]
	- **groups** => (Array) 
	- **name** => string [default/example = ""]
	- **vote_locked** => bool [default/example = false]
	- **description** => string [default/example = ""]
	- **args** => (Array) 
	- **examples** => (Array) 
	- **premium_only** => bool [default/example = false]
	- **notes** => (Array) 
	- **doc_link** => None (unknown value type)
	- **id** => None (unknown value type)
	- **nsfw** => bool [default/example = false]



- **webhook** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]
- **webhook_secret** => (Optional) string [default/example = "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint"]
- **webhook_type** => None (unknown value type)
- **webhook_hmac_only** => None (unknown value type)
- **api_token** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]



**Request Body Example**

```json
{
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "description": "",
    "tags": [],
    "created_at": "1970-01-01T00:00:00Z",
    "last_updated_at": "1970-01-01T00:00:00Z",
    "last_stats_post": "1970-01-01T00:00:00Z",
    "long_description": "blah blah blah",
    "long_description_raw": "blah blah blah unsanitized",
    "long_description_type": 1,
    "guild_count": 0,
    "shard_count": 493,
    "user_count": 0,
    "shards": [],
    "prefix": "Some prefix, null = slash command",
    "library": "",
    "invite": "Raw invite, null = auto-generated. Use invite_link instead",
    "invite_link": "https://discord.com/api/oauth2/authorize....",
    "invite_amount": 48,
    "owners": [
        {
            "user": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            },
            "main": false
        }
    ],
    "features": [
        {
            "id": "",
            "name": "",
            "viewed_as": "",
            "description": ""
        }
    ],
    "state": 0,
    "page_style": 1,
    "extra_links": {
        "key": "value"
    },
    "css": "<style></style>",
    "css_raw": "unsanitized css",
    "votes": 0,
    "total_votes": 0,
    "vanity": "",
    "banner_card": "https://api.fateslist.xyz/static/botlisticon.webp",
    "banner_page": "https://api.fateslist.xyz/static/botlisticon.webp",
    "client_id": "",
    "flags": [],
    "action_logs": [
        {
            "user_id": "",
            "bot_id": "",
            "action": 0,
            "action_time": "1970-01-01T00:00:00Z",
            "context": "Some context as to why the action happened"
        }
    ],
    "vpm": [
        {
            "votes": 0,
            "ts": "1970-01-01T00:00:00Z"
        }
    ],
    "uptime_checks_total": 30,
    "uptime_checks_failed": 19,
    "commands": [
        {
            "cmd_type": 0,
            "groups": [],
            "name": "",
            "vote_locked": false,
            "description": "",
            "args": [],
            "examples": [],
            "premium_only": false,
            "notes": [],
            "doc_link": null,
            "id": null,
            "nsfw": false
        }
    ],
    "webhook": "This will be redacted for Get Bot endpoint",
    "webhook_secret": "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint",
    "webhook_type": null,
    "webhook_hmac_only": null,
    "api_token": "This will be redacted for Get Bot endpoint"
}
```


**Response Body**

- **done** => bool [default/example = true]
- **reason** => None (unknown value type)
- **context** => None (unknown value type)



**Response Body Example**

```json
{
    "done": true,
    "reason": null,
    "context": null
}
```


**Authorization Needed** | [User](#authorization)


## Edit Bot
### PATCH `https://api.fateslist.xyz`/users/{id}/bots

Edits a existing bot. 

Set ``created_at``, ``last_stats_post`` to sometime in the past

Set ``api_token``, ``guild_count`` etc (unknown/not editable fields) to any 
random value of the same type

With regards to ``extra_owners``, put all of them as a ``BotOwner`` object
containing ``main`` set to ``false`` and ``user`` as a dummy ``user`` object 
containing ``id`` filled in and the rest of a ``user``empty strings. Set ``bot`` 
to false.

**Path Parameters**

- **id** => i64 [default/example = 0]




**Request Body**

- **user** => Struct User 
	- **id** => string [default/example = ""]
	- **username** => string [default/example = ""]
	- **disc** => string [default/example = ""]
	- **avatar** => string [default/example = ""]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]



- **description** => string [default/example = ""]
- **tags** => (Array) 
- **created_at** => string [default/example = "1970-01-01T00:00:00Z"]
- **last_updated_at** => string [default/example = "1970-01-01T00:00:00Z"]
- **last_stats_post** => string [default/example = "1970-01-01T00:00:00Z"]
- **long_description** => string [default/example = "blah blah blah"]
- **long_description_raw** => string [default/example = "blah blah blah unsanitized"]
- **long_description_type** => i32 [default/example = 1]
- **guild_count** => i64 [default/example = 0]
- **shard_count** => i64 [default/example = 493]
- **user_count** => i64 [default/example = 0]
- **shards** => (Array) 
- **prefix** => (Optional) string [default/example = "Some prefix, null = slash command"]
- **library** => string [default/example = ""]
- **invite** => (Optional) string [default/example = "Raw invite, null = auto-generated. Use invite_link instead"]
- **invite_link** => string [default/example = "https://discord.com/api/oauth2/authorize...."]
- **invite_amount** => i32 [default/example = 48]
- **owners** => (Array) Struct BotOwner 
	- **user** => Struct User 
		- **id** => string [default/example = ""]
		- **username** => string [default/example = ""]
		- **disc** => string [default/example = ""]
		- **avatar** => string [default/example = ""]
		- **bot** => bool [default/example = false]
		- **status** => string [default/example = "Unknown"]



	- **main** => bool [default/example = false]



- **features** => (Array) Struct Feature 
	- **id** => string [default/example = ""]
	- **name** => string [default/example = ""]
	- **viewed_as** => string [default/example = ""]
	- **description** => string [default/example = ""]



- **state** => i32 [default/example = 0]
- **page_style** => i32 [default/example = 1]
- **extra_links** => Map (key/value)  
	- **key**
 => string [default/example = "value"]



- **css** => string [default/example = "<style></style>"]
- **css_raw** => string [default/example = "unsanitized css"]
- **votes** => i64 [default/example = 0]
- **total_votes** => i64 [default/example = 0]
- **vanity** => string [default/example = ""]
- **banner_card** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
- **banner_page** => (Optional) string [default/example = "https://api.fateslist.xyz/static/botlisticon.webp"]
- **client_id** => string [default/example = ""]
- **flags** => (Array) 
- **action_logs** => (Array) Struct ActionLog 
	- **user_id** => string [default/example = ""]
	- **bot_id** => string [default/example = ""]
	- **action** => i32 [default/example = 0]
	- **action_time** => string [default/example = "1970-01-01T00:00:00Z"]
	- **context** => (Optional) string [default/example = "Some context as to why the action happened"]



- **vpm** => (Optional) (Array) Struct VotesPerMonth 
	- **votes** => i64 [default/example = 0]
	- **ts** => string [default/example = "1970-01-01T00:00:00Z"]



- **uptime_checks_total** => (Optional) i32 [default/example = 30]
- **uptime_checks_failed** => (Optional) i32 [default/example = 19]
- **commands** => (Array) Struct BotCommand 
	- **cmd_type** => i32 [default/example = 0]
	- **groups** => (Array) 
	- **name** => string [default/example = ""]
	- **vote_locked** => bool [default/example = false]
	- **description** => string [default/example = ""]
	- **args** => (Array) 
	- **examples** => (Array) 
	- **premium_only** => bool [default/example = false]
	- **notes** => (Array) 
	- **doc_link** => None (unknown value type)
	- **id** => None (unknown value type)
	- **nsfw** => bool [default/example = false]



- **webhook** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]
- **webhook_secret** => (Optional) string [default/example = "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint"]
- **webhook_type** => None (unknown value type)
- **webhook_hmac_only** => None (unknown value type)
- **api_token** => (Optional) string [default/example = "This will be redacted for Get Bot endpoint"]



**Request Body Example**

```json
{
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "description": "",
    "tags": [],
    "created_at": "1970-01-01T00:00:00Z",
    "last_updated_at": "1970-01-01T00:00:00Z",
    "last_stats_post": "1970-01-01T00:00:00Z",
    "long_description": "blah blah blah",
    "long_description_raw": "blah blah blah unsanitized",
    "long_description_type": 1,
    "guild_count": 0,
    "shard_count": 493,
    "user_count": 0,
    "shards": [],
    "prefix": "Some prefix, null = slash command",
    "library": "",
    "invite": "Raw invite, null = auto-generated. Use invite_link instead",
    "invite_link": "https://discord.com/api/oauth2/authorize....",
    "invite_amount": 48,
    "owners": [
        {
            "user": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            },
            "main": false
        }
    ],
    "features": [
        {
            "id": "",
            "name": "",
            "viewed_as": "",
            "description": ""
        }
    ],
    "state": 0,
    "page_style": 1,
    "extra_links": {
        "key": "value"
    },
    "css": "<style></style>",
    "css_raw": "unsanitized css",
    "votes": 0,
    "total_votes": 0,
    "vanity": "",
    "banner_card": "https://api.fateslist.xyz/static/botlisticon.webp",
    "banner_page": "https://api.fateslist.xyz/static/botlisticon.webp",
    "client_id": "",
    "flags": [],
    "action_logs": [
        {
            "user_id": "",
            "bot_id": "",
            "action": 0,
            "action_time": "1970-01-01T00:00:00Z",
            "context": "Some context as to why the action happened"
        }
    ],
    "vpm": [
        {
            "votes": 0,
            "ts": "1970-01-01T00:00:00Z"
        }
    ],
    "uptime_checks_total": 30,
    "uptime_checks_failed": 19,
    "commands": [
        {
            "cmd_type": 0,
            "groups": [],
            "name": "",
            "vote_locked": false,
            "description": "",
            "args": [],
            "examples": [],
            "premium_only": false,
            "notes": [],
            "doc_link": null,
            "id": null,
            "nsfw": false
        }
    ],
    "webhook": "This will be redacted for Get Bot endpoint",
    "webhook_secret": "This (along with ``webhook_type``, ``api_token`` and ``webhook_hmac_only``) will be redacted for Get Bot endpoint",
    "webhook_type": null,
    "webhook_hmac_only": null,
    "api_token": "This will be redacted for Get Bot endpoint"
}
```


**Response Body**

- **done** => bool [default/example = true]
- **reason** => None (unknown value type)
- **context** => None (unknown value type)



**Response Body Example**

```json
{
    "done": true,
    "reason": null,
    "context": null
}
```


**Authorization Needed** | [User](#authorization)


## Transfer Ownership
### PATCH `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}/main-owner

Transfers bot ownership.

You **must** be main owner of the bot to use this endpoint.
                

**Path Parameters**

- **user_id** => i64 [default/example = 0]
- **bot_id** => i64 [default/example = 0]




**Request Body**

- **user** => Struct User 
	- **id** => string [default/example = "id here"]
	- **username** => string [default/example = "Leave blank"]
	- **disc** => string [default/example = "Leave blank"]
	- **avatar** => string [default/example = "Leave blank"]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]



- **main** => bool [default/example = true]



**Request Body Example**

```json
{
    "user": {
        "id": "id here",
        "username": "Leave blank",
        "disc": "Leave blank",
        "avatar": "Leave blank",
        "bot": false,
        "status": "Unknown"
    },
    "main": true
}
```


**Response Body**

- **done** => bool [default/example = true]
- **reason** => None (unknown value type)
- **context** => None (unknown value type)



**Response Body Example**

```json
{
    "done": true,
    "reason": null,
    "context": null
}
```


**Authorization Needed** | [User](#authorization)


## Delete Bot
### DELETE `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}

Deletes a bot.

You **must** be main owner of the bot to use this endpoint.

**Path Parameters**

- **user_id** => i64 [default/example = 0]
- **bot_id** => i64 [default/example = 0]





**Response Body**

- **done** => bool [default/example = true]
- **reason** => None (unknown value type)
- **context** => None (unknown value type)



**Response Body Example**

```json
{
    "done": true,
    "reason": null,
    "context": null
}
```


**Authorization Needed** | [User](#authorization)


## Get Import Sources
### GET `https://api.fateslist.xyz`/import-sources
Returns a array of sources that a bot can be imported from.



**Response Body**

- **sources** => (Array) Struct ImportSourceListItem 
	- **id** => string [default/example = "Rdl"]
	- **name** => string [default/example = "Rovel Bot List"]






**Response Body Example**

```json
{
    "sources": [
        {
            "id": "Rdl",
            "name": "Rovel Bot List"
        }
    ]
}
```


**Authorization Needed** | None


## Import Bot
### POST `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}/import?src={source}
Imports a bot from a source listed in ``Get Import Sources``
**Query Parameters**

- **src** => string [default/example = "Rdl"]
- **custom_source** => (Optional) string [default/example = ""]




**Path Parameters**

- **user_id** => i64 [default/example = 0]
- **bot_id** => i64 [default/example = 0]




**Request Body**

- **ext_data** => (Optional) Map (key/value)  
	- **key**
 => string [default/example = "value"]






**Request Body Example**

```json
{
    "ext_data": {
        "key": "value"
    }
}
```


**Response Body**

- **done** => bool [default/example = true]
- **reason** => None (unknown value type)
- **context** => None (unknown value type)



**Response Body Example**

```json
{
    "done": true,
    "reason": null,
    "context": null
}
```


**Authorization Needed** | [User](#authorization)


