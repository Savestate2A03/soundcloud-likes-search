# SoundCloud Likes Search

Search and filter SoundCloud likes without an official API key.

Live: https://savestate2a03.github.io/soundcloud-likes-search/

## How It Works

SoundCloud already has a public API but does not have CORS enabled for it, so this project scrapes `client_id` from the provided JavaScript files on the homepage, then uses it to proxy API requests through AWS Lambda. The `client_id` is cached in DynamoDB and refreshed every 2 minutes.

The static frontend is hosted on GitHub Pages and communicates with the Lambda proxy.

The limit currently for likes is 50,000. This is an arbitrary amount set by me. If 50,000 is somehow not enough for you, raise a GitHub issue with a use case to justify it.

Additionally, if not using filters and the total number of likes is less than 50,000 while also reporting having fewer than your total likes, those will be songs that have been deleted/privated.

## Why not request a developer app and use OAuth 2.0?

I did, they haven't gotten back to me yet (I had to talk to an AI chatbot) so things are done this way in the meantime.

## Files

```
|  index.html .......... frontend
|  handler.py .......... lambda function
|  template.yaml ....... aws sam template
|  .github
|  |-- workflows
|  |-- |-- deploy.yml .. github pages deployment
```

## AWS Deployment

### AWS CLI and SAM CLI
Requirements:
- AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- AWS SAM CLI: https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

You can find `.msi` installers (as well as installers for other systems) linked on each.N

If you haven't set up AWS CLI yet, grab your credentials from AWS Management Console:

AWS CLI:
```sh
aws login
```

### Build and deploy

AWS SAM CLI commands:

```sh
sam build && sam deploy --guided
```

The guided deploy will prompt for stack name and parameters. When asked:
> SoundcloudProxyFunction has no authentication. Is this okay? [y\/N]:

Make sure to answer with `y`. Defaults are generally going to be fine for other prompts.

Note what `ApiUrl` is after deploying as you will need to provide it to the frontend / GitHub.

This is also how you re-deploy the environment on top of the existing one.

#### Example deployment output

<details>
<summary>Click to view output</summary>
 
