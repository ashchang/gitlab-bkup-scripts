import gitlab
import time
import requests
import json
import os
import string
import boto3
from datetime import datetime

### Time
now = datetime.now()
date = datetime.strftime(now, '%Y-%m-%d_%H-%M')


### Variables
group_num = "xxxxxxxx"
dir_name = "gitlab-bkup"
file_name = f"{dir_name}.tar.gz"
file_path = os.popen("pwd").read().split('\n')[0]
directory = os.path.dirname(file_path+"/"+dir_name+"/")
bucket_name = "s3://gitlab/"


### private token or personal token authentication
client = boto3.client('ssm')
git_user = client.get_parameter(Name='gitlab_user', WithDecryption=True)['Parameter']['Value']
git_token = client.get_parameter(Name='gitlab_token', WithDecryption=True)['Parameter']['Value']

gl = gitlab.Gitlab('https://gitlab.com/', private_token=git_token, api_version=4)
my_header={'PRIVATE-TOKEN': git_token}


### Gitlab Project Probe
def group_recursive(id, depth):
    '''Find Projects in recursive '''
    depth=depth+1
    group = gl.groups.get(id)
    subgroup = group.subgroups.list()
    for i in subgroup:
        print("depth: {} {:>8} {} {}".format(depth,i.id,i.name,i.full_path))
        os.system(f"mkdir -p {file_path}/{i.full_path}")
        os.chdir(file_path+"/"+i.full_path)
        now=os.getcwd()
        print(now)
        
        urls=f"https://gitlab.com/api/v4/groups/{i.id}/projects"
        r2 = requests.get(urls, headers=my_header)
        d2 = json.loads(r2.text)
        for j in d2:
            print("project: {:>8} {:>30}\t{}".format(j['id'],j['name'],j['http_url_to_repo']))
            v_url=j['http_url_to_repo'].split('https://')[1]
            os.system(f"git clone -s https://{git_user}:{git_token}@{v_url}") 
        group_recursive(i.id, depth)


### MAIN
try:
    os.stat(directory)
except:
    os.mkdir(directory)

retval = os.getcwd()
print(retval)
os.chdir( directory )

retval = os.getcwd()
print(retval)

gl.auth()
group_recursive(group_number,0)
os.chdir( file_path )
os.system(f"tar -zcvf {file_name} ./{dir_name}/")
os.system(f"aws s3 cp {file_path}/{file_name} {bucket_name}{date}/")
os.system(f"rm -rf {file_path}/{dir_name}/ {file_path}/{file_name}")

