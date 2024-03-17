# Stripe Events to SQS Topic

This SAM template sets up a complete serverless application to handle webhook events from Stripe, registers the webhook with stripe, and process events as needed. It provides a scalable and flexible architecture to integrate with Stripe and handle events efficiently. Webhook events from Stripe are published to an SNS (Simple Notification Service) topic.

# Parameters

    StripeApiKey: The Stripe API key.
    WebhookEvents: A comma-delimited string array of the events that the webhook should recieve.

# Resources

    StripeLayer: A Lambda layer containing dependencies needed for Stripe integration.
    StripeSNSTopic: An SNS topic where webhook events will be published.
    WebhookApi: An HTTP API endpoint to receive webhook events from Stripe.
    WebhookToSNS: A Lambda function to process webhook events and publish them to the SNS topic.
    WebhookSubscriptionManager: A Lambda function to automatically register the webhook api to stripe
    WebhookSubscriber: A custom resource to trigger the subscription manager Lambda function.
    StripeSigningSecret: An SSM parameter to store the Stripe signing key used to verify webhook messages.
    StripeAuthorizer: A Lambda function to authorize requests to the HTTP API endpoint.

# Outputs

    StripeWebhookUrl: The URL of the HTTP API endpoint to receive messages from Stripe.
    StripeEventsTopic: The ARN of the SNS topic where webhook events are published.

# Subscribe to Stripe events
```
  ConsumerTest:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: ./functions/consumer-test
      Runtime: python3.10
      Handler: lambda_function.lambda_handler
      Policies:
        - AWSLambdaBasicExecutionRole
      Events:
        MySNSLambdaEvent:
          Type: SNS
          Properties:
            Topic: !ImportValue StripeEventsTopic # import sns topic from webhook stack

  ConsumerTestSubscription:
    Type: 'AWS::SNS::Subscription'
    Properties:
      Protocol: lambda
      Endpoint: !GetAtt ConsumerTest.Arn
      TopicArn: !ImportValue StripeEventsTopic
      FilterPolicy:
        type:
          - customer.updated # event type to subscribe to
```