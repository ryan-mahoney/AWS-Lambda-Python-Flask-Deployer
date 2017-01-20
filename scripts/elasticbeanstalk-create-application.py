import boto3, sys

# let's use Elastic Beanstalk
client = boto3.client('elasticbeanstalk')

# get application name
if len(sys.argv) > 1:
    applicationName = sys.argv[2]
else:
    raise Exception('application name not provided')

# get application description