## Pre-Requisites
You'll need to create a virtual environment for python and install libraries using `pip`:
```
pip install -r requirements.txt
```

## Configuration
`config.json` file contains all non-critical information, generally. For critical info, insert it into different file, some are required in .csv while other in .json format, and encrypt those files. Finally, mention path of encrypted files in higher level `config.json` file.


```
{
  "processes": 15,
  "endpoints_file": "_endpoints.csv",
  "options": "_options.json"
}
```
A sample config is given where **`processes`** specify the number of processes to open in parallel for execution. Say, your endpoints are **1500** in total. **15 processes** will divide the task into **100 endpoints** each and then display the end result.
&nbsp;**`_endpoints.csv`** file is an encrypted csv containing endpoints. Similarly, &nbsp;**`_options.json`** is an encrypted .json file containing options with critical data that you don't want exposed, if codebase goes public.

A sample of **unencrypted endpoints.csv** can be:
```
Host/Endpoint,
my-endpoint-1,
my-endpoint-2,
```
A csv file can be as complex as you like but first row, ` Host/Endpoint` in our case, will be ignored and first column needs to have endpoints you want the program to check.


A sample of **unencrypted options.json** can be:
```
{
  "endpoints": {
    "my-endpoint-1": {
      "strings": [
        "string-1", "string-2"
      ]
    },
    "my-endpoint-2": {
      "strings": [
        "string-1", "string-2"
      ]
    }
  },
  "webhooks": [
    "my-slack-bot-webhook-1",
    "my-slack-bot-webhook-2"
  ]
}
```
If options file is specified in higher level config, each endpoint can have `strings` list that program can match against. For example, for `my-endpoint-2`, program will check the returned response and if `string-1` and `string-2` exist in response, it is considered okay. If not, it will be considered down. In other cases like **connection timeout or 500** errors, it will be considered down again.

You can also specifiy slack webhooks in options file and program will send you a message in case it detects any down endpoint.

## Encryption / Decryption
You can encrypt / decrypt data using `crypto.py` script. **(AES-256 Encryption)**

For example, to encrypt you can do following:
```
python crypto.py <my-file.json> -E --new
# encrypts myfile.json using newly created crypto-secure keys. Keys will be written to _keys file.

python crypto.py <my-file.json> -E
# encrypts using keys in AES_KEY, AES_IV environment variables.

# If your input file is myfile.json, encrypted file will be _myfile.json
```

For decryption, you'll need to have `AES_KEY` and `AES_IV` keys in your environment variables.
```
python crypto.py <my-file.json> -D
# decrypts my-file.json and write the unencrypted data to _decrypted_my-file.json
```
## Execution
If you have your configs ready, you can run the script by typing:
```
python script.py
```
> Make sure that you have a **`config.json`** file as a high level config. Inside that, you can specify path to ***encrypted*** endpoints and options file.

### Lambda Execution
You need to upload a deployment package to either directly to **AWS Lambda** or to **S3** and then insert your bucket path to lambda. To create a deployment package:
```
# create archive with your libraries.
cd /your/python/env/lib/python3.x/site-packages/
zip -r9 myarchive.zip ./
mv myarchive.zip /path/to/project/
cd /path/to/project/

# add python scripts and config files.
zip -g myarchive.zip *.py
zip -g myarchive.zip config.json
zip -g myarcvice.zip encrypted_endpoints.csv
zip -g myarcvice.zip encrypted_options.json
```
*Usually, you don't need to create your archive everytime you make a change. You can re-add your changed files by using zip utility command as follows:*
```
zip -g myarchive.zip changed_file # adds/updates file to archive.
zip -d myarchive.zip file_in_archive # removes file from archive.
```
*You can even check the archive structure, using unzip command as follows:*
```
unzip -l myarchive.zip
```