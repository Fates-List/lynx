
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

## New Bot Token
### DELETE `https://api.fateslist.xyz`/bots/{id}/token

'Deletes' a bot token and reissues a new bot token. Use this if your bots
token ever gets leaked! Also used by the official client

**Path Parameters**

- **id** => i64 [ex 0]





**Response Body**

- **done** => bool [ex true]
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


**Authorization Needed** | [Bot](#authorization)


## New User Token
### DELETE `https://api.fateslist.xyz`/users/{id}/token

'Deletes' a user token and reissues a new user token. Use this if your bots
token ever gets leaked! Also used by the official client

**Path Parameters**

- **id** => i64 [ex 0]





**Response Body**

- **done** => bool [ex true]
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


## New Server Token
### DELETE `https://api.fateslist.xyz`/servers/{id}/token

'Deletes' a server token and reissues a new server token. Use this if your server
token ever gets leaked.

**Path Parameters**

- **id** => i64 [ex 0]





**Response Body**

- **done** => bool [ex true]
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


**Authorization Needed** | [Server](#authorization)


## Revoke Frostpaw Client Auth
### DELETE `https://api.fateslist.xyz`/users/{id}/frostpaw/clients/{client_id}

'Deletes' a user token and reissues a new user token. Use this if your user
token ever gets leaked.
                

**Path Parameters**

- **id** => i64 [ex 0]
- **client_id** => string [ex "client_id"]





**Response Body**

- **done** => bool [ex true]
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


