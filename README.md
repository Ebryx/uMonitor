## Pre-Requisites
You'll need to create a virtual environment for python and install libraries using `pip`:
```
pip install -r requirements.txt
```

## Configuration
`config.json` file contains all settings you require for the program. It doesn't have to be `config.json` file, program detect the config file from **`CONFIG_FILE`** environment variable. A complete template with supported fields is shown below for reference.


```
{
  "processes": 15,
  "endpoints": [
    "my-endpoint-1",
    "my-endpoint-2",
    "my-endpoint-3"
  ],
  "suppression_mins": 30,
  "storage_path": "https://s3-eu-west-1.amazonaws.com/your-bucket-name/your-storage-file-path",
  "custom_user_agent": "your-header-user-agent",
  "slack_prefix_message": "Sample prefix text",
  "slack_bot_access_token": "xoxb-slack-token",
  "slack_workstation_access_token": "xoxp-slack-token",
  "webhooks": {
    "my-slack-bot-webhook-1": {
      "tags": ["@user1", "@team1"]
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

#### Multithreaded Requests
```
"processes": 15,
"endpoints": [
  "my-endpoint-1",
  "my-endpoint-2",
  "my-endpoint-3"
],
```
**`processes`** specify the number of processes to open in parallel for execution. Say, your endpoints are **1500** in total. **15 processes** will divide the task into **100 endpoints** each and then display the end result. **`endpoints`** specify the list of endpoints to check the status for. Number of **`processes`** are limited back to number of **`endpoints`** if greater i.e. each process takes care of one endpoint.
>Optimal value for execution on lambda is 12-18 processes.

#### Endpoint Details
```
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
```
In **`options`** section of config, each endpoint can have `strings` list that program can match against. For example, for `my-endpoint-2`, program will check the returned response and if `string-1` and `string-2` exist in response, it is considered okay. If not, it will be considered down. If you have not specified any option for an endpoint, then program will check the response status code and decides if it's up or not.
>**`500+` status code means it's down, if there is no additional option for the endpoint.**

Moreover, ach endpoint in **`options`** can have **`auth`** suboption specifying **`user`** and **`pass`** for authentication.

#### Slack Configuration
```
"slack_prefix_message": "Sample prefix text",
"slack_bot_access_token": "xoxb-slack-token",
"slack_workstation_access_token": "xoxp-slack-token",
"webhooks": {
  "my-slack-bot-webhook-1": {
    "tags": ["@user1", "@team1"]
  }
  "my-slack-bot-webhook-2": {
    "tags": []
  }
},
```
You can also specifiy slack webhooks in config and program will send a message in case it detects any down endpoint. To prefix a message in a slack alert, use **`slack_prefix_message`** field. To mention a **user** or **a custom team** in slack message, use **`tags`** option, a list, in webhooks. For example, to tag `user-321` on slack, you can specify it in **`tags`** list as `@user-321`. Similarly, you can add custom team in same **`tags`** list.
>For user tags to work, you need to have a valid **`slack_bot_access_token`** in options.

>For team tags to work, you need to have a valid **`slack_workspace_access_token`** in options.

> When you intsall a slack app in your workspace, you can get these tokens from app settings page.

#### Alerts Suppression
```
"suppression_mins": 30,
"storage_path": "https://s3-eu-west-1.amazonaws.com/your-bucket-name/your-storage-file-path",
```
**`suppression_mins`** field can suppress slack alerts for given number of minutes if endpoint is down for same reason as previous alert. To make it work on lambda, you have to provide **`storage_path`** that refers to a path in same **S3** bucket that you mention using **CloudFormation** to create a stack for this project.
>The reason behind is that the role associate with lambda has to have access to S3 bucket to upload storage file. Since associated role is generated automatically via CloudFormation, it writes permission policy with respect to the bucket that you provide the deployment package from.

#### User-Agent Header
You can also had your custom `User-Agent` header in requests made to endpoints by using **`cutom_user_agent`** field.
```
"custom_user_agent": "your-header-user-agent"
```

### Unified Configuration
In case your endpoints are in a .csv file, you can add them to your config file and then use the unified config file for your program:

A sample of **endpoints.csv** can be:
```
Host/Endpoint,...
my-endpoint-1,...
my-endpoint-2,...
...
```
A csv file can be as complex as you like but first row, **`Host/Endpoint`** in our case, will be ignored and first column needs to have endpoints you want the program to check.

You can add these csv endpoints to your config file:
```
python helper.py -config path/to/config.json --add endpoints.csv

# get details on what parameters to use.
python helper.py -h
```

## Encryption / Decryption
Confguration file in `.json` format is given in encrypted form and program decrypts it using AES keys provided in environment. For more information on encryption / decryption, look at [**opencrypt**](https://pypi.org/project/opencrypt/) library of python.


## Execution
For execution, **`CONFIG_FILE`**, **`AES_KEY`** and **`AES_IV`** must be in your environment and **`CONFIG_FILE`** content must be encrypted using the encryption keys. See encryption section, if you are not sure how to achieve it.

If you have your encrypted config ready, you can run the script by typing:
```
python script.py
```

## AWS Lambda Deployment
- Create a deployment package, place it to S3 so you can specify it in your cloudformation process. You need make an archive containing all the required libraries as mentioned in `requirements.txt` file and python scripts containing the code.
    ```
    cd /path/to/env/lib/pythonx.x/site-packages/
    zip -r9 <archive-name> ./
    ```
    From root directory of the project, add python scripts to the same archive you created above:
    ```
    zip -g <archive-name> *.py
    ```
- Or just execute following command to create lambda deployment package named `lambda_code-YYYY-mm-ddTHH-MM-SSZ.zip` command
  ```
  /bin/bash lambda_package_creator.sh /path/to/env/lib/pythonx.x/site-packages/
  ```

Usually, you don't need to create your archive everytime you make a change. You can re-add your changed files by using zip utility command as follows:
```
zip -g myarchive.zip changed_file # adds/updates file to archive.
zip -d myarchive.zip file_in_archive # removes file from archive.
```
You can even check the archive structure, using unzip command as follows:
```
unzip -l myarchive.zip
```

## Configuration Changes
When you change your config file for local execution, you will have to encrypt your config file and put the path in **`CONFIG_FILE`** of your environment.

If you are using **AWS Lambda**, you can set **`CONFIG_FILE`** to a **S3** path that can be fetched; it can be public since the config file will be encrypted. Whenever you change the config file, encrypt it using encryption module of ebryx and  update the file on **S3**. **AWS Lambda** code will fetch the updated encrypted file, decrypt it and run the rest of program accordingly.