```sh
C:\Users\Savestate\dev\soundcloud-likes-search>sam build && sam deploy --guided
Building codeuri: C:\Users\Savestate\dev\soundcloud-likes-search runtime: python3.12 architecture: x86_64 functions: SoundcloudProxyFunction
requirements.txt file not found. Continuing the build without dependencies.
 Running PythonPipBuilder:CopySource

Build Succeeded

Built Artifacts  : .aws-sam\build
Built Template   : .aws-sam\build\template.yaml

Commands you can use next
=========================
[*] Validate SAM template: sam validate
[*] Invoke Function: sam local invoke
[*] Test Function in the Cloud: sam sync --stack-name {{stack-name}} --watch
[*] Deploy: sam deploy --guided

Configuring SAM deploy
======================

        Looking for config file [samconfig.toml] :  Found
        Reading default arguments  :  Success

        Setting default arguments for 'sam deploy'
        =========================================
        Stack Name [soundcloud-proxy]:
        AWS Region [us-east-1]:
        Parameter TableName [soundcloud-proxy]:
        Parameter RateLimitSeconds [1]:
        Parameter ClientIdTtlSeconds [120]:
        #Shows you resources changes to be deployed and require a 'Y' to initiate deploy
        Confirm changes before deploy [Y/n]:
        #SAM needs permission to be able to create roles to connect to the resources in your template
        Allow SAM CLI IAM role creation [Y/n]:
        #Preserves the state of previously provisioned resources when an operation fails
        Disable rollback [y/N]:
        SoundcloudProxyFunction has no authentication. Is this okay? [y/N]: y #   <--- MAKE SURE TO SELECT 'y'
        SoundcloudProxyFunction has no authentication. Is this okay? [y/N]: y #   <--- MAKE SURE TO SELECT 'y'
        SoundcloudProxyFunction has no authentication. Is this okay? [y/N]: y #   <--- MAKE SURE TO SELECT 'y'
        SoundcloudProxyFunction has no authentication. Is this okay? [y/N]: y #   <--- MAKE SURE TO SELECT 'y'
        SoundcloudProxyFunction has no authentication. Is this okay? [y/N]: y #   <--- MAKE SURE TO SELECT 'y'
        SoundcloudProxyFunction has no authentication. Is this okay? [y/N]: y #   <--- MAKE SURE TO SELECT 'y'
        Save arguments to configuration file [Y/n]:
        SAM configuration file [samconfig.toml]:
        SAM configuration environment [default]:

        Looking for resources needed for deployment:

        Managed S3 bucket: aws-sam-cli-managed-default-samclisourcebucket-abcdefghijkl
        Auto resolution of buckets can be turned off by setting resolve_s3=False
        To use a specific S3 bucket, set --s3-bucket=<bucket_name>
        Above settings can be stored in samconfig.toml

        Saved arguments to config file
        Running 'sam deploy' for future deployments will use the parameters saved above.
        The above parameters can be changed by modifying samconfig.toml
        Learn more about samconfig.toml syntax at
        https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-config.html


        File with same data already exists at soundcloud-proxy/12345678123456781234567812345678, skipping upload

        Deploying with following values
        ===============================
        Stack name                   : soundcloud-proxy
        Region                       : us-east-1
        Confirm changeset            : True
        Disable rollback             : False
        Deployment s3 bucket         : aws-sam-cli-managed-default-samclisourcebucket-abcdefghijkl
        Capabilities                 : ["CAPABILITY_IAM"]
        Parameter overrides          : {"TableName": "soundcloud-proxy", "RateLimitSeconds": "1", "ClientIdTtlSeconds": "120"}
        Signing Profiles             : {}

Initiating deployment
=====================


        File with same data already exists at soundcloud-proxy/cad60aada974010a8cab905944de378a.template, skipping upload


Waiting for changeset to be created..

CloudFormation stack changeset
-------------------------------------------------------------------------------------------------------------------------------------
Operation            LogicalResourceId                                        ResourceType                      Replacement
-------------------------------------------------------------------------------------------------------------------------------------
+ Add                SoundcloudProxyApiDeployment1234fa1234                   AWS::ApiGateway::Deployment       N/A
+ Add                SoundcloudProxyApiprodStage                              AWS::ApiGateway::Stage            N/A
+ Add                SoundcloudProxyApi                                       AWS::ApiGateway::RestApi          N/A
+ Add                SoundcloudProxyFunctionApiHealthPermissionprod           AWS::Lambda::Permission           N/A
+ Add                SoundcloudProxyFunctionApiLikesPermissionprod            AWS::Lambda::Permission           N/A
+ Add                SoundcloudProxyFunctionApiOptionsHealthPermissionprod    AWS::Lambda::Permission           N/A
+ Add                SoundcloudProxyFunctionApiOptionsLikesPermissionprod     AWS::Lambda::Permission           N/A
+ Add                SoundcloudProxyFunctionApiOptionsUsernamePermissionprod  AWS::Lambda::Permission           N/A
+ Add                SoundcloudProxyFunctionApiUsernamePermissionprod         AWS::Lambda::Permission           N/A
+ Add                SoundcloudProxyFunctionRole                              AWS::IAM::Role                    N/A
+ Add                SoundcloudProxyFunction                                  AWS::Lambda::Function             N/A
+ Add                SoundcloudProxyTable                                     AWS::DynamoDB::Table              N/A
-------------------------------------------------------------------------------------------------------------------------------------
Changeset created successfully.
arn:aws:cloudformation:us-east-1:1234123412341:changeSet/samcli-deploy12341234123/12341234-4444-3333-2222-abcdef987654

2026-01-07 01:28:23 - Waiting for stack create/update to complete

CloudFormation events from stack operations (refresh every 5.0 seconds)
-------------------------------------------------------------------------------------------------------------------------------------
ResourceStatus      ResourceType                 LogicalResourceId                                        ResourceStatusReason
-------------------------------------------------------------------------------------------------------------------------------------
CREATE_IN_PROGRESS  AWS::CloudFormation::Stack   soundcloud-proxy                                         User Initiated
CREATE_IN_PROGRESS  AWS::DynamoDB::Table         SoundcloudProxyTable                                     -
CREATE_IN_PROGRESS  AWS::DynamoDB::Table         SoundcloudProxyTable                                     Resource creation Initiated
CREATE_COMPLETE     AWS::DynamoDB::Table         SoundcloudProxyTable                                     -
CREATE_IN_PROGRESS  AWS::IAM::Role               SoundcloudProxyFunctionRole                              -
CREATE_IN_PROGRESS  AWS::IAM::Role               SoundcloudProxyFunctionRole                              Resource creation Initiated
CREATE_COMPLETE     AWS::IAM::Role               SoundcloudProxyFunctionRole                              -
CREATE_IN_PROGRESS  AWS::Lambda::Function        SoundcloudProxyFunction                                  -
CREATE_IN_PROGRESS  AWS::Lambda::Function        SoundcloudProxyFunction                                  Resource creation Initiated
CREATE_COMPLETE     AWS::Lambda::Function        SoundcloudProxyFunction                                  -
CREATE_IN_PROGRESS  AWS::ApiGateway::RestApi     SoundcloudProxyApi                                       -
CREATE_IN_PROGRESS  AWS::ApiGateway::RestApi     SoundcloudProxyApi                                       Resource creation Initiated
CREATE_COMPLETE     AWS::ApiGateway::RestApi     SoundcloudProxyApi                                       -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiLikesPermissionprod            -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsLikesPermissionprod     -
CREATE_IN_PROGRESS  AWS::ApiGateway::Deployment  SoundcloudProxyApiDeployment1234fa1234                   -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsHealthPermissionprod    -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiUsernamePermissionprod         -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiHealthPermissionprod           -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsUsernamePermissionprod  -
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiLikesPermissionprod            Resource creation Initiated
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsHealthPermissionprod    Resource creation Initiated
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiHealthPermissionprod           Resource creation Initiated
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsUsernamePermissionprod  Resource creation Initiated
CREATE_IN_PROGRESS  AWS::ApiGateway::Deployment  SoundcloudProxyApiDeployment1234fa1234                   Resource creation Initiated
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiUsernamePermissionprod         Resource creation Initiated
CREATE_IN_PROGRESS  AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsLikesPermissionprod     Resource creation Initiated
CREATE_COMPLETE     AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsHealthPermissionprod    -
CREATE_COMPLETE     AWS::Lambda::Permission      SoundcloudProxyFunctionApiLikesPermissionprod            -
CREATE_COMPLETE     AWS::Lambda::Permission      SoundcloudProxyFunctionApiHealthPermissionprod           -
CREATE_COMPLETE     AWS::Lambda::Permission      SoundcloudProxyFunctionApiUsernamePermissionprod         -
CREATE_COMPLETE     AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsUsernamePermissionprod  -
CREATE_COMPLETE     AWS::ApiGateway::Deployment  SoundcloudProxyApiDeployment1234fa1234                   -
CREATE_COMPLETE     AWS::Lambda::Permission      SoundcloudProxyFunctionApiOptionsLikesPermissionprod     -
CREATE_IN_PROGRESS  AWS::ApiGateway::Stage       SoundcloudProxyApiprodStage                              -
CREATE_IN_PROGRESS  AWS::ApiGateway::Stage       SoundcloudProxyApiprodStage                              Resource creation Initiated
CREATE_COMPLETE     AWS::ApiGateway::Stage       SoundcloudProxyApiprodStage                              -
CREATE_COMPLETE     AWS::CloudFormation::Stack   soundcloud-proxy                                         -

CloudFormation outputs from deployed stack
-------------------------------------------------------------------------------------------------------------------------------------
Outputs
-------------------------------------------------------------------------------------------------------------------------------------
Key                 FunctionArn
Description         Lambda function ARN
Value               arn:aws:lambda:us-east-1:123412341234:function:soundcloud-proxy

Key                 ApiUrl 
Description         API Gateway endpoint URL
Value               https://zxc1234zxc1.execute-api.us-east-1.amazonaws.com/prod # <--- This is the endpoint GitHub will need

Key                 TableArn
Description         DynamoDB table ARN
Value               arn:aws:dynamodb:us-east-1:56785678567856:table/soundcloud-proxy
-------------------------------------------------------------------------------------------------------------------------------------


Successfully created/updated stack - soundcloud-proxy in us-east-1
```

