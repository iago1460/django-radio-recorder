from aiohttp import ClientSession, ClientTimeout

from radioco_recorder.const import REQUEST_TIMEOUT


async def get_episodes(radioco_endpoint, token, language, params):
    return await _request_json(
        url=f'{radioco_endpoint}/api/1/recording_schedules/',
        headers={
            'Accept-Language': language,
            'Authorization': f'Token {token}'
        },
        params=params
    )


async def submit_episode(radioco_endpoint, token, params):
    return await _request_json(
        url=f'{radioco_endpoint}/api/1/submit_recorder/',
        headers={
            'Authorization': f'Token {token}'
        },
        params=params
    )


async def _request_json(url, headers, params):
    client_timeout = ClientTimeout(total=REQUEST_TIMEOUT)
    async with ClientSession(timeout=client_timeout) as session:
        async with session.get(url, params=params, headers={
            'Content-Type': 'application/json',
            **headers
        }) as response:
            response.raise_for_status()
            return await response.json(encoding='utf-8', content_type=None)
