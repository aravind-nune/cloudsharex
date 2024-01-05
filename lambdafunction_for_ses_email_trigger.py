import json
import boto3


ses_client = boto3.client('ses', aws_access_key_id="AKIAVWZFT2VBPD6YQEJ4", aws_secret_access_key="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", region_name="us-east-1")


def lambda_handler(event, context):
    file_url = event['source_key']
    emails = event['destination_email']
    
    def send_email( file_url):
        subject = "File Sharing Link"
        body = f"Here is the link to download the shared file: {file_url}"
    
        try:
           res= ses_client.send_email(
                Source='aravindnune2303@gmail.com',
                Destination={'ToAddresses': emails},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body}}
                }
            )
           print(f"Email sent to {res}")
        except Exception as e:
            print(f"Failed to send email to : {str(e)}")
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda!')
        }
    send_email(file_url)
