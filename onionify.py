import pystache
from pathlib import Path

from nacl.public import PrivateKey
from typer import Typer, Option
import base64

app = Typer()

START_HEADER = "### ONION SITE '{}' ###"
END_HEADER = "### END ONION SITE '{}' ###"
SITE_TEMPLATE = Path("torrc.tmpl").read_text()


def get_hostname(name: str, site_dir: str):
    return Path(site_dir, name, "hostname").read_text().strip()


def get_site_dir():
    site_dir = Path.home() / ".onionify_sites"
    site_dir.mkdir(mode=0o660, exist_ok=True)
    return site_dir


def get_torrc():
    torrc_paths = [
        "/etc/tor/torrc",  # Default debian path
        Path(Path.home(), "../usr/etc/tor/torrc")  # Termux
    ]
    for path in torrc_paths:
        path = Path(path)
        if path.exists():
            return path


@app.command(
    help="Adds a few lines to your torrc to allow authentication"
)
def add(
    name: str,
    torrc_path: str = Option(None, "-c", "--torrc"),
    site_dir: str = Option(None, "-d", "--site-dir"),
    host: str = "127.0.0.1",
    real_port: int = 80,
    tor_port: int = 80,
):
    site_dir = site_dir or get_site_dir()
    torrc_path = torrc_path or get_torrc()

    config = torrc_path.read_bytes()
    start = START_HEADER.format(name).encode()
    end = END_HEADER.format(name).encode()
    new_onion_config = (
        pystache.render(
            SITE_TEMPLATE,
            context={
                "webserver_dir": str(Path(site_dir, name).absolute()),
                "tor_port": tor_port,
                "real_port": real_port,
                "host": host,
            },
        )
        .encode()
        .strip()
    )
    if start in config and end in config:
        config = bytearray(config)
        config[config.find(start) + len(start) : config.find(end)] = (
            b"\n" + new_onion_config + b"\n"
        )
    else:
        config = config.strip()
        config += b"\n\n"
        config += start + b"\n"
        config += new_onion_config
        config += b"\n" + end + b"\n"

    torrc_path.write_bytes(config)


@app.command(help="Generates a authentication pair for a onion service")
def generate_auth_pair(
    name_or_hosthame: str = Option(
        None,
        "-n",
        "--name-or-hostname",
        help="In this option you can specify a onionify site name, "
        "which it will try to automaticly resolve into a hostname, "
        "or you can specify the hostname yourself",
    ),
    add_key: bool = Option(False, "-a", "--add-key", help="Adds this key to your list of authorized clients."),

    site_dir: str = Option(None, "-d", "--site-dir"),
):
    site_dir = site_dir or get_site_dir()

    # Original code can be found here: https://github.com/pastly/python-snippits

    def key_str(key):
        key_bytes = bytes(key)
        key_b32 = base64.b32encode(key_bytes)
        key_b32 = key_b32[:-4]
        s = key_b32.decode("utf-8")
        return s

    priv_key = PrivateKey.generate()
    pub_key = priv_key.public_key
    auth_public = f"descriptor:x25519:{key_str(pub_key)}"
    print(
        "# PUBLIC KEY: Put this in your <site_folder>/authorized_clients/<some_unique_name>.auth"
    )
    if add_key:
        key_path = Path(site_dir, name_or_hosthame, "authorized_clients", key_str(pub_key)[:8] + ".auth")
        key_path.write_text(auth_public)
        print(f"# Wrote the key to {key_path.absolute()}. It should be automatically recognized by tor")
    print(auth_public)
    print(
        "# PRIVATE KEY: Put this in your ClientOnionAuthDir with extension .auth_private, "
        "which you should specify in your client torrc. If you are using Tor Browser, "
        "you don't need to do anything manually at all, your browser will just give you "
        "a prompt to type your private key in and an option to save it in "
        "the Data/onion-auth/ folder for later use."
    )
    if name_or_hosthame is None:
        hostname = "<your hostname here without .onion>"
    elif name_or_hosthame.endswith(".onion"):
        hostname = name_or_hosthame
    else:
        hostname = get_hostname(name_or_hosthame, site_dir).replace(".onion", "")
    auth_private = f"{hostname}:descriptor:x25519:{key_str(priv_key)}"
    print(auth_private)


@app.command(
    help="Removes a site from the config. Does not delete the site folder for safety reasons."
)
def remove(name: str, torrc_path: str = Option(None, "-c", "--torrc")):
    torrc_path = torrc_path or get_torrc()

    config = torrc_path.read_bytes()
    start = START_HEADER.format(name).encode()
    end = END_HEADER.format(name).encode()

    if start in config and end in config:
        config = bytearray(config)
        config[config.find(start) + len(start) : config.find(end)] = b"\n\n"
        torrc_path.write_bytes(config)
    else:
        print(f"Site '{name}' not found.")


if __name__ == "__main__":
    app()
