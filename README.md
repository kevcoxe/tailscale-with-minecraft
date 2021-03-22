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

`ansible-playbook start_minecraft.yml --ask-vault-pass`
