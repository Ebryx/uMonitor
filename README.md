## Pre-Requisites
You'll need to create a virtual environment for python and install libraries using `pip`:
```
pip install -r requirements.txt
```

## Configuration
`config.json` file contains all settings you require for the program. It doesn't have to be `config.json` file, program detect the config file from **`CONFIG_FILE`** environment variable.


```
{
  "processes": 15,
  "endpoints": [
    "my-endpoint-1",
    "my-endpoint-2",
    "my-endpoint-3"
  ],
  "slack_bot_access_token": "xoxb-slack-token",
  "slack_workstation_access_token": "xoxp-slack-token",
  "webhooks": {
    "my-slack-bot-webhook-1": {
      "tags": ["user1", "@user2"]
    }
    "my-slack-bot-webhook-2": {
      "tags": []
    }
  },
  "options":  {
    "endpoints": {
      "my-endpoint-1": {
        "strings": [
          "string-1", "string-2"
        ]
      },
      "my-endpoint-2": {
        "strings": [
          "string-1", "string-2"
        ],
        "auth": {
          "user": <user>,
          "pass": <pass>
        }
      }
    }
  }
}
```
A sample config is given where **`processes`** specify the number of processes to open in parallel for execution. Say, your endpoints are **1500** in total. **15 processes** will divide the task into **100 endpoints** each and then display the end result. **`endpoints`** specify the list of endpoints to check the status of.

If **options** section of config, each endpoint can have `strings` list that program can match against. For example, for `my-endpoint-2`, program will check the returned response and if `string-1` and `string-2` exist in response, it is considered okay. If not, it will be considered down. If you have not specified any option for an endpoint, then program will check the response status code and decides if it's up or not.
>**`500+` status code means it's down, if there is no additional option for the endpoint.**

Similarly, each endpoint in **options** can have `auth` suboption specifying `user` and `pass` for authentication.

You can also specifiy slack webhooks in config and program will send a message in case it detects any down endpoint. To mention a **user** or **a custom team** in slack message, use `tags` option, a list, in webhooks. For example, to tag `user-321` on slack, you can specify it in `tags` list as `user-321` or `@user-321`. Similarly, you can add custom team in same `tags` list.
>**1- For user tags to work, you need to have a valid `slack_bot_access_token` in options.**
>
>**2- For team tags to work, you need to have a valid `slack_workspace_access_token` in options.**
>
> *When you intsall a slack app in your workspace, you can get these tokens from app settings page.*


### Unified Configuration
In case your endpoints are in a .csv file, you can add them to your config file and then use the unified config file for your program:

A sample of **endpoints.csv** can be:
```
Host/Endpoint,...
my-endpoint-1,...
my-endpoint-2,...
...
```
A csv file can be as complex as you like but first row, ` Host/Endpoint` in our case, will be ignored and first column needs to have endpoints you want the program to check.

You can add these csv endpoints to your config file:
```
python helper.py -config path/to/config.json --add endpoints.csv

# get details on what parameters to use.
python helper.py -h
```

## Encryption / Decryption
Use the ebryx encryption / decryption module.

https://github.com/EbryxLabs/ebryx#encryption--decryption

**Note:** Program expects the given config file to be encrypted. It will always try to decrypt the config file using `AES_KEY` in your environment variables.

## Execution
For execution, **`CONFIG_FILE`** and **`AES_KEY`** must be in your environment and **`CONFIG_FILE`** content must be encrypted using above **`AES_KEY`**. See encryption section, if you are not sure how to achieve it.

If you have your encrypted config ready, you can run the script by typing:
```
python script.py
```

### Lambda Execution
You need to upload a deployment package to either directly to **AWS Lambda** or to **S3** and then insert your bucket path to lambda. To create a deployment package:
```
# create archive with your libraries.
cd /your/python/env/lib/python3.x/site-packages/
zip -r9 myarchive.zip ./
mv myarchive.zip /path/to/project/
cd /path/to/project/

# add python scripts (necessary code files) of your project.
zip -g myarchive.zip *.py
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

### Configuration Changes
When you change your config file for local execution, you will have to encrypt your config file and put the path in **`CONFIG_FILE`** of your environment.

If you are using **AWS Lambda**, you can set **`CONFIG_FILE`** to a **S3** path that can be fetched; it can be public since the config file will be encrypted. Whenever you change the config file, encrypt it using encryption module of ebryx and  update the file on **S3**. **AWS Lambda** code will fetch the updated encrypted file, decrypt it and run the rest of program accordingly.