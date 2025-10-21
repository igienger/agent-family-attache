
# Before you begin

**Install dependencies**

MacOS
```
$ brew tap hashicorp/tap
$ brew tap infisical/get-cli
$ brew install gcloud-cli hashicorp/tap/terraform infisical/get-cli/infisical hashicorp/tap/terraform
```

**Setup gcloud CLI & authenticate**

Project ID: `family-services-475820`

```
$ gcloud init
$ gcloud auth application-default login
```

# Running Terraform

```
$ infisical run --env=dev --path=/terraform -- terraform init
$ infisical run --env=dev --path=/terraform -- terraform plan
$ infisical run --env=dev --path=/terraform -- terraform apply
```

# Appendix

### One-time manual OAuth setup

Google APIs OAuth 2.0 Client IDs cannot be created programmatically, so they must be created in the UI.
https://console.cloud.google.com/apis/credentials?project=family-services-475820

We saved the client secret JSON file to Infisical using:
```
$ brew install jq
$ export SECRET_FILE=/path/to/file
$ infisical secrets set \
    OAUTH_CLIENT_SECRET_JSON=@$SECRET_FILE \
    OAUTH_CLIENT_ID=$(jq -r '.installed.client_id' $SECRET_FILE) \
    OAUTH_CLIENT_SECRET=$(jq -r '.installed.client_secret' $SECRET_FILE) \
    --path="/gcloud/projects/family-services-475820/" \
    --env=dev \
    > /dev/null \
    && echo "Secrets uploaded\!"
```
