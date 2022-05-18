
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

## Get OAuth2 Link
### GET `https://api.fateslist.xyz`/oauth2





**Response Body**

- **done** => bool [default/example = true]
- **reason** => None (unknown value type)
- **context** => (Optional) string [default/example = "https://discord.com/........."]



**Response Body Example**

```json
{
    "done": true,
    "reason": null,
    "context": "https://discord.com/........."
}
```


**Authorization Needed** | None


## Get Frostpaw Client
### GET `https://api.fateslist.xyz`/frostpaw/clients/{id}



**Path Parameters**

- **id** => string [default/example = "client id here"]







**Response Body**

- **id** => string [default/example = ""]
- **name** => string [default/example = ""]
- **domain** => string [default/example = ""]
- **privacy_policy** => string [default/example = ""]
- **owner** => Struct User 
	- **id** => string [default/example = ""]
	- **username** => string [default/example = ""]
	- **disc** => string [default/example = ""]
	- **avatar** => string [default/example = ""]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]






**Response Body Example**

```json
{
    "id": "",
    "name": "",
    "domain": "",
    "privacy_policy": "",
    "owner": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    }
}
```


**Authorization Needed** | None


## Refresh Frostpaw Token
### POST `https://api.fateslist.xyz`/frostpaw/clients/{client_id}/refresh



**Path Parameters**

- **id** => string [default/example = "client id here"]







**Response Body**

- **done** => bool [default/example = true]
- **reason** => (Optional) string [default/example = "Error code, if any"]
- **context** => (Optional) string [default/example = "Refresh token, if everything went ok :)"]



**Response Body Example**

```json
{
    "done": true,
    "reason": "Error code, if any",
    "context": "Refresh token, if everything went ok :)"
}
```


**Authorization Needed** | None


## Create OAuth2 Login
### POST `https://api.fateslist.xyz`/oauth2




**Request Body**

- **code** => string [default/example = "code from discord oauth"]
- **state** => (Optional) string [default/example = "Random UUID right now"]
- **frostpaw** => bool [default/example = true]
- **frostpaw_blood** => None (unknown value type)
- **frostpaw_claw** => None (unknown value type)
- **frostpaw_claw_unseathe_time** => None (unknown value type)



**Request Body Example**

```json
{
    "code": "code from discord oauth",
    "state": "Random UUID right now",
    "frostpaw": true,
    "frostpaw_blood": null,
    "frostpaw_claw": null,
    "frostpaw_claw_unseathe_time": null
}
```




**Response Body**

- **state** => i32 [default/example = 0]
- **token** => string [default/example = ""]
- **refresh_token** => None (unknown value type)
- **user** => Struct User 
	- **id** => string [default/example = ""]
	- **username** => string [default/example = ""]
	- **disc** => string [default/example = ""]
	- **avatar** => string [default/example = ""]
	- **bot** => bool [default/example = false]
	- **status** => string [default/example = "Unknown"]



- **site_lang** => string [default/example = ""]
- **css** => None (unknown value type)
- **user_experiments** => (Array) 



**Response Body Example**

```json
{
    "state": 0,
    "token": "",
    "refresh_token": null,
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "site_lang": "",
    "css": null,
    "user_experiments": []
}
```


**Authorization Needed** | None


## Delete OAuth2 Login
### DELETE `https://api.fateslist.xyz`/oauth2





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


**Authorization Needed** | None


