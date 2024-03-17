import json
import boto3
from botocore.exceptions import ClientError
from os import environ
import logging
from json import loads
import stripe

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger()

logger.setLevel(logging.INFO)

sns_client = boto3.client('sns')
ssm_client = boto3.client('ssm')
SNS_TOPIC = environ['SNS_TOPIC']
STRIPE_SIGNING_SECRET_PARAM = environ['STRIPE_SIGNING_SECRET_PARAM']
STRIPE_SECRET = None

stripe.api_key = environ['STRIPE_API_KEY']


def get_stripe_secret() -> str:
    """
    Retrieves stripe signing secret from param store and caches it globally 
    for the life of the lambda instance.
    """
    global STRIPE_SECRET
    if STRIPE_SECRET is None:
        try:
            response = ssm_client.get_parameter(
                Name=STRIPE_SIGNING_SECRET_PARAM,
                WithDecryption=True
            )
            parameter_value = response['Parameter']['Value']
            STRIPE_SECRET = parameter_value
            return parameter_value
        except ClientError as e:
            err_code = e.response['Error']['Code']
            logger.exception(f"Boto3 ssm request failed: {err_code}")
            raise e
        except Exception as e:
            logger.exception("Failed to retrieve stripe signing key")
            raise e
    else:
        return STRIPE_SECRET


def verify_stripe_event_signature(event:dict) -> dict:
    """Verifies the authenticity of the stripe message"""
    signature = event['headers']['stripe-signature']
    message_body = event['body']

    try:
        return stripe.Webhook.construct_event(
            message_body, signature, get_stripe_secret()
        )
    except ValueError as e:
        logging.exception("Invalid stripe payload")
        raise e
    except stripe.error.SignatureVerificationError as e:
        logging.exception("Invalid stripe signature")
        raise e


def create_sns_message_attributes(attributes_dict:dict):
    """Converts a dict to sns message attributes"""
    message_attributes = {}

    for key, value in attributes_dict.items():

        message_attributes[key] = {
            'DataType': "String",
            'StringValue': str(value)
        }

    return message_attributes


def lambda_handler(event, context):
    """Verify the incoming message is authentic from stripe and publishes the event to sns"""
    try:
        payload = verify_stripe_event_signature(event)
        message_attributes = {
            "id": {
                'DataType': "String",
                'StringValue': payload['data']['object']['id']
            },
            "event_type": {
                'DataType': "String",
                'StringValue': payload['type']
            },
            "livemode": {
                'DataType': "String",
                'StringValue': str(payload['livemode'])
            },
        }
        response = sns_client.publish(
            TopicArn=SNS_TOPIC,
            Message=event['body'],
            MessageAttributes=message_attributes
        )
        return {
            'statusCode': 200,
            'body': f"Message recieved {response['MessageId']}"
        }
    except ValueError:
        # Invalid payload
        logger.exception("Invalid payload")
        logger.info('event')
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid payload'})
        }
    except ClientError as e:
        # Extract HTTP status code and description from the exception
        status_code = e.response['ResponseMetadata']['HTTPStatusCode']
        error_description = e.response['Error']['Message']
        logger.exception('Failed to send event to snss')
        logger.info(event)
        return {
            "statusCode": status_code,
            'body': json.dumps({'error': error_description})
        }

