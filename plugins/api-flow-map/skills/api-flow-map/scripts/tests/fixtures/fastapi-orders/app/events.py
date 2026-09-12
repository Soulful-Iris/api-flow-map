import json
import boto3

sns = boto3.client("sns")
TOPIC_ARN = "arn:aws:sns:us-east-1:123:order-events"


async def publish(topic, event):
    sns.publish(TopicArn=TOPIC_ARN, Message=json.dumps(event), Subject=topic)
