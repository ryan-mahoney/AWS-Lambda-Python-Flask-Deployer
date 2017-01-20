import boto3, sys, os
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-s', '--stage', dest='stage')
parser.add_option('-b', '--bucket', dest='bucket')
parser.add_option('-t', '--type', dest='type')
parser.add_option('-f', '--file', dest='file')
parser.add_option('-n', '--name', dest='name')
parser.add_option('-v', '--version', dest='version', default='v1')
parser.add_option("-r", "--region", dest="region_name", default='us-east-1')
(options, args) = parser.parse_args()

# handle required fields
if not options.stage:
    parser.error('stage is required')

if not options.bucket:
    parser.error('bucket is required')

if not options.file:
    parser.error('file is required')

if not options.name:
    parser.error('name is required')

if not options.type:
    parser.error('type is required')

s3Client = boto3.resource('s3', region_name=options.region_name)

bucketRes = s3Client.create_bucket(Bucket=options.bucket)

print bucketRes

s3Obj = s3Client.Object(options.bucket, options.type + '/' + options.stage + '/' + options.version + '/' + options.name)

putRes = s3Obj.put(Body=open(options.file, 'rb'), ContentType='application/javascript')

print putRes

aclRes = s3Obj.Acl().put(ACL='public-read')

print aclRes