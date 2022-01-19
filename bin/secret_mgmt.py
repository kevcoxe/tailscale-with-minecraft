#!/usr/bin/env python3

import re
import subprocess
import sys

from ansible.parsing.vault import VaultLib
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import ClientScriptVaultSecret
from ansible.config.manager import ConfigManager
import click
from ruamel.yaml import YAML
from ruamel.yaml import comments


@click.group(name="secrets", help="Secret management utilities.", chain=True)
def secrets():
    pass


@secrets.command(name='encrypt-string')
#@click.argument('vault_password_file', type=click.Path(exists=True))
@click.argument('string', required=False)
def encrypt_string(string):
    """Encrypt a string"""
    #import pdb;pdb.set_trace()
    if not string:
        if sys.stdin.isatty():
            print("String (end with newline + Control+D): ", end="")
            sys.stdout.flush()
        # NOTE(stpierre): we don't want to use input() here because
        # input() reads to a newline; we want to read until EOF for
        # multi-line strings.
        string = click.get_text_stream('stdin').read()
        # for some reason this now gets trailing newlines
        string = string.rstrip()
    #cmd = ("ansible-vault", "encrypt_string", "--vault-password-file",
    #       vault_password_file, "--", string)
    click.echo("Encrypting string")
    cmd = ("ansible-vault", "encrypt_string", "--", string)
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    result, stderr = proc.communicate()
    retval = proc.wait()
    if retval != 0:
        click.secho(str(stderr), fg='red')
        sys.exit(retval)

    click.secho(result.strip().decode(), fg='green')


@secrets.command(name='decrypt-string-in-file')
@click.argument('inventory_file', type=click.Path(exists=True))
@click.argument('yaml_key')
def decrypt_string_in_file(inventory_file, yaml_key):
    """Decrypt an inline encrypted string in an inventory file

    The passed YAML_KEY is the name of the variable to decrypt (e.g. 'my_key').
    It can also be the dot-separated keys of the dictionary containing the
    variable to decrypt if the encrypted value embedded in a dictionary
    structure.
    For example the key 'key_a.key_b' can be used to decrypt the key present
    in a file containing:

    \b
    key_a:
      key_b: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          6163<encrypted_content>334
    """
    config_manager = ConfigManager()
    vault_identity_list = config_manager.data.get_setting('DEFAULT_VAULT_IDENTITY_LIST')
    (vault_id, vault_script) = vault_identity_list.value[0].split('@')
    yaml = YAML()
    parsed = yaml.load(open(click.format_filename(inventory_file)).read())
    sub_tree = parsed
    for key in yaml_key.split('.'):
        sub_tree = sub_tree[key]
    if isinstance(sub_tree, comments.TaggedScalar):
        # Cope with dictionary exploration which returns a
        # ruamel.yaml.comments.TaggedScalar.
        key = sub_tree.value
    else:
        key = sub_tree

    # Use ansible directly to avoid additional formatting resulting from
    # shell-based execution or tty-related problems.
    #secret = FileVaultSecret(vault_password_file, loader=DataLoader())
    secret = ClientScriptVaultSecret(filename=vault_script, vault_id=vault_id, loader=DataLoader())
    secret.load()
    vault = VaultLib([(u'default', secret)])
    result = vault.decrypt(key)

    click.secho(result.decode(), fg='green', nl=False)


def _ensure_encrypted_secrets(tree, skip_patterns, filename, prefix=''):
    unencrypted = 0
    for key, value in tree.items():
        print(key)
        if isinstance(value, comments.TaggedScalar):
            # NOTE(stpierre): data is encrypted, so all's well
            continue
        elif any(p.match(key) for p in skip_patterns):
            # NOTE(stpierre): we can safely skip this item; it's a username or
            # something that doesn't need to be encrypted
            continue
        elif isinstance(value, dict):
            unencrypted += _ensure_encrypted_secrets(value,
                                                     skip_patterns,
                                                     filename,
                                                     prefix="%s%s." %
                                                     (prefix, key))
        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, comments.TaggedScalar):
                    click.secho("%s: Found unencrypted item in list %s%s" %
                                (filename, prefix, key),
                                fg="red")
                    unencrypted += 1
        elif type(value) is not int and value.startswith("{{") and value.endswith("}}"):
            # NOTE(stpierre): jinja2 templated value, so doesn't need to be
            # encrypted
            continue
        else:
            click.secho("%s: Found unencrypted item %s%s" %
                        (filename, prefix, key),
                        fg="red")
            unencrypted += 1
    return unencrypted


@secrets.command(name="precommit")
@click.option("--config-file",
              default="precommit-config.yml",
              type=click.Path(exists=True),
              help="Path to precommit hook config file")
@click.argument("inventory_file", type=click.Path(exists=True))
def precommit_hook(config_file, inventory_file):
    yaml = YAML()
    config = yaml.load(open(click.format_filename(config_file)).read())
    skip_patterns = []
    for pattern in config.get("skip_patterns", []):
        skip_patterns.append(re.compile(pattern))

    inv_filename = click.format_filename(inventory_file)
    data = yaml.load(open(inv_filename).read())
    unencrypted = _ensure_encrypted_secrets(data, skip_patterns, inv_filename)
    if unencrypted != 0:
        click.secho("%s: %s unencrypted item(s) found, aborting commit" %
                    (inv_filename, unencrypted),
                    fg="red")
        sys.exit(2)

@click.group()
def cli():
    """ This is our CLI """

cli.add_command(secrets)

if __name__ == '__main__':
    cli()
