
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

## Index
### GET `https://api.fateslist.xyz`/index
Returns the index for bots and servers
**Query Parameters**

- **target_type** => i32 [ex 1]






**Response Body**

- **new** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971344483Z"]



- **top_voted** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971344483Z"]



- **certified** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971344483Z"]



- **tags** => (Array) Struct Tag 
	- **name** => string [ex ""]
	- **iconify_data** => string [ex ""]
	- **id** => string [ex ""]
	- **owner_guild** => None (unknown value type)



- **features** => (Array) Struct Feature 
	- **id** => string [ex ""]
	- **name** => string [ex ""]
	- **viewed_as** => string [ex ""]
	- **description** => string [ex ""]






**Response Body Example**

```json
{
    "new": [
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
            "created_at": "2022-05-28T16:34:12.971344483Z"
        }
    ],
    "top_voted": [
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
            "created_at": "2022-05-28T16:34:12.971344483Z"
        }
    ],
    "certified": [
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
            "created_at": "2022-05-28T16:34:12.971344483Z"
        }
    ],
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
```


**Authorization Needed** | None


## Get Experiment List
### GET `https://api.fateslist.xyz`/experiments
Returns all currently available experiments



**Response Body**

- **user_experiments** => (Array) Struct UserExperimentListItem 
	- **name** => string [ex "Unknown"]
	- **value** => i32 [ex 0]






**Response Body Example**

```json
{
    "user_experiments": [
        {
            "name": "Unknown",
            "value": 0
        }
    ]
}
```


**Authorization Needed** | None


## Resolve Vanity
### GET `https://api.fateslist.xyz`/code/{code}
Resolves the vanity for a bot/server in the list

**Path Parameters**

- **code** => string [ex "my-vanity"]





**Response Body**

- **target_type** => string [ex "bot | server"]
- **target_id** => string [ex "0000000000"]



**Response Body Example**

```json
{
    "target_type": "bot | server",
    "target_id": "0000000000"
}
```


**Authorization Needed** | None


## Get Partners
### GET `https://api.fateslist.xyz`/partners
Get current partnership list



**Response Body**

- **partners** => (Array) Struct Partner 
	- **id** => string [ex "0"]
	- **name** => string [ex "My development"]
	- **owner** => string [ex "12345678901234567"]
	- **image** => string [ex ""]
	- **description** => string [ex "Some random description"]
	- **links** => Struct PartnerLinks 
		- **discord** => string [ex "https://discord.com/lmao"]
		- **website** => string [ex "https://example.com"]






- **icons** => Struct PartnerLinks 
	- **discord** => string [ex ""]
	- **website** => string [ex ""]






**Response Body Example**

```json
{
    "partners": [
        {
            "id": "0",
            "name": "My development",
            "owner": "12345678901234567",
            "image": "",
            "description": "Some random description",
            "links": {
                "discord": "https://discord.com/lmao",
                "website": "https://example.com"
            }
        }
    ],
    "icons": {
        "discord": "",
        "website": ""
    }
}
```


**Authorization Needed** | None


## Search List
### GET `https://api.fateslist.xyz`/search?q={query}

Searches the list based on a query named ``q``. 
        
Using -1 for ``gc_to`` will disable ``gc_to`` field
**Query Parameters**

- **q** => string [ex "mew"]
- **gc_from** => i64 [ex 1]
- **gc_to** => i64 [ex -1]






**Response Body**

- **bots** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971476429Z"]



- **servers** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971476696Z"]



- **profiles** => (Array) Struct SearchProfile 
	- **banner** => string [ex ""]
	- **description** => string [ex ""]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]






- **packs** => (Array) Struct BotPack 
	- **id** => string [ex "0"]
	- **name** => string [ex ""]
	- **description** => string [ex ""]
	- **icon** => string [ex ""]
	- **banner** => string [ex ""]
	- **resolved_bots** => (Array) Struct ResolvedPackBot 
		- **user** => Struct User 
			- **id** => string [ex ""]
			- **username** => string [ex ""]
			- **disc** => string [ex ""]
			- **avatar** => string [ex ""]
			- **bot** => bool [ex false]
			- **status** => string [ex "Unknown"]



		- **description** => string [ex ""]



	- **owner** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **created_at** => string [ex "1970-01-01T00:00:00Z"]



- **tags** => Struct SearchTags 
	- **bots** => (Array) Struct Tag 
		- **name** => string [ex ""]
		- **iconify_data** => string [ex ""]
		- **id** => string [ex ""]
		- **owner_guild** => None (unknown value type)



	- **servers** => (Array) Struct Tag 
		- **name** => string [ex ""]
		- **iconify_data** => string [ex ""]
		- **id** => string [ex ""]
		- **owner_guild** => None (unknown value type)









**Response Body Example**

