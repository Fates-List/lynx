
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

## Add Pack
### POST `https://api.fateslist.xyz`/users/{id}/packs

Creates a bot pack. 

- Set ``id`` to empty string, 
- Set ``created_at`` to any datetime
- In user and bot, only ``id`` must be filled, all others can be left empty string
but must exist in the object

**Path Parameters**

- **id** => i64 [default/example = 0]




**Request Body**

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



**Request Body Example**

```json
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


