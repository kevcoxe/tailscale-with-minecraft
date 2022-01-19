### Why

I wanted to setup a minecraft server and have it accessible through my tailscale tunnel.
This will install tailscale and start it up using an auth key.

### Setup

This will work with either ubuntu 16.04 or 20.04.

You can also choose between a minecraft java server or bedrock server.


### Running

after creating the vault secrets 

- `vars/minecraft-secrets.yml`
- `vars/tailscale-secrets.yml`

Next you need to create an `inventory` file

`inventory`
```
[minecraft]
<the ip of your minefraft server>
```

You can run install via

`ansible-playbook start_minecraft.yml`


encrypting secrets

```
$ bin/secret_mgmt.py secrets encrypt-string
String (end with newline + Control+D): pass123
Encrypting string
!vault |
          $ANSIBLE_VAULT;1.2;AES256;/ops/ansible-vault:secret-20210430
          61333033616230656339303061353833663837343238306461323561653461613132616263353231
          3161383738343531343838326162396634363339646263630a623161333063323531346337353266
          30306639666332336563653934643733376236376562633339653930376430393332363333646130
          3639306339363262300a616136376131666134316637303037333566366337633836613862393264
          3131
```

decrypting secrets from a file

```
$ bin/secret_mgmt.py secrets decrypt-string-in-file vars/minecraft-secrets.yml minecraft_user
pi%
```