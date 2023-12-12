from flask import Flask, request, Response
import requests

app = Flask(__name__)
SITE_NAME = 'http://18.133.31.185/'

@app.route('/<path:path>',methods=['GET'])
def proxy_get(path):
    # get headers
    auth = request.headers.get('Authorization')

    # makes get request to site
    resp = requests.get(f'{SITE_NAME}{path}', headers={'Authorization': auth})

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    return response # sends response to user

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)