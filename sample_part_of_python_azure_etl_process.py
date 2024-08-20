from azure.storage.blob import BlobServiceClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
import io
import json
import logging, sys
import os
import pandas as pd
import requests

# INPUTS
# Expected number of columns to exist in the first sheet/transformed dataset of the new file
EXPECTED_NO_COLUMNS = 30
# Set file paths
SOURCE_FOLDER_NAME = 'SourceFilePath/SourceFolder'
TARGET_FOLDER_NAME = 'TargetFilePath/TargetFolder'
TARGET_SHEET1_NAME = 'Sheet1'
TARGET_SHEET2_NAME = 'Sheet2'
TARGET_SHEET3_NAME = 'Sheet3'
# Set name values of clean column names to pull into the dataframe
COLUMN_NAMES=['Column1', 'Column2', 'Column3', 'Column4', 'Column5', 'Column6', 
              'Column7', 'Column8', 'Column9', 'Column10', 'Column11', 'Column12', 
              'Column13', 'Column14', 'Column15', 'Column16', 'Column17', 'Column18', 
              'Column19', 'Column20', 'Column21', 'Column22', 'Column23', 'Column24', 
              'Column25', 'Column26', 'Column27', 'Column28', 'Column29', 'Column30'
]
# END OF INPUTS


class AuthenticateGraphAPI():
    '''
    Takes a tenant id, client id, and secret value (not secret id)
    Must create an access token via the generate_access_token method
    Able to access various header strings depending on what type of data you are accessing

    # Example code:
    api_auth_object = AuthenticateGraphAPI(api_tenant_id, api_client_id, api_secret)
    api_auth_object.generate_access_token()
    drive_url = f'https://graph.microsoft.com/v1.0/sites/{mapping_site_id}/drives/{mapping_drive_id}/root/children'
    sharepoint_drive = requests.get(drive_url, headers=api_auth_object.headers_binary).json()
    '''
    def __init__(self, tenant_id, client_id, secret_value): 
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.secret_value = secret_value
        self.url = f'https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token'
        self.access_token = None
  
    def generate_access_token(self):
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.secret_value,
            'scope': 'https://graph.microsoft.com/.default'
        }
        response = requests.post(self.url, data=data)
        if response.status_code in [200, 204]:
            logging.debug("Created Access token successfully!")
        else:
            logging.debug(f"Failed to create access token: {response.status_code}, {response.text}")
        self.access_token = response.json()['access_token']
        return self.access_token
    
    @property
    def headers_binary(self):
        headers_binary = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream'
            }
        return headers_binary
    
    @property
    def headers_json(self):
        headers_json = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
        return headers_json


class InteractWithGraphAPI(AuthenticateGraphAPI):
    '''
    Takes a tenant id, client id, and secret value (not secret id)
    Must create an access token via the generate_access_token method in the AuthenticateGraphAPI parent class

    # Example code:
    sharepoint_object = InteractWithGraphAPI(api_tenant_id, api_client_id, api_secret)
    sharepoint_object.generate_access_token()
    '''
    def __init__(self, tenant_id, client_id, secret_value):
        super().__init__(tenant_id, client_id, secret_value)

    def download_files(self, drive_url, text_in_file_name):
        '''
        This method returns all file content for files in the drive_url which have a file name that contains text which matches text_in_file_name
        For example, if text_in_file_name = 'Sample Text' any file in the drive_url with 'Sample Text' in it's name 
        will have it's byte data pulled down and returned in an iterable dictionary object with a key value of the file name
        '''
        sharepoint_drive = requests.get(drive_url, headers=self.headers_binary).json()
        download_content = {}
        for item in sharepoint_drive.get('value', []):
            if text_in_file_name in item.get('name'):
                file_name = item.get('name')
                file_download = item.get('@microsoft.graph.downloadUrl')
                response = requests.get(file_download)
                download_content[file_name] = response.content
        return download_content
    
    def upload_files(self, drive_url, file_name, data):
        pass

    def update_metadata(self, item_url, field_name, field_value):
        '''
        This method is used to update metadata values in sharepoint files

        # Example code:
        file_url = 'https://graph.microsoft.com/v1.0/sites/nameofcompany.sharepoint.com,123,123/drives/123/items/123/listItem/fields'
        sharepoint_object.update_metadata(file_url, 'MetaDataCode', 'XXXXXXXXX')
        '''
        data = json.dumps({field_name: field_value})
        response = requests.patch(item_url, headers=self.headers_json, data=data)
        if response.status_code in [200, 204]:
            logging.debug("Metadata updated successfully.")
        else:
            logging.debug(f"Failed to update metadata: {response.status_code}, {response.text}")
 

class AuthenticateBlobStorage():
    '''
    Takes a blob storage account name value and blob storage account key value
    Find this data in the azure portal > storage accounts > name of storage account using > security + networking > access keys
    Must run the blob_service_client method to create a BlobServiceClient your code can interact with

    # Example code:
    blob_auth = AuthenticateBlobStorage(storage_account_name, storage_account_key)
    blob_service_client = blob_auth.blob_service_client()
    '''
    def __init__(self, name_value, key_value): 
        self.name_value = name_value
        self.key_value = key_value
        self.url = f'https://{self.name_value}.blob.core.windows.net/'

    def blob_service_client(self):
        blob_credentials = {
            'account_name': self.name_value,
            'account_key': self.key_value
            }
        self.blob_service_client=BlobServiceClient(account_url=self.url,credential=blob_credentials)
        return self.blob_service_client
    

