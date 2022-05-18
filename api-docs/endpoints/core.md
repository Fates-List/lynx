
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


**Query Parameters**

- **target_type** => i32 [default/example = 1]








**Response Body**

- **new** => (Array) Struct IndexBot 
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
	- **created_at** => string [default/example = "2022-05-18T13:24:20.402898826Z"]



- **top_voted** => (Array) Struct IndexBot 
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
	- **created_at** => string [default/example = "2022-05-18T13:24:20.402898826Z"]



- **certified** => (Array) Struct IndexBot 
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
	- **created_at** => string [default/example = "2022-05-18T13:24:20.402898826Z"]



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
            "created_at": "2022-05-18T13:24:20.402898826Z"
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
            "created_at": "2022-05-18T13:24:20.402898826Z"
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
            "created_at": "2022-05-18T13:24:20.402898826Z"
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


## Experiment List
### GET `https://api.fateslist.xyz`/experiments





**Response Body**

- **user_experiments** => (Array) Struct UserExperimentListItem 
	- **name** => string [default/example = "Unknown"]
	- **value** => i32 [default/example = 0]






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



**Path Parameters**

- **code** => string [default/example = "my-vanity"]







**Response Body**

- **target_type** => string [default/example = "bot | server"]
- **target_id** => string [default/example = "0000000000"]



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





**Response Body**

- **partners** => (Array) Struct Partner 
	- **id** => string [default/example = "0"]
	- **name** => string [default/example = "My development"]
	- **owner** => string [default/example = "12345678901234567"]
	- **image** => string [default/example = ""]
	- **description** => string [default/example = "Some random description"]
	- **links** => Struct PartnerLinks 
		- **discord** => string [default/example = "https://discord.com/lmao"]
		- **website** => string [default/example = "https://example.com"]






- **icons** => Struct PartnerLinks 
	- **discord** => string [default/example = ""]
	- **website** => string [default/example = ""]






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


## Preview Description
### WS `https://api.fateslist.xyz`/ws/_preview




**Request Body**

- **text** => string [default/example = ""]
- **long_description_type** => i32 [default/example = 1]



**Request Body Example**

```json
{
    "text": "",
    "long_description_type": 1
}
```




**Response Body**

- **preview** => string [default/example = ""]



**Response Body Example**

```json
{
    "preview": ""
}
```


**Authorization Needed** | None


## Search List
### GET `https://api.fateslist.xyz`/search?q={query}


**Query Parameters**

- **q** => string [default/example = "mew"]
- **gc_from** => i64 [default/example = 1]
- **gc_to** => i64 [default/example = -1]








**Query Parameters**

- **bots** => (Array) Struct IndexBot 
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
	- **created_at** => string [default/example = "2022-05-18T13:24:20.403041743Z"]



- **servers** => (Array) Struct IndexBot 
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
	- **created_at** => string [default/example = "2022-05-18T13:24:20.403044644Z"]



- **profiles** => (Array) Struct SearchProfile 
	- **banner** => string [default/example = ""]
	- **description** => string [default/example = ""]
	- **user** => Struct User 
		- **id** => string [default/example = ""]
		- **username** => string [default/example = ""]
		- **disc** => string [default/example = ""]
		- **avatar** => string [default/example = ""]
		- **bot** => bool [default/example = false]
		- **status** => string [default/example = "Unknown"]






- **packs** => (Array) Struct BotPack 
	- **id** => string [default/example = "0"]
	- **name** => string [default/example = ""]
	- **description** => string [default/example = ""]
	- **icon** => string [default/example = ""]
	- **banner** => string [default/example = ""]
	- **resolved_bots** => (Array) Struct ResolvedPackBot 
		- **user** => Struct User 
			- **id** => string [default/example = ""]
			- **username** => string [default/example = ""]
			- **disc** => string [default/example = ""]
			- **avatar** => string [default/example = ""]
			- **bot** => bool [default/example = false]
			- **status** => string [default/example = "Unknown"]



		- **description** => string [default/example = ""]



	- **owner** => Struct User 
		- **id** => string [default/example = ""]
		- **username** => string [default/example = ""]
		- **disc** => string [default/example = ""]
		- **avatar** => string [default/example = ""]
		- **bot** => bool [default/example = false]
		- **status** => string [default/example = "Unknown"]



	- **created_at** => string [default/example = "1970-01-01T00:00:00Z"]



- **tags** => Struct SearchTags 
	- **bots** => (Array) Struct Tag 
		- **name** => string [default/example = ""]
		- **iconify_data** => string [default/example = ""]
		- **id** => string [default/example = ""]
		- **owner_guild** => None (unknown value type)



	- **servers** => (Array) Struct Tag 
		- **name** => string [default/example = ""]
		- **iconify_data** => string [default/example = ""]
		- **id** => string [default/example = ""]
		- **owner_guild** => None (unknown value type)










**Authorization Needed** | None


## Mini Index
### GET `https://api.fateslist.xyz`/mini-index





**Response Body**

- **new** => (Array) 
- **top_voted** => (Array) 
- **certified** => (Array) 
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


