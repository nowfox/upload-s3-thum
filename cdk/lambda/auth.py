import json
import boto3
import os

ak = os.environ['ak']
sk = os.environ['sk']

def handler(event, context):
    sts = boto3.client('sts',
                       aws_access_key_id=ak,
                       aws_secret_access_key=sk)
    credentials = sts.get_session_token()
    credentials["Credentials"]["Expiration"] = ""

    print('request: {}'.format(json.dumps(event)))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': json.dumps(credentials)
    }
