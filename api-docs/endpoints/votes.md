
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

## Create Bot Vote
### PATCH `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}/votes
This endpoint creates a vote for a bot which can only be done *once* every 8 hours.
**Query Parameters**

- **test** => bool [ex true]




**Path Parameters**

- **user_id** => i64 [ex 0]
- **bot_id** => i64 [ex 0]





**Response Body**

- **done** => bool [ex false]
- **reason** => (Optional) string [ex "Error code"]
- **context** => (Optional) string [ex "Some context on the error"]



**Response Body Example**

```json
{
    "done": false,
    "reason": "Error code",
    "context": "Some context on the error"
}
```


**Authorization Needed** | [User](#authorization)


## Create Server Vote
### PATCH `https://api.fateslist.xyz`/users/{user_id}/servers/{server_id}/votes

This endpoint creates a vote for a server which can only be done *once* every 8 hours
and is independent from a bot vote.
                    
**Query Parameters**

- **test** => bool [ex true]




**Path Parameters**

- **user_id** => i64 [ex 0]
- **server_id** => i64 [ex 0]





**Response Body**

- **done** => bool [ex false]
- **reason** => (Optional) string [ex "Why the vote failed or any extra info to send to client if the vote succeeded"]
- **context** => (Optional) string [ex "Some context on the vote"]



**Response Body Example**

```json
{
    "done": false,
    "reason": "Why the vote failed or any extra info to send to client if the vote succeeded",
    "context": "Some context on the vote"
}
```


**Authorization Needed** | [User](#authorization)


## Get Bot Votes
### GET `https://api.fateslist.xyz`/users/{user_id}/bots/{bot_id}/votes

Endpoint to check amount of votes a user has.

- votes | The amount of votes the bot has.
- voted | Whether or not the user has *ever* voted for a bot in the past 8 hours.
- timestamps | A list of timestamps that the user has voted for the bot on that has been recorded.
- expiry | The time when the user can next vote.
- vote_right_now | Whether a user can vote right now. Currently equivalent to `vote_epoch < 0`.

- Unlike API v2, this *does not* require authorization to use. This is to speed up responses and 
because the last thing people want to scrape are Fates List user votes anyways. **You should not rely on
this however, it is prone to change *anytime* in the future and may return bogus results for privacy purposes**.
- ``vts`` has been renamed to ``timestamps``

**This endpoint will return bogus data if "Hide votes to other users" is enabled**

**Path Parameters**

- **user_id** => i64 [ex 0]
- **bot_id** => i64 [ex 0]





**Response Body**

- **votes** => i64 [ex 10]
- **voted** => bool [ex true]
- **vote_right_now** => bool [ex false]
- **expiry** => u64 [ex 101]
- **timestamps** => (Array) string [ex "1970-01-01T00:00:00Z"]



**Response Body Example**

```json
{
    "votes": 10,
    "voted": true,
    "vote_right_now": false,
    "expiry": 101,
    "timestamps": [
        "1970-01-01T00:00:00Z"
    ]
}
```


**Authorization Needed** | None


## Get Server Votes
### GET `https://api.fateslist.xyz`/users/{user_id}/servers/{server_id}/votes

Endpoint to check amount of votes a user has.

- votes | The amount of votes the server has.
- voted | Whether or not the user has *ever* voted for a server in the past 8 hours.
- timestamps | A list of timestamps that the user has voted for the server on that has been recorded.
- expiry | The time when the user can next vote.
- vote_right_now | Whether a user can vote right now. Currently equivalent to `vote_epoch < 0`.
                
- Unlike API v2, this does not require authorization to use. This is to speed up responses and 
because the last thing people want to scrape are Fates List user votes anyways. **You should not rely on
this however, it is prone to change *anytime* in the future and may return bogus results for privacy purposes**.
- ``vts`` has been renamed to ``timestamps``

**This endpoint will return bogus data if "Hide votes to other users" is enabled**

**Path Parameters**

- **user_id** => i64 [ex 0]
- **server_id** => i64 [ex 0]





**Response Body**

- **votes** => i64 [ex 10]
- **voted** => bool [ex true]
- **vote_right_now** => bool [ex false]
- **expiry** => u64 [ex 101]
- **timestamps** => (Array) string [ex "1970-01-01T00:00:00Z"]



**Response Body Example**

```json
{
    "votes": 10,
    "voted": true,
    "vote_right_now": false,
    "expiry": 101,
    "timestamps": [
        "1970-01-01T00:00:00Z"
    ]
}
```


**Authorization Needed** | None


