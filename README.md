# onionify
Create onion services and more in one CLI command

## Example
Create a onion service for some port on your system.

```bash
# Try to guess the torrc file location and put site data in ~/.onionify_sites/<sitename>/
$ sudo python3 onionify.py my_cool_site

# Specify torrc file and sites folder manually (in it, Tor will create a subfolder with the site name)
$ sudo python3 onionify.py my_cool_site -c /some/path/to/torrc -d /etc/my_sites/

# Generate a auth key pair for onion client authentication
$ python onionify.py generate-auth-pair > instructions.txt

Example output:

# PUBLIC KEY: Put this in your <site_folder>/authorized_clients/<some_unique_name>.auth
descriptor:x25519:46XTPPAEZFORGAVMO2V6SRWGGCMA5P7RO354ZA47LFFMRCMHNM6A
# PRIVATE KEY: Put this in your ClientOnionAuthDir with extension .auth_private, which you should specify in your client torrc. If you are using Tor Browser, you don't need to do anything manually at all, your browser will just give you a prompt to type your private key in and an option to save it in the Data/onion-auth/ folder for later use.
<your hostname here without .onion>:descriptor:x25519:IUS2IISPKMV5UOUIJUFLUKQBGZBK4PGC36S73L2FYNCNM2RLYNPQ
