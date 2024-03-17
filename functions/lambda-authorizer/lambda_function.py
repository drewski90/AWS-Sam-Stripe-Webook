import logging

logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger()

logger.setLevel(logging.INFO)

def lambda_handler(event, context):
  
    headers = event['headers']
    allow = headers['content-type'] == 'application/json; charset=utf-8' and \
       headers['user-agent'] == 'Stripe/1.0 (+https://stripe.com/docs/webhooks)' and \
       'stripe-signature' in headers
    response = {"isAuthorized": allow}
    logging.info(response)
    return response