</details>

### Debugging Logs

You can debug logs with AWS SAM:

```sh
sam logs --stack-name soundcloud-proxy --tail
```

#### Example log output

```log
C:\Users\Savestate\dev\soundcloud-likes-search>sam logs --stack-name soundcloud-proxy --tail
INIT_START Runtime Version: python:3.12.v101 Runtime Version ARN: arn:aws:lambda:us-east-1::runtime:994aac32248ecf4d69d9f5e9a3a57aba3ccea19d94170a61d5ecf978927e1b0f
[WARNING] LAMBDA_WARNING: Unhandled exception. The most likely cause is an issue in the function code. However, in rare cases, a Lambda
                          runtime update can cause unexpected function behavior. For functions using managed runtimes, runtime updates
                          can be triggered by a function change, or can be applied automatically. To determine if the runtime has been
                          updated, check the runtime version in the INIT_START log entry. If this error correlates with a change in the
                          runtime version, you may be able to mitigate this error by temporarily rolling back to the previous runtime
                          version. For more information, see https://docs.aws.amazon.com/lambda/latest/dg/runtimes-update.html
[ERROR] Runtime.ImportModuleError: Unable to import module 'handler': No module named 'aws_lambda_typing'
INIT_REPORT Init Duration: 374.97 ms      Phase: init     Status: error       Error Type: Runtime.ImportModuleError
START RequestId: 12312312-2342-3453-4564-567567ffeedd Version: $LATEST... END RequestId: 12312312-2342-3453-4564-567567ffeedd
REPORT RequestId: 12312312-2342-3453-4564-567567ffeedd    Duration: 256.18 ms Billed Duration: 257 ms Memory Size: 256 MB     Max Memory Used: 65 MB  Status: error   Error Type: Runtime.ImportModuleError
```

