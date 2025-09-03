# core/api_schemas.py
from rest_framework import serializers

# --- Base envelope
class EnvelopeSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    error = serializers.JSONField(allow_null=True, required=False)
    data = serializers.JSONField(allow_null=True, required=False)


# --- Auth small pieces
class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


# --- Users pieces (reuse your app serializers)
# We avoid circular import by importing inside wrappers where needed.

# Envelope: { data: { user: UserPrivate } }
def UserPrivateEnvelopeSerializer():
    from users.api.serializers import UserPrivateSerializer

    class _Data(serializers.Serializer):
        user = UserPrivateSerializer()

    class _Env(EnvelopeSerializer):
        data = _Data()

    return _Env


# Envelope: { data: TokenPair }
class TokensEnvelopeSerializer(EnvelopeSerializer):
    data = TokenPairSerializer()


# Envelope: OK with data: null
class OkEnvelopeSerializer(EnvelopeSerializer):
    pass


# Envelope: list pagination for public users under data.results
def PublicUsersListEnvelopeSerializer():
    from users.api.serializers import UserPublicSerializer

    class _ListData(serializers.Serializer):
        count = serializers.IntegerField()
        page = serializers.IntegerField()
        page_size = serializers.IntegerField()
        results = UserPublicSerializer(many=True)

    class _Env(EnvelopeSerializer):
        data = _ListData()

    return _Env


# Envelope: single public user (not paginated)
def PublicUserEnvelopeSerializer():
    from users.api.serializers import UserPublicSerializer

    class _Env(EnvelopeSerializer):
        data = UserPublicSerializer()

    return _Env
