"""
S3 file uploader helper
"""
import boto3
from botocore.exceptions import ClientError
import logging
import os
from config.constant_config import Config


class S3Uploader:
    """S3 file uploader with presigned URL generation"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION,

        )

        self.bucket_name = Config.S3_BUCKET_NAME
    
    def upload_file_and_get_url(self, file_path, object_name=None, expiration=3600):
        """Upload file to S3 and return presigned URL"""
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            print(f"File uploaded to S3: {object_name}")
            
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_name,

                },
                ExpiresIn=expiration
            )
            
            return presigned_url
            
        except ClientError as e:
            logging.error(f"S3 upload error: {e}")
            print(f"S3 upload error: {e}")
            return None
        


