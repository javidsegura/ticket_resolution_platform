from typing import Dict
import boto3
import os
import json
import logging

logger = logging.getLogger(__name__)

s3_client = None
secrets_manager_client = None


def initialize_aws_s3_client():
	global s3_client
	logger.debug("Initializing s3 client")
	if not s3_client:
		logger.debug("Instantiat s3 client for the first time")
		s3_client = boto3.client("s3", region_name=os.getenv("AWS_MAIN_REGION"))
	return s3_client


def initialize_aws_secrets_manager_client():
	global secrets_manager_client
	logger.debug("Initializing secrets manager client")
	if not secrets_manager_client:
		logger.debug("Instantiat secrets manager client for the first time")
		secrets_manager_client = boto3.client(
			"secretsmanager", region_name=os.getenv("AWS_MAIN_REGION")
		)
	return secrets_manager_client
