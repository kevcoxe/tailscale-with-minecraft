#!/usr/bin/env python3

# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developers/getting-started/python/

import argparse
import base64
import boto3
import json
import os
import sys
from botocore.exceptions import ClientError, NoRegionError

from ansible.config.manager import ConfigManager


def build_arg_parser():
    parser = argparse.ArgumentParser(description='Get a vault password from user keyring')

    parser.add_argument('--vault-id', action='store', default=None,
                        dest='vault_id',
                        help='name of the vault secret to get from keyring')
    return parser

def get_secret(secret_name, entry):

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
    )


    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    # the secret is json stored as a string
    secret_decoded = json.loads(secret)
    return(secret_decoded[entry])


#print(sys.argv, file=sys.stderr)
def main():
  config_manager = ConfigManager()
  arg_parser = build_arg_parser()
  args = arg_parser.parse_args()
  (secret_name, secret_entry) = args.vault_id.split(':')
  try:
    secret = get_secret(secret_name, secret_entry)
    sys.stdout.write('%s\n' % secret)
  except NoRegionError:
    print("Error: Must have your AWS region set", file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    main()