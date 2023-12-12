from flask import Flask, request, Response
import requests

app = Flask(__name__)
SITE_NAME = 'http://18.133.31.185/'

# Valid paths and methods
VALID = {
    'CATEGORIES' : ['hospitals', 'staffs', 'patients', 'notes'],

    'GET' : ['hospitals', 'hospitals/<id>', 
            'staffs', 'staffs/<id>', 'staffs/me'
            'patients', 'patients/<id>',
            'notes', 'notes/<id>'],
    
    'DELETE' : ['hospitals/<id>', 
                'staffs/<id>', 
                'patients/<id>', 
                'notes/<id>'],
}

# validate the Get method path
def validate_get_path(path):
    # split the path
    path = path.split('/')

    # check length of path
    if len(path) > 2:
        return False
    
    # get first part of path is valid category
    if path[0] not in VALID['CATEGORIES']:
        return False
    
    # if theres a second part to the path
    if len(path) == 2:

        # handle staff separately
        if path[0] != 'staffs':
            # check if second part is a number
            if not path[1].isdigit():
                return False
        # handle staff
        else:
            # check if second part is me or a number
            if (path[1] != 'me') and (not path[1].isdigit()):
                return False
    
    return True

# validate the Delete method path
def validate_delete_path(path):
    # split path
    path = path.split('/')

    # check if length is not 2
    if len(path) != 2:
        return False
    
    # check if first part is valid category
    if path[0] not in VALID['CATEGORIES']:
        return False
    
    # check if second part is a number
    if not path[1].isdigit():
        return False
    
    return True

@app.route('/<path:path>',methods=['GET'])
def proxy_get(path):

    # get headers
    auth = request.headers.get('Authorization')

    # validate auth included
    if not auth:
        return Response('No Authorization header', 401)
    
    # check if path valid
    if not validate_get_path(path):
        return Response('Invalid request', 404)

    # makes get request to site
    resp = requests.get(f'{SITE_NAME}{path}', headers={'Authorization': auth})

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    return response # sends response to user

@app.route('/<path:path>',methods=['DELETE'])
def proxy_delete(path):
    # get headers
    auth = request.headers.get('Authorization')

    # validate auth included
    if not auth:
        return Response('No Authorization header', 401)
    
    # check if path valid
    if not validate_delete_path(path):
        return Response('Invalid request', 404)

    # makes get request to site
    resp = requests.delete(f'{SITE_NAME}{path}', headers={'Authorization': auth})

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    return response # sends response to user

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)