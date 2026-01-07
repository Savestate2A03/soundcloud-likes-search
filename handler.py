# soundcloud API proxy for aws lambda
# - rate limited (1 request per second globally)
# - gets client_id every 2 minutes
# - exposes only /resolve and /likes

from __future__ import annotations

import json
import re
import time
import urllib.request
import urllib.parse
import os
import boto3
import inspect
from decimal import Decimal
from collections.abc import Callable

# don't get aws lambda type modules if not at runtime
from typing import TYPE_CHECKING, TypeVar, Optional, Any, Self

if TYPE_CHECKING:
    from aws_lambda_typing import context as context_
    from aws_lambda_typing.events import APIGatewayProxyEventV1
    from aws_lambda_typing.responses import APIGatewayProxyResponseV1

T = TypeVar('T')
SOUNDCLOUD_URL = 'https://soundcloud.com/'

# defaults, can be overridden via env vars
RATE_LIMIT_SECONDS = int(os.environ.get('RATE_LIMIT_SECONDS', '1'))
CLIENT_ID_TTL_SECONDS = int(os.environ.get('CLIENT_ID_TTL_SECONDS', '120'))

# < logger > #################################################################

class Logger:
    def __init__(self: Self, base_depth: int | None = None) -> None:
        self._base_depth = base_depth if base_depth is not None else len(inspect.stack())

    def log(self: Self, message: str) -> None:
        stack = inspect.stack()
        depth = max(0, len(stack) - self._base_depth - 1)
        caller_name = stack[1].function

        if depth == 0:
            prefix = ""
        else:
            prefix = "|   " * (depth - 1) + "|-- "

        print(f"{prefix}[{caller_name}] {message}")

LOGGER = Logger()

# < dynamodb > ###############################################################

DYNAMODB = boto3.resource('dynamodb')
TABLE = DYNAMODB.Table(os.environ.get('TABLE_NAME', 'soundcloud-proxy'))
CdtlChkFldEx = DYNAMODB.meta.client.exceptions.ConditionalCheckFailedException

# attempt to get client_id from dynamodb
def get_cached_client_id() -> Optional[str]:
    LOGGER.log("GETTING CACHED client_id")

    try:
        response = TABLE.get_item(Key={'pk': 'client_id'})
        if 'Item' in response:
            item = response['Item']
            expires_at = float(str(item.get('expires_at', 0)))  # Decimal -> float
            if time.time() < expires_at:
                return str(item['value'])
            
    except Exception as error:
        LOGGER.log(f"(error) DYNAMODB READ ERROR: {error}")

    return None

# attempt to save client_id to dynamodb
def save_client_id(client_id: str) -> None:
    ttl = int(CLIENT_ID_TTL_SECONDS)

    try:
        TABLE.put_item(Item={
            'pk': 'client_id',
            'value': client_id,
            'expires_at': Decimal(str(time.time() + ttl)),
            'updated_at': Decimal(str(time.time()))
        })

    except Exception as error:
        LOGGER.log(f"(error) DYNAMODB WRITE ERROR: {error}")

# make sure requests aren't being made beyond the rate limit
def check_rate_limit() -> bool:
    now = Decimal(str(time.time()))
    threshold = Decimal(str(time.time() - int(RATE_LIMIT_SECONDS)))

    try:
        TABLE.update_item(
            Key={'pk': 'rate_limit'},
            UpdateExpression='SET last_request = :now',
            ConditionExpression='attribute_not_exists(last_request) OR last_request < :threshold',
            ExpressionAttributeValues={
                ':now': now,
                ':threshold': threshold
            },
            ReturnValues='ALL_NEW'
        )
        return True
    
    except CdtlChkFldEx:
        return False
    
    except Exception as error:
        LOGGER.log(f"(error) RATE LIMIT CHECK ERROR: {error}")
        return True

# < web scraping utilities > #################################################

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/128.0.0.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Charset': 'UTF-8'
}

# request wrapper returning the callback function that handles data
def request(url: str, callback: Callable[[str], T],user_headers: dict[str, str] = {}) -> Optional[T]:

    try:
        req = urllib.request.Request(url, headers={**HEADERS, **user_headers})
        with urllib.request.urlopen(req, timeout=10) as resp:
            ret = callback(resp.read().decode('utf-8', errors='ignore'))
            return ret
        
    except Exception as error:
        LOGGER.log(f"(error) ERROR FETCHING {url}: {error}")
        return None

def client_id_from_js(js) -> Optional[str]:
    LOGGER.log(f"ATTEMPTING TO EXTRACT client_id FROM '{js}'...")
    regex = r'[^A-Za-z0-9_]client_id:[\'"]([a-zA-Z0-9]+)[\'"]'
    match = re.search(regex, js)

    if match:
        client_id = match.group(1)
        LOGGER.log(f"client_id EXTRACTED! {js}: '{client_id}'")
        return client_id
    
    return None

def search_js_scripts_for_client_id(html) -> Optional[str]:
    regex = r'src="(https:\/\/[^"]*sndcdn\.com[^"]*\.js)"'
    script_urls = re.findall(regex, html)
    script_urls.reverse() # the containing script is usually at the bottom
    LOGGER.log(f"COLLECTED HOMEPAGE SCRIPTS. TOTAL: {len(script_urls)}")

    for url in script_urls:
        client_id = request(url, client_id_from_js)
        if client_id:
            return client_id
    
    LOGGER.log("(error) NO client_id FOUND IN SCRIPTS")
    return None

