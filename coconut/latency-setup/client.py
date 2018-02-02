##########################################
# Client main file
# client.py
#
# version: 0.0.1
##########################################
# coconut
from lib import setup
from lib import elgamal_keygen
from lib import keygen, sign, aggregate_sign, aggregate_keys, randomize, verify
from lib import prepare_blind_sign, blind_sign, elgamal_dec, show_blind_sign, blind_verify
from lib import ttp_th_keygen, aggregate_th_sign
# petlib import-export
from utils import pack, unpack
# standard REST lib
from json  import loads, dumps
import requests
# async REST lib
import asyncio
import concurrent.futures
import requests
import grequests 
# timing & db
import time
from tinydb import TinyDB, Query


##########################################
# parameters
ATTRIBUTE = 10
N = 2
T = N

# crypto
params = setup()
(sk, _, vvk) = ttp_th_keygen(params, T, N)

# static fields
PUBLIC_SIGN_DB = 'public_sign.json'
PRIVATE_SIGN_DB = 'private_sign.json'
SERVER_ADDR = [
	"ec2-18-219-15-223.us-east-2.compute.amazonaws.com", 
	"ec2-18-216-197-109.us-east-2.compute.amazonaws.com"
]
SERVER_PORT = [80] * N
REPEAT = 1

ROUTE_SERVER_INFO = "/"
ROUTE_KEY_SET = "/key/set"
ROUTE_SIGN_PUBLIC = "/sign/public"
ROUTE_SIGN_PRIVATE = "/sign/private"

# timings
mem = []
tic = 0


##########################################
# utils
##########################################
# test server connection
def test_connection():
    for i in range(N):
        r = requests.get(
            "http://"+SERVER_ADDR[i]+":"+str(SERVER_PORT[i])+ROUTE_SERVER_INFO
        )
        assert loads(r.text)["status"] == "OK"

def get_time():
	return time.clock()

# make aync post requests
def async_request(route, json):
    unsent_request = [
        grequests.post(
            "http://"+SERVER_ADDR[i]+":"+str(SERVER_PORT[i])+route, 
            hooks={'response': response_handler}, 
            data=dumps(json)
        )
        for i in range(N)
    ]
    global tic
    tic = get_time()
    responses = grequests.map(unsent_request, size=N)
    for r in responses: assert loads(r.text)["status"] == "OK"

# response handler
def response_handler(response, *args, **kwargs):
    toc = get_time()
    record(toc-tic, loads(response.text))

# store data in mem
def record(time, data):
    mem.append({'time':time, 'request':data})

# stave mem to file
def save(filename):
    with open(filename, 'w') as file:
        file.write('[')
        for i in range(len(mem)): 
            mem[i]['time'] = mem[i]['time'] * 1000 # change to ms
            file.write(dumps(mem[i]))
            if i != len(mem)-1: file.write(',')
        file.write(']')


##########################################
# test server connection
##########################################
def set_key():
    for i in range(N):
        r = requests.post(
            "http://"+SERVER_ADDR[i]+":"+str(SERVER_PORT[i])+ROUTE_KEY_SET, 
            data = dumps({"sk": pack(sk[i])})
        )
        assert loads(r.text)["status"] == "OK"


##########################################
# request signature
##########################################
def request_sign():
    json = {"message":ATTRIBUTE}
    async_request(ROUTE_SIGN_PUBLIC, json)


##########################################
# request blind signature
##########################################
def request_blind_sign():
    (_, pub) = elgamal_keygen(params)
    (cm, c, proof_s) = prepare_blind_sign(params, ATTRIBUTE, pub)
    json = {
        "cm": pack(cm),
        "c": pack(c),
        "proof_s": pack(proof_s),
        "pub": pack(pub)
    }
    async_request(ROUTE_SIGN_PRIVATE, json)


##########################################
# main function
##########################################
def main():
    # test server connection
    test_connection()
    print('[OK] Test connection.')

    # attribute private key to each authority
    set_key()
    print('[OK] Key distribution.')

    # request signature on a public attribute
    print('[OK] Testing public attr. signature...')
    del mem[:]
    for _ in range(REPEAT): 
        request_sign()
        time.sleep(5)
    save(PUBLIC_SIGN_DB)
    print('[OK] Done.')

    # request signature on a private attribute
    print('[OK] Testing private attr. signature...')
    del mem[:]
    for _ in range(REPEAT): 
        request_blind_sign()
        time.sleep(5)
    save(PRIVATE_SIGN_DB)
    print('[OK] Done.')

    
##########################################
# program entry point
##########################################
if __name__ == "__main__": 
    main()


##########################################