from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from jwt.exceptions import InvalidSignatureError
from rest_framework_jwt.authentication import jwt_decode_handler

User = get_user_model()


@database_sync_to_async
def get_user(token_key):
    try:
        payload = jwt_decode_handler(token_key)
    except InvalidSignatureError:
        return AnonymousUser()
    if User.objects.filter(id=payload["user_id"], is_active=True).exists():
        return User.objects.get(id=payload["user_id"])
    else:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    async def __call__(self, scope, receive, send):
        try:
            headers = {i[0].decode(): i[1].decode() for i in scope["headers"]}
            query_params = scope["query_string"].decode()
            if query_params != "":
                token_key = query_params.replace("tk=", "")
            else:
                token_key = headers["authorization"].replace("Bearer ", "")
            # token_key = (dict((x.split('=') for x in scope['query_string'].decode().split("&")))).get('token', None)
        except ValueError:
            token_key = None
        except KeyError:
            token_key = None
        scope['user'] = AnonymousUser() if token_key is None else await get_user(token_key)
        return await super().__call__(scope, receive, send)
