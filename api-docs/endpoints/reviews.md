
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

## Get Reviews
### GET `https://api.fateslist.xyz`/reviews/{id}

Gets reviews for a reviewable entity.

A reviewable entity is currently only a bot or a server. Profile reviews are a possibility
in the future.

``target_type`` is a [TargetType](https://lynx.fateslist.xyz/docs/endpoints/enums#targettype)

This reviewable entities id which is a ``i64`` is the id that is specifed in the
path.

``page`` must be greater than 0 or omitted (which will default to page 1).

``user_id`` is optional for this endpoint but specifying it will provide ``user_reviews`` if
the user has made a review. This will tell you the users review for the entity.

``per_page`` (amount of root/non-reply reviews per page) is currently set to 9. 
This may change in the future and is given by ``per_page`` key.

``from`` contains the index/count of the first review of the page.
**Query Parameters**

- **target_type** => i32 [ex 0]
- **page** => (Optional) i64 [ex 1]
- **user_id** => (Optional) i64 [ex 0]




**Path Parameters**

- **id** => i64 [ex 0]





**Response Body**

- **reviews** => (Array) Struct Review 
	- **id** => None (unknown value type)
	- **star_rating** => string [ex "0"]
	- **review_text** => string [ex ""]
	- **votes** => Struct ParsedReviewVotes 
		- **upvotes** => (Array) 
		- **downvotes** => (Array) 



	- **flagged** => bool [ex false]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **epoch** => (Array) 
	- **replies** => (Array) 
	- **parent_id** => None (unknown value type)



- **per_page** => i64 [ex 9]
- **from** => i64 [ex 0]
- **stats** => Struct ReviewStats 
	- **average_stars** => string [ex "8.800000"]
	- **total** => i64 [ex 78]



- **user_review** => (Optional) Struct Review 
	- **id** => None (unknown value type)
	- **star_rating** => string [ex "0"]
	- **review_text** => string [ex ""]
	- **votes** => Struct ParsedReviewVotes 
		- **upvotes** => (Array) 
		- **downvotes** => (Array) 



	- **flagged** => bool [ex false]
	- **user** => Struct User 
		- **id** => string [ex ""]
		- **username** => string [ex ""]
		- **disc** => string [ex ""]
		- **avatar** => string [ex ""]
		- **bot** => bool [ex false]
		- **status** => string [ex "Unknown"]



	- **epoch** => (Array) 
	- **replies** => (Array) 
	- **parent_id** => None (unknown value type)






**Response Body Example**

```json
{
    "reviews": [
        {
            "id": null,
            "star_rating": "0",
            "review_text": "",
            "votes": {
                "upvotes": [],
                "downvotes": []
            },
            "flagged": false,
            "user": {
                "id": "",
                "username": "",
                "disc": "",
                "avatar": "",
                "bot": false,
                "status": "Unknown"
            },
            "epoch": [],
            "replies": [],
            "parent_id": null
        }
    ],
    "per_page": 9,
    "from": 0,
    "stats": {
        "average_stars": "8.800000",
        "total": 78
    },
    "user_review": {
        "id": null,
        "star_rating": "0",
        "review_text": "",
        "votes": {
            "upvotes": [],
            "downvotes": []
        },
        "flagged": false,
        "user": {
            "id": "",
            "username": "",
            "disc": "",
            "avatar": "",
            "bot": false,
            "status": "Unknown"
        },
        "epoch": [],
        "replies": [],
        "parent_id": null
    }
}
```


**Authorization Needed** | None


## Add Review
### POST `https://api.fateslist.xyz`/reviews/{id}

Creates a review.

``id`` and ``page`` should be set to null or omitted though are ignored by this endpoint
so there should not be an error even if provided.

A reviewable entity is currently only a bot or a server. Profile reviews are a possibility
in the future.

The ``parent_id`` is optional and is used to create a reply to a review.

``target_type`` is a [TargetType](https://lynx.fateslist.xyz/docs/endpoints/enums#targettype)

``review`` is a [Review](https://lynx.fateslist.xyz/docs/endpoints/enums#review)

``user_id`` is *required* for this endpoint and must be the user making the review. It must
also match the user token sent in the ``Authorization`` header
**Query Parameters**

- **target_type** => i32 [ex 0]
- **page** => None (unknown value type)
- **user_id** => (Optional) i64 [ex 0]




**Path Parameters**

- **id** => i64 [ex 0]




**Request Body**

- **id** => None (unknown value type)
- **star_rating** => string [ex "0"]
- **review_text** => string [ex ""]
- **votes** => Struct ParsedReviewVotes 
	- **upvotes** => (Array) 
	- **downvotes** => (Array) 



- **flagged** => bool [ex false]
- **user** => Struct User 
	- **id** => string [ex ""]
	- **username** => string [ex ""]
	- **disc** => string [ex ""]
	- **avatar** => string [ex ""]
	- **bot** => bool [ex false]
	- **status** => string [ex "Unknown"]



- **epoch** => (Array) 
- **replies** => (Array) 
- **parent_id** => (Optional) string [ex "350c71b4-c5e0-4baf-ba11-89ed8a590fe6"]



**Request Body Example**

```json
{
    "id": null,
    "star_rating": "0",
    "review_text": "",
    "votes": {
        "upvotes": [],
        "downvotes": []
    },
    "flagged": false,
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "epoch": [],
    "replies": [],
    "parent_id": "350c71b4-c5e0-4baf-ba11-89ed8a590fe6"
}
```


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


## Edit Review
### PATCH `https://api.fateslist.xyz`/reviews/{id}

Edits a review.

``page`` should be set to null or omitted though are ignored by this endpoint
so there should not be an error even if provided.

A reviewable entity is currently only a bot or a server. Profile reviews are a possibility
in the future.

``target_type`` is a [TargetType](https://lynx.fateslist.xyz/docs/endpoints/enums#targettype)

This reviewable entities id which is a ``i64`` is the id that is specifed in the
path.

The id of the review must be specified as ``id`` in the request body which accepts a ``Review``
object. The ``user_id`` specified must *own*/have created the review being editted. Staff should
edit reviews using Lynx when required.

``user_id`` is *required* for this endpoint and must be the user making the review. It must
also match the user token sent in the ``Authorization`` header
**Query Parameters**

- **target_type** => i32 [ex 0]
- **page** => None (unknown value type)
- **user_id** => (Optional) i64 [ex 0]




**Path Parameters**

- **id** => i64 [ex 0]




**Request Body**

- **id** => (Optional) string [ex "1b2a9fe1-bba6-43b6-96ff-3bd05a6d31a6"]
- **star_rating** => string [ex "0"]
- **review_text** => string [ex ""]
- **votes** => Struct ParsedReviewVotes 
	- **upvotes** => (Array) 
	- **downvotes** => (Array) 



- **flagged** => bool [ex false]
- **user** => Struct User 
	- **id** => string [ex ""]
	- **username** => string [ex ""]
	- **disc** => string [ex ""]
	- **avatar** => string [ex ""]
	- **bot** => bool [ex false]
	- **status** => string [ex "Unknown"]



- **epoch** => (Array) 
- **replies** => (Array) 
- **parent_id** => None (unknown value type)



**Request Body Example**

```json
{
    "id": "1b2a9fe1-bba6-43b6-96ff-3bd05a6d31a6",
    "star_rating": "0",
    "review_text": "",
    "votes": {
        "upvotes": [],
        "downvotes": []
    },
    "flagged": false,
    "user": {
        "id": "",
        "username": "",
        "disc": "",
        "avatar": "",
        "bot": false,
        "status": "Unknown"
    },
    "epoch": [],
    "replies": [],
    "parent_id": null
}
```


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


## Delete Review
### DELETE `https://api.fateslist.xyz`/reviews/{rid}

Deletes a review

``rid`` must be a valid uuid.

``user_id`` is *required* for this endpoint and must be the user making the review. It must
also match the user token sent in the ``Authorization`` header. ``page`` is currently ignored

A reviewable entity is currently only a bot or a server. Profile reviews are a possibility
in the future.

``target_type`` is a [TargetType](https://lynx.fateslist.xyz/docs/endpoints/enums#targettype)

``target_type`` is not currently checked but it is a good idea to set it anyways. You must
set this anyways so you might as well set it correctly.
**Query Parameters**

- **target_type** => i32 [ex 0]
- **page** => None (unknown value type)
- **user_id** => (Optional) i64 [ex 0]




**Path Parameters**

- **rid** => string [ex "ba175ef7-108d-4527-8af8-2641dc391a77"]





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


## Vote Review
### PATCH `https://api.fateslist.xyz`/reviews/{rid}/votes

Creates a vote for a review

``rid`` must be a valid uuid.

``user_id`` is *required* for this endpoint and must be the user making the review. It must
also match the user token sent in the ``Authorization`` header. 

**Unlike other review APIs, ``user_id`` here is in request body as ReviewVote object**

A reviewable entity is currently only a bot or a server. Profile reviews are a possibility
in the future.

``target_type`` is a [TargetType](https://lynx.fateslist.xyz/docs/endpoints/enums#targettype)

**This endpoint does not require ``target_type`` at all. You can safely omit it**
                

**Path Parameters**

- **rid** => string [ex "a7a2fce8-51da-4446-bb5a-40f6a9cd6a04"]




**Request Body**

- **user_id** => string [ex "user id here"]
- **upvote** => bool [ex true]



**Request Body Example**

```json
{
    "user_id": "user id here",
    "upvote": true
}
```


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


