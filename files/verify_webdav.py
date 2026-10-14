#!/usr/bin/python3
"""Exercise real HTTPS WebDAV transfers; read credentials from stdin only."""
import base64
import hashlib
import json
import ssl
import sys
import urllib.error
import urllib.request
import uuid


def main():
    config = json.load(sys.stdin)
    context = ssl.create_default_context(cafile=config['ca'])
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=context))
    url = config['endpoint'].rstrip('/') + '/.ansible-smoke-' + uuid.uuid4().hex
    payload = b'dCache Ansible integration test\n' + bytes(range(256)) * 1024
    token = base64.b64encode((config['user'] + ':' + config['password']).encode()).decode()

    def request(method, body=None, authenticate=True):
        headers = {'Authorization': 'Basic ' + token} if authenticate else {}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with opener.open(req, timeout=60) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    created = False
    try:
        code, _ = request('PUT', payload)
        assert code in (200, 201, 204), 'PUT returned ' + str(code)
        created = True
        code, downloaded = request('GET')
        assert code == 200 and downloaded == payload, 'Downloaded content mismatch'
        code, _ = request('GET', authenticate=False)
        assert code in (401, 403), 'Unauthenticated file access was accepted'
        code, _ = request('DELETE')
        assert code in (200, 204), 'DELETE returned ' + str(code)
        created = False
        code, _ = request('GET')
        assert code == 404, 'Deleted file remains available'
        print('DCACHE_SMOKE_OK sha256=' + hashlib.sha256(downloaded).hexdigest())
    finally:
        if created:
            request('DELETE')


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('DCACHE_SMOKE_FAILED: ' + type(error).__name__ + ': ' + str(error), file=sys.stderr)
        sys.exit(1)