```json
{
    "bots": [
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
            "created_at": "2022-05-28T16:34:12.971476429Z"
        }
    ],
    "servers": [
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
            "created_at": "2022-05-28T16:34:12.971476696Z"
        }
    ],
    "profiles": [
        {
            "banner": "",
            "description": "",
            "user": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            }
        }
    ],
    "packs": [
        {
            "id": "0",
            "name": "",
            "description": "",
            "icon": "",
            "banner": "",
            "resolved_bots": [
                {
                    "user": {
                        "id": "",
                        "username": "",
                        "disc": "",
                        "avatar": "",
                        "bot": false,
                        "status": "Unknown"
                    },
                    "description": ""
                }
            ],
            "owner": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            },
            "created_at": "1970-01-01T00:00:00Z"
        }
    ],
    "tags": {
        "bots": [
            {
                "name": "",
                "iconify_data": "",
                "id": "",
                "owner_guild": null
            }
        ],
        "servers": [
            {
                "name": "",
                "iconify_data": "",
                "id": "",
                "owner_guild": null
            }
        ]
    }
}
```


**Authorization Needed** | None


## Search Tags
### GET `https://api.fateslist.xyz`/search-tags?q={query}
Searches the list based on a tag named ``q``.
**Query Parameters**

- **q** => string [ex "mew"]






**Response Body**

- **bots** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971516287Z"]



- **servers** => (Array) Struct IndexBot 
	- **guild_count** => i64 [ex 30]
	- **description** => string [ex "My description"]
	- **banner** => string [ex "My banner or default banner url"]
	- **votes** => i64 [ex 40]
	- **state** => i32 [ex 3]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **flags** => (Array) 
	- **created_at** => string [ex "2022-05-28T16:34:12.971516506Z"]



- **profiles** => (Array) Struct SearchProfile 
	- **banner** => string [ex ""]
	- **description** => string [ex ""]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]






- **packs** => (Array) Struct BotPack 
	- **id** => string [ex "0"]
	- **name** => string [ex ""]
	- **description** => string [ex ""]
	- **icon** => string [ex ""]
	- **banner** => string [ex ""]
	- **resolved_bots** => (Array) Struct ResolvedPackBot 
		- **user** => Struct User 
			- **id** => string [ex ""]
			- **username** => string [ex ""]
			- **disc** => string [ex ""]
			- **avatar** => string [ex ""]
			- **bot** => bool [ex false]
			- **status** => string [ex "Unknown"]



		- **description** => string [ex ""]



	- **owner** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **created_at** => string [ex "1970-01-01T00:00:00Z"]



- **tags** => Struct SearchTags 
	- **bots** => (Array) Struct Tag 
		- **name** => string [ex ""]
		- **iconify_data** => string [ex ""]
		- **id** => string [ex ""]
		- **owner_guild** => None (unknown value type)



	- **servers** => (Array) Struct Tag 
		- **name** => string [ex ""]
		- **iconify_data** => string [ex ""]
		- **id** => string [ex ""]
		- **owner_guild** => None (unknown value type)









**Response Body Example**

```json
{
    "bots": [
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
            "created_at": "2022-05-28T16:34:12.971516287Z"
        }
    ],
    "servers": [
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
            "created_at": "2022-05-28T16:34:12.971516506Z"
        }
    ],
    "profiles": [
        {
            "banner": "",
            "description": "",
            "user": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            }
        }
    ],
    "packs": [
        {
            "id": "0",
            "name": "",
            "description": "",
            "icon": "",
            "banner": "",
            "resolved_bots": [
                {
                    "user": {
                        "id": "",
                        "username": "",
                        "disc": "",
                        "avatar": "",
                        "bot": false,
                        "status": "Unknown"
                    },
                    "description": ""
                }
            ],
            "owner": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            },
            "created_at": "1970-01-01T00:00:00Z"
        }
    ],
    "tags": {
        "bots": [
            {
                "name": "",
                "iconify_data": "",
                "id": "",
                "owner_guild": null
            }
        ],
        "servers": [
            {
                "name": "",
                "iconify_data": "",
                "id": "",
                "owner_guild": null
            }
        ]
    }
}
```


**Authorization Needed** | None


## Mini Index
### GET `https://api.fateslist.xyz`/mini-index

Returns a mini-index which is basically a Index but with only ``tags``
and ``features`` having any data. Other fields are empty arrays/vectors.

This is used internally by sunbeam for the add bot system where a full bot
index is too costly and making a new struct is unnecessary.
                



**Response Body**

- **new** => (Array) 
- **top_voted** => (Array) 
- **certified** => (Array) 
- **tags** => (Array) Struct Tag 
	- **name** => string [ex ""]
	- **iconify_data** => string [ex ""]
	- **id** => string [ex ""]
	- **owner_guild** => None (unknown value type)



- **features** => (Array) Struct Feature 
	- **id** => string [ex ""]
	- **name** => string [ex ""]
	- **viewed_as** => string [ex ""]
	- **description** => string [ex ""]






**Response Body Example**

```json
{
    "new": [],
    "top_voted": [],
    "certified": [],
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
```


**Authorization Needed** | None