def scrape() -> Optional[str]:
    client_id = request(SOUNDCLOUD_URL, search_js_scripts_for_client_id)

    if client_id:
        LOGGER.log("SCRAPING HOMEPAGE SUCCESSFUL!")
        return client_id
    
    LOGGER.log(f"(error) FAILURE IN SCRAPING HOMEPAGE {SOUNDCLOUD_URL}")
    return None

# < main logic > #############################################################

def get_client_id() -> str:
    client_id = get_cached_client_id()

    if client_id:
        LOGGER.log(f"USING CACHED client_id: '{client_id[:8]}'...")
        return client_id
    
    LOGGER.log("SCRAPING FOR client_id")

    client_id = scrape()

    if client_id:
        LOGGER.log(f"GOT client_id! '{client_id[:8]}'. SAVING...")
        save_client_id(client_id)
        return client_id
    
    raise Exception("(error) COULD NOT GET client_id FROM CACHE OR SCRAPE")

def proxy_soundcloud(endpoint, params) -> Optional[Any]:
    LOGGER.log("PROXYING SOUNDCLOUD API")

    client_id = get_client_id()

    # build GET url query parameters
    base_url = 'https://api-v2.soundcloud.com'
    params['client_id'] = client_id
    query_string = '&'.join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"{base_url}{endpoint}?{query_string}"

    LOGGER.log(f"PROXYING TO: {url}")

    def to_dict(body: str) -> Optional[Any]:
        return json.loads(body)

    return request(url, to_dict, {'Accept': 'application/json'})

# < lambda > #################################################################

def cors(status: int, b: Any) -> APIGatewayProxyResponseV1:
    b = {'error': b} if status != 200 and isinstance(b, str) else b

    return {
        'statusCode': status,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(b)
    }

def lambda_handler(event: APIGatewayProxyEventV1, context: context_.Context) -> APIGatewayProxyResponseV1:
    # preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors(200, '')

    ### ENDPOINTS ##############################################
    try:
        path = event.get('path', '')
        query_params = event.get('queryStringParameters') or {}
        
        ### /username ##########################################
        if path == '/username':
            username = query_params.get('username', '')

            if not username:
                return cors(400, {
                    'error': 'PARAMETER_ERROR',
                    'parameter': 'username',
                    'type': 'missing'
                })
            
            if not re.match(r'^[\w-]+$', username):
                return cors(400, {
                    'error': 'PARAMETER_ERROR',
                    'parameter': 'username',
                    'type': 'invalid'
                })

            url = f'https://soundcloud.com/{username}'
            data = proxy_soundcloud('/resolve', {'url': url})
            
            if data and data.get('kind') != 'user':
                return cors(400, 'NOT_A_USER_ERROR')
            
            if data:
                return cors(200, {
                    'id': data.get('id') or '',
                    'urn': data.get('urn') or '',
                    'username': data.get('username') or '',
                    'permalink_url': data.get('permalink_url') or '',
                    'avatar_url': data.get('avatar_url') or '',
                })
            
            return cors(400, 'USER_RESOLVE_ERROR')

        ### /likes #############################################
        if path == '/likes':

            # check rate limit
            if not check_rate_limit():
                body = {
                    'error': 'RATE_LIMITED_ERROR',
                    'message': f'PLEASE WAIT {RATE_LIMIT_SECONDS} SECONDS AND TRY AGAIN',
                    'retry_after': RATE_LIMIT_SECONDS
                }
                return cors(429, body)
            
            urn = query_params.get('urn')

            if not urn:
                return cors(400, {
                    'error': 'PARAMETER_ERROR',
                    'parameter': 'urn',
                    'type': 'missing'
                })
            
            if not urn.isdigit():
                return cors(400, {
                    'error': 'PARAMETER_ERROR',
                    'parameter': 'urn',
                    'type': 'invalid'
                })

            limit = min(int(query_params.get('limit', 50000)), 50000)

            data = proxy_soundcloud(
                f'/users/{urn}/likes',
                {'limit': limit}
            )

            if data:
                return cors(200, data)
            
            return cors(400, 'USER_LIKES_ERROR')

        ### /health ############################################
        if path == '/health':
            client_id = get_client_id()
            info = {
                'status': 'ok',
                'client_id': client_id[:8] + '...' if client_id else 'NO client_id FOUND',
                'rate_limit_seconds': RATE_LIMIT_SECONDS,
                'client_id_ttl_seconds': CLIENT_ID_TTL_SECONDS
            }
            return cors(200, info)

        ### 404 ################################################
        return cors(404, {
            'error': 'NOT_FOUND_ERROR',
            'endpoints': [
                {
                    'endpoint': '/username',
                    'params': ['username']
                },
                {
                    'endpoint': '/likes',
                    'params': ['urn']
                },
                {
                    'endpoint': '/health',
                    'params': []
                }
            ]
        })

    except Exception as error:
        LOGGER.log(f"ERROR: {error}")
        return cors(500, {
            'error': 'UNKNOWN_ERROR',
            'message': str(error)
        })

if __name__ == '__main__':
    client_id = get_client_id()
    LOGGER.log(f"SCRAPED client_id: {client_id}")
