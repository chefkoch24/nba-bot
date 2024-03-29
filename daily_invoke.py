import boto3

# Create a Lambda client
lambda_client = boto3.client('lambda', region_name='eu-central-1')

# Invoke the Lambda function asynchronously
response = lambda_client.invoke(
    FunctionName='lastnightscores-NBAScrapeFunction-9PvFprdAbkeA',
    InvocationType='Event',  # Asynchronous invocation
    Payload='{}'  # Optional payload/data to pass to the function
)
