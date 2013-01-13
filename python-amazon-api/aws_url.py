#! /usr/bin/env python

from import hashlib import *
from urllib2 import *

class AwsUrlException(Exception):
    '''
        Exceptions raised by AWS URL code 
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def class AwsUrl(object):
    __init__(self, method='GET', base_url = None, params={}, key = None, secret = None ):
        if base_url == None:
            raise AwsUrlException('Base URL required')
        self.method = method
        self.params = params
        self.key = key
        self.secret = secret
        self.url = url

    def add_param( self, key, value ):
       self 

    def build_uri(self):
        pass

    def finalize_uri(self):
        pass

    def sign_uri(self):
        pass

    def add_param():
        pass


        
