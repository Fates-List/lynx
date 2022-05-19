
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

## Create Bot Appeal
### POST `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}/appeal

Creates a appeal for a bot.

``request_type`` is a [AppealType](./enums#appealtype)
                

**Path Parameters**

- **user_id** => i64 [default/example = 0]
- **bot_id** => i64 [default/example = 0]




**Request Body**

- **request_type** => i32 [default/example = 0]
- **appeal** => string [default/example = "This bot deserves to be unbanned because..."]



**Request Body Example**

```json
{
    "request_type": 0,
    "appeal": "This bot deserves to be unbanned because..."
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


## Create Server Appeal
### POST `https://api.fateslist.xyz`/users/{user_id}/servers/{server_id}/appeal

Creates a appeal for a server.

**Currently only `report` is supported by this endpoint**

``request_type`` is a [AppealType](./enums#appealtype)
                

**Path Parameters**

- **user_id** => i64 [default/example = 0]
- **server_id** => i64 [default/example = 0]




**Request Body**

- **request_type** => i32 [default/example = 0]
- **appeal** => string [default/example = "This server deserves to be unbanned because..."]



**Request Body Example**

```json
{
    "request_type": 0,
    "appeal": "This server deserves to be unbanned because..."
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