class InteractWithBlobs():
    '''
    Pass in a BlobServiceClient generated by AuthenticateBlobStorage and a storage container name to use this class

    # Example code:
    blob_auth = AuthenticateBlobStorage(storage_account_name, storage_account_key)
    blob_service_client = blob_auth.blob_service_client()
    source_container = InteractWithBlobs(blob_service_client, source_container_name)
    source_container.remove_files_in_container()
    '''
    def __init__(self, blob_service_client, container):
        self.blob_service_client = blob_service_client
        self.container = container
        self.container_client = self.blob_service_client.get_container_client(container=self.container)
        self.df = None
  
    def upload_file(self, file_name, data):
        self.container_client.upload_blob(name=file_name, data=data, overwrite=True)

    def upload_df_to_file(self, df, file_name, sheet_name, startrow):
        # Error handle already opened excel file.  Not sure if this should be more robust?  Will this be an issue in Sharepoint?
        try:
            excel_stream = io.BytesIO()
            with pd.ExcelWriter(excel_stream) as xlsx:
                df.to_excel(xlsx, sheet_name=sheet_name, startrow=startrow, index=False)
            excel_stream.seek(0)
            self.container_client.upload_blob(name=file_name, data=excel_stream.getvalue(), overwrite=True)
        except PermissionError: 
            print(f'need to close {file_name} file')

    def upload_dfs_to_file(self, parameters=None):
        # Error handle already opened excel file.  Not sure if this should be more robust?  Will this be an issue in Sharepoint?
        try:
            excel_stream = io.BytesIO()
            with pd.ExcelWriter(excel_stream) as xlsx:
                for df, file_name, sheet_name, startrow, header in parameters:
                    df.to_excel(xlsx, sheet_name=sheet_name, startrow=startrow, header=header, index=False)
                    xlsx.sheets[sheet_name].set_column(0, 30, 20)
            excel_stream.seek(0)
            self.container_client.upload_blob(name=file_name, data=excel_stream.getvalue(), overwrite=True)
        except PermissionError: 
            print(f'need to close {file_name} file')

    def download_file(self, file_name):
        download_file = self.container_client.download_blob(blob=file_name).readall()
        return download_file

    def download_dataframe_from_file(self, file_name, sheet_name, skiprows=None, nrows=None):
        self.df = pd.read_excel(io.BytesIO(self.download_file(file_name)), sheet_name=sheet_name, skiprows=skiprows, nrows=nrows) 
        return self.df
    
    def get_first_value_from_df_header(self, file_name, sheet_name, skiprows):
        df_first_value = self.download_dataframe_from_file(file_name, sheet_name, skiprows)
        value = df_first_value.columns.values[0]
        return value
    
    def remove_files_in_container(self):
        blob_list = self.container_client.list_blobs()
        for blob in blob_list:
            self.container_client.delete_blob(blob=blob.name)


class InteractWithDataFrame():
    # Class variable used to store count of new columns and old column names
    column_names_list = list()

    def __init__(self, df):
        self.df = df

    @classmethod
    def generate_column_header_file(cls, df_columns, item_number, no_clean_columns):
        column_header_data = [''.join(map(lambda x: x, list(item_number)[0:7]))] + list(df_columns.columns)
        InteractWithDataFrame.column_names_list.append([''.join(map(lambda x: x, list(no_clean_columns)[0:2]))] + column_header_data)

    def clean_special_characters_df_columns(self, list_of_characters):
        special_character_patterns = '|'.join(list_of_characters)
        self.df.columns = self.df.columns.str.replace(special_character_patterns, ' ', regex=True)
        # Clean double whitespaces
        self.df.columns = self.df.columns.str.replace('  ', ' ')
        self.df.columns = self.df.columns.str.replace('  ', ' ')
        logging.debug("Cleaned Dataframe Columns:")
        logging.debug(self.df.columns)   

    # Set dataframe to only contain columns that match column_names values
    def select_columns(self, column_names):
        self.df = self.df[[col for col in column_names if col in self.df.columns]]

    def remove_most_values_after_blank_row(self):
        null_mask = self.df.isnull().all(axis=1)
        first_null_row_index_value = self.df[null_mask].index.values[0]
        self.df = self.df[self.df.index < first_null_row_index_value + 2]

    def check_no_columns(self, expected_no_cols):
        no_cols = len(self.df.axes[1])
        str_no_cols = str(no_cols)
        if expected_no_cols > no_cols:
            print("Missing Columns! only " + str_no_cols)
        if expected_no_cols < no_cols:
            print("Too Many Columns! There are " + str_no_cols)
        return str_no_cols
    
    def lookup_value(self, key_column, lookup_key_value, lookup_column):
        try:
            lookup_value = self.df.loc[self.df[key_column] == int(lookup_key_value), [lookup_column]].values[0][0]
        except ValueError:
            lookup_value = self.df.loc[self.df[key_column] == str(lookup_key_value), [lookup_column]].values[0][0]
        if lookup_value == False:
            print(f'!!!Missing {lookup_column} or key data in Mapping file!!!') 
        lookup_value = lookup_key_value if lookup_value == False else lookup_value
        return lookup_value
