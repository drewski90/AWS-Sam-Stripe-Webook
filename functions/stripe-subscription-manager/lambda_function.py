from crhelper import CfnResource
import stripe
from os import environ
import logging

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger()

logger.setLevel(logging.INFO)

helper = CfnResource()

API_ENDPOINT = environ['API_ENDPOINT']
WEBHOOK_EVENTS = environ['WEBHOOK_EVENTS'].replace(' ', '').split(',')
stripe.api_key = environ['STRIPE_API_KEY']


def clear_existing_subscriptions():
  
  for endpoint in stripe.WebhookEndpoint.list()['data']:
    
    if endpoint['url'] == API_ENDPOINT:
      
      response = stripe.WebhookEndpoint.delete(endpoint['id'])
      logging.info('Deleting existing webhook subscription')
      logging.warning(response)

  
def register_subscription():
  
  response = stripe.WebhookEndpoint.create(
    enabled_events=WEBHOOK_EVENTS,
    url=API_ENDPOINT,
  )

  helper.Data['StripeSigningSecret'] = response['secret']
  
  logging.info('Created Webhook subscription')
  logging.info(response)


@helper.delete
def do_nothing(_, __):
  clear_existing_subscriptions()


@helper.create
@helper.update
def generate_keys(_, __):
  clear_existing_subscriptions()
  register_subscription()
  

def lambda_handler(event, context):
  return helper(event, context)