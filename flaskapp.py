import boto3
from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)

# configuration of aws 
AWS_ACCESS_KEY_ID = "AKIAVWZFT2VBPD6YQEJ4"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "fileuploadtos3cloudtool"
DYNAMODB_TABLE_NAME = "cloud_file_sharing_tool_to_save_filename"
SES_SOURCE_EMAIL = "aravindnune2303@gmail.com"
LAMBDA_FUNCTION_NAME = "lambda_email_service"


# Initialize Boto3 clients for S3, DynamoDB, and SES
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
dynamodb_resource = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
ses_client = boto3.client('ses', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
lambda_client = boto3.client('lambda', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)

# DynamoDB Table
table = dynamodb_resource.Table(DYNAMODB_TABLE_NAME)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods  = ['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    is_login = check_login_details(email, password)
    
    if is_login:
        return render_template("index.html")
    return render_template("login.html")

def check_login_details(email, password):
    dynamodb_login = boto3.resource('dynamodb', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION)
    login_details = "login" #db table name
    login_details_data = dynamodb_login.Table(login_details)
    response = login_details_data.query(
        KeyConditionExpression = boto3.dynamodb.conditions.Key("email").eq(email)

    )
    login_db_items = response["Items"]

    if not login_db_items:
        return False
    
    return True



@app.route('/upload', methods=['POST'])
def upload_file():
    # Get the uploaded file and email addresses from the form data
    file = request.files['file']
    emails = request.form.get('emails').split(',')
    print("request:", request)
    print("filename", file.filename)

    if not file:
        return jsonify({"message": "Please select a file to upload."}), 400

    if not emails or len(emails) > 5 or not all(email.strip() for email in emails):
        return jsonify({"message": "Please enter up to 5 valid email addresses (comma-separated)."}), 400

    try:
        # Upload the file directly to S3
        s3_client.upload_fileobj(file, S3_BUCKET_NAME, file.filename)

        # Generate the link to the uploaded file on S3
        file_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file.filename},
            ExpiresIn=3000 
        )
        lambda_email_service(file_url,emails)

        # Send email to provided addresses
        """for email in emails:
            send_email(email, file_url)"""

        # Store file information in DynamoDB
        store_file_info(file.filename)

       

        return jsonify({"message": "File uploaded, emails sent successfully!"}), 200

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

"""def send_email(recipient_email, file_url):
    # Your code to send email using AWS SES
    subject = "File Sharing Link"
    body = f"Here is the link to download the shared file: {file_url}"

    try:
       res= ses_client.send_email(
            Source='aravindnune2303@gmail.com',
            Destination={'ToAddresses': ['aravindnune2303@gmail.com']},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
       print(f"Email sent to {res}")
    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {str(e)}")"""

def store_file_info(filename):
    table.put_item(
        Item={
            'file_name': filename,
            'email':'aravindnune2303@gmail.com'
        }
    )
    print(f"File information stored in DynamoDB: {filename} ")

def lambda_email_service(file_url,emails):
    print("triggered lambda")
    Payload = {
        'source_email':'aravindnune2303@gmail.com',
        'source_key': file_url,
        'destination_email':emails
    }

    try:
        lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType='Event',
            Payload=bytes(json.dumps(Payload), encoding='utf-8')

        #     Payload = {
        # 'source_email':'aravindnune2303@gmail.com',
        # 'source_key': file_url,
        # 'destination_email':'aravindnune2303@gmail.com'}
        )
        print("Lambda function invoked for S3 object copy.")
    except Exception as e:
        print(f"Failed to invoke Lambda function: {str(e)}")




if __name__ == '__main__':
    app.run('0.0.0.0', port = 5000)
