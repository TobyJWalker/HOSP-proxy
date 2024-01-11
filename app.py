from flask import Flask, request, Response
from flask_caching import Cache
import base64
import requests
import json
import redis

config = {
    "CACHE_TYPE": "RedisCache",  # Flask-Caching related configs
    "CACHE_REDIS_HOST": "redis",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_DB": 0,
    "CACHE_REDIS_URL": "redis://redis:6379/0",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app = Flask(__name__)
SITE_NAME = 'http://18.133.31.185/'

# load config and create cache
app.config.from_mapping(config)
cache = Cache(app)

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
    
    'POST' : ['hospitals',
            'staffs',
            'patients', 'patients/<id>/screen'
            'notes'],
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

# validate the Post method path
def validate_post_path(path):
    # split path
    path = path.split('/')

    # check if length is not 1
    if len(path) != 1 and len(path) != 3:
        return False
    
    # check 3 length path is valid]
    if len(path) == 3 and (path[0] != 'patients' or path[2] != 'screen' or not path[1].isdigit()):
        return False
    
    # check if first part is valid category
    if path[0] not in VALID['CATEGORIES']:
        return False
    
    return True

# validate post content
def validate_post_content(content, path):
    # check if content is json
    try:
        data = json.loads(content)
    except:
        return 406
    
    # get the object type to make
    path = path.split('/')
    obj = path[0]

    # check content matches object
    if obj == 'hospitals':
        if not 'name' in data.keys():
            return 400
        
    elif obj == 'patients':
        if len(path) == 1:
            if not all(key in data.keys() for key in ['name', 'hospital_id', 'birthdate']):
                return 400
        else:
            if not 'images' in data.keys():
                return 400
    
    elif obj == 'staffs':
        if not all(key in data.keys() for key in ['name', 'hospital_id', 'password']):
            return 400
    
    elif obj == 'notes':
        if not all(key in data.keys() for key in ['title', 'body', 'patient_id', 'staff_id']):
            return 400
    
    else:
        return 404
    
    return 200

# validate the Post method path
def validate_patch_path(path):
    # split path
    path = path.split('/')

    # check if length is not 2
    if len(path) != 2:
        return False
    
    # check if first part is valid category
    if path[0] not in VALID['CATEGORIES']:
        return False
    
    if not path[1].isdigit():
        return False
    
    return True

# validate post content
def validate_patch_content(content, path):
    # check if content is json
    try:
        data = json.loads(content)
    except:
        return 406
    
    # get the object type to make
    path = path.split('/')
    obj = path[0]

    # check content matches object
    if obj == 'hospitals':
        if not 'name' in data.keys():
            return 400
        
    elif obj == 'patients':
        if len(path) == 1:
            if not all(key in ['name', 'hospital_id', 'birthdate'] for key in data.keys()):
                return 400
    
    elif obj == 'staffs':
        if not all(key in ['name', 'hospital_id', 'password'] for key in data.keys()):
            return 400
    
    elif obj == 'notes':
        if not all(key in ['title', 'body', 'patient_id', 'staff_id'] for key in data.keys()):
            return 400
    
    else:
        return 404
    
    return 200

# checks a response for a 500 error
def check_500(resp):
    if resp.status_code in [400, 401, 403, 404, 405, 406, 500, 503]:
        return False
    else:
        return True

def log(event):
    requests.post('https://pg9t2w92n4.execute-api.eu-west-2.amazonaws.com/blip-logging', data=event)

def get_staff_id(auth):
    resp = requests.get(f'{SITE_NAME}staffs/me', headers={'Authorization': auth})
    try:
        staff_data = json.loads(resp.content)
        return staff_data['id']
    except:
        return None
    
# get staff name from auth string
def get_staff_name(auth):
    try:
        # converting the base64 code into ascii characters
        convertbytes = auth.encode("utf-8")
        # converting into bytes from base64 system
        convertedbytes = base64.b64decode(convertbytes)
        print(convertedbytes)
        # decoding the auth string
        decoded_auth = convertedbytes.decode("utf-8")

        # splitting the auth string into username and password
        username = decoded_auth.split(':')[0]
    except:
        username = None

    return username if username != '' or username.isspace() else None
    
# make a cache key to incorporate the authorisation header
def make_key(path):
    auth_head = request.headers.get('Authorization', '')
    return f"{request.path}:{auth_head}" # return formulated cache key

@app.route('/', methods=['GET'])
def proxy_index():
    # makes get request to site
    resp = requests.get(f'{SITE_NAME}')

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    return response # sends response to user

@app.route('/<path:path>',methods=['GET'])
@cache.cached(timeout=300, response_filter=check_500, make_cache_key=make_key) # cache the response if it is not an error for 30 seconds
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
    for i in range(3):
        resp = requests.get(f'{SITE_NAME}{path}', headers=request.headers)
        if resp.status_code != 500:
            break

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    #log_request
    try:
        if resp.status_code in [200, 201]:
            staff_name = get_staff_name(auth)
            log_string = f"{staff_name} requested to view {path}"
            log(log_string)
    except:
        pass

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
    for i in range(3):
        resp = requests.delete(f'{SITE_NAME}{path}', headers=request.headers)
        if resp.status_code != 500:
            break

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    #log_request
    try:
        if resp.status_code in [200, 201]:
            staff_name = get_staff_name(auth)
            try:
                json.loads(resp.content)
                log_string = f"{staff_name} deleted {path}"
            except:
                log_string = f"{staff_name} attempted to delete {path}"
        
            log(log_string)
    except:
        pass
    
    return response # sends response to user

@app.route('/<path:path>',methods=['POST'])
def proxy_post(path):

    # get headers
    auth = request.headers.get('Authorization')
    content_type = request.headers.get('Content-Type')

    # get data
    data = request.data

    # validate headers
    if not auth:
        return Response('No Authorization header', 401)
    if content_type != 'application/json':
        return Response('Invalid Content-Type', 406)
    
    # validate post path
    if not validate_post_path(path):
        return Response('Invalid path', 404)
    
    # validate post content
    status = validate_post_content(data, path)
    if status == 400:
        return Response('Invalid content', 400)
    elif status == 404:
        return Response('Invalid request', 404)
    elif status == 406:
        return Response('Invalid Content-Type', 406)
    
    # ensure the correct staff id is added to the note 
    if path == 'notes':
        staff_id = get_staff_id(auth)
        if staff_id == None:
            return Response('Invalid Credentials', 401)
        post_data = json.loads(data)
        post_data['staff_id'] = staff_id 
        data = json.dumps(post_data)           

    # makes get request to site
    for i in range(3):
        resp = requests.post(f'{SITE_NAME}{path}', headers=request.headers, data=data)
        if resp.status_code != 500:
            break

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    # create a note of screening data
    if path.split('/')[-1] == 'screen':
        # get the staff id related to the provided authorization
        staff_id = get_staff_id(auth)
        if staff_id == None:
            return Response('Invalid Credentials', 401)
        
        # get patient id from path and images from post request
        patient_id = path.split('/')[1]
        images = json.loads(data)['images']

        # get screening results
        screen_results = json.loads(resp.content)

        # create body of note
        body = f"Overall: {screen_results['overall']},  "
        for index, image in enumerate(images):
            body += f"{image}: {screen_results['results'][index]}, "
        
        # create json data for post request
        note_data = {
            'title': f"Patient {patient_id} Screening",
            'body': body[:-2],
            'patient_id': patient_id,
            'staff_id': staff_id
        }
        
        # make notes post request
        resp_notes = requests.post(f'{SITE_NAME}notes', headers={'Authorization': auth, 'Content-type': 'application/json'}, data=json.dumps(note_data))

        # check if request was successful
        if resp_notes.status_code != 201:
            print('Screening note creation failed')

    #log_request
    try:
        if resp.status_code in [200, 201]:
            staff_name = get_staff_name(auth)
            try:
                content = json.loads(resp.content)
                if path.split('/')[-1] == 'screen':
                    log_string = f"{staff_name} created a screening for patient {path.split('/')[1]}"
                else:
                    log_string = f"{staff_name} created {path} {content['id']}"
                    
                log(log_string)
            except:
                return response
    except:
        pass

    return response # sends response to user

@app.route('/<path:path>',methods=['PATCH'])
def proxy_patch(path):

    # get headers
    auth = request.headers.get('Authorization')
    content_type = request.headers.get('Content-Type')

    # get data
    data = request.data

    # validate headers
    if not auth:
        return Response('No Authorization header', 401)
    if content_type != 'application/json':
        return Response('Invalid Content-Type', 406)
    
    # validate post path
    if not validate_patch_path(path):
        return Response('Invalid path', 404)
    
    # validate post content
    status = validate_patch_content(data, path)
    if status == 400:
        return Response('Invalid content', 400)
    elif status == 404:
        return Response('Invalid request', 404)
    elif status == 406:
        return Response('Invalid Content-Type', 406)

    # makes get request to site
    for i in range(3):  
        resp = requests.patch(f'{SITE_NAME}{path}', headers=request.headers, data=request.data)
        if resp.status_code != 500:
            break

    # adds headers to the response (excluding specified)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]

    # create response object
    response = Response(resp.content, resp.status_code, headers)

    #log_request
    try:
        if resp.status_code in [200, 201]:
            staff_name = get_staff_name(auth)
            try:
                content = json.loads(resp.content)
                log_string = f"{staff_name} updated {path}"
            except:
                log_string = f"{staff_name} attempted to update {path}"
            
            log(log_string)
    except:
        pass
        
    return response # sends response to user





if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)