In this case, I forgot to add a guard around the typing packages for lambda.

### Deleting a deployment

```sh
sam delete --stack-name soundcloud-proxy
```

### Parameters

| Parameter          | Default          | Description                   |
|--------------------|------------------|-------------------------------|
| TableName          | soundcloud-proxy | DynamoDB table name           |
| RateLimitSeconds   | 1                | Global rate limit (seconds)   |
| ClientIdTtlSeconds | 120              | How long to cache `client_id` |

If overriding during deploy without `--guided`:

```sh
sam deploy --parameter-overrides RateLimitSeconds=5 ClientIdTtlSeconds=300
```

## GitHub Pages Setup

1. Fork/clone this repo

2. Add the API URL as a repository variable:
   - Go to Settings > Secrets and variables > Actions > Variables
   - Add variable: `API_BASE_URL` = (`ApiUrl` from earlier)
   - Example: `https://abc123.execute-api.us-east-1.amazonaws.com/prod`

3. Enable GitHub Pages:
   - Go to Settings > Pages
   - Source: GitHub Actions

4. Push to `main` / manually trigger workflow

## Local Development

The frontend defaults to sending requests to `http://localhost:3000` when the API URL placeholder is unchanged.

To start the API on port 3000 locally:
```sh
sam local start-api
```

However, this requires Docker.

Alternatively, edit `API_BASE` in **index.html** to point to any endpoint.

## API Endpoints

### GET /username

Resolves a SoundCloud username to info used by **index.html**.

```
/username?username=someuser
```

Returns: `id`, `urn`, `username`, `permalink_url`, `avatar_url`

### GET /likes

Returns a user's liked tracks.

```
/likes?urn=93060898&limit=1000
```

- `urn`: numeric user id from the urn field
- `limit`: max likes to return (default: all, i.e. 50000)

If this limit is somehow not enough for you, raise an issue with a use case to justify it.

### GET /health

Basic health check that returns the current configuration and whether or not `client_id` is available.

### OPTIONS

CORS preflight. Returns HTTP 200.

## Rate Limiting

**handler.py** enforces a global rate limit (default 1 req/sec across all users) to avoid concerns with hitting SoundCloud too hard, especially with the limit being a default of all likes. If rate limited, wait and retry. I don't suspect enough people to use this to matter though.

## Notes

- SoundCloud may change their frontend at any time, breaking `client_id` scraping
- This is for personal use - don't abuse it
