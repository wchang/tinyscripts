import os, json, os.path, argparse
import boto
import boto.s3.connection
access_key = '<access_key>'
secret_key = '<secret_key>'
gateway = 'griffin-objstore.opensciencedatacloud.org'

parser = argparse.ArgumentParser(description='Basic s3')

parser.add_argument('-b','--bucket', action="store", dest="bucket_name", help='setup becket name you are interested in')
parser.add_argument('-l','--list', action="store_true", help='list keys in bucket')
parser.add_argument('-d','--download', action="store", dest="download_key",  help='Download files from a bucket')
parser.add_argument('-u','--upload', action="store", dest="upload_key", help='Upload files')
args = parser.parse_args()

# create connection

conn = boto.connect_s3(
       aws_access_key_id = access_key,
       aws_secret_access_key = secret_key,
       host = gateway,
       calling_format = boto.s3.connection.OrdinaryCallingFormat(),
       )

for bucket in conn.get_all_buckets():
        print "{name}\t{created}".format(
                name = bucket.name,
                created = bucket.creation_date,
        )

if args.bucket_name:
    bucket = conn.get_bucket(args.bucket_name)
    if args.list:
       for keys in bucket.list():
           print keys.name

    if args.download_key:
       print "Downloading %s ......"%(args.download_key)
       key = bucket.get_key(args.download_key)
       key.get_contents_to_filename(args.download_key)

    if args.upload_key:
       print "Uploading %s ......"%(args.upload_key)
       key = bucket.new_key(args.upload_key)
       key.set_contents_from_filename(args.upload_key)

