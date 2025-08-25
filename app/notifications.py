from dataclasses import dataclass
from typing import Optional
from config import settings

import boto3
from botocore.exceptions import ClientError


@dataclass
class Message:
    subject: str
    body: str
    recipient: str

class Notifier:
    """Contrato para proveedores de notificación."""
    def send(self, message: Message, email: Optional[str], phone: Optional[str]) -> bool:
        raise NotImplementedError
    
class EmailNotifier(Notifier):
    """Implementación de Notifier para enviar correos electrónicos usando AWS SES."""
    def __init__ (self):
        super().__init__()
        self.client = boto3.client('ses', region_name=settings.region)
    
    def send(self, message: Message, email: str) -> bool:

        sender_email = settings.ses_sender
        subject = message.subject
        body = message.body
        body_html = f"""
            <html>
            <head></head>
            <body>
            <h1>Hello!</h1>
            <p>{body}</p>
            </body>
            </html>
        """
        try:
            response = self.client.send_email(
                Source=sender_email,
                Destination={
                    'ToAddresses': [
                        email,
                    ],
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': body_html,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
        print(f"Email sent! Message ID: {response['MessageId']}")
        return True


class SMSNotifier(Notifier):
    def __init__ (self):
        super().__init__()
        self.client = boto3.client('sns', region_name=settings.region)
    """Implementación de Notifier para enviar SMS usando AWS SNS."""""
    def send(self, message: Message, phone: str) -> bool:
        print("Sending SMS to", phone)
        print("Message:", message.body)
        try:
            response = self.client.publish(
                PhoneNumber=phone, Message=message.body
            )
            message_id = response["MessageId"]
        except ClientError:
            print("Error sending SMS")
            raise
        else:
            return message_id