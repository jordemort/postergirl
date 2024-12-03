from mastodon import Mastodon  # type: ignore


def create_app(instance_url: str, app_name: str = "Postergirl") -> tuple[str, str]:
    return Mastodon.create_app(  # type: ignore
        app_name, api_base_url=instance_url
    )


def make_access_token(
    instance_url: str,
    client_id: str,
    client_secret: str,
    username: str,
    password: str,
) -> str:
    client = Mastodon(
        client_id=client_id, client_secret=client_secret, api_base_url=instance_url
    )

    return client.log_in(  # type: ignore
        username=username,
        password=password,
    )
