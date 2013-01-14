#! /usr/bin/env python

import hashlib
import urllib2
from hashlib import *
from urllib2 import *
import time
import sys

class AwsUrlException(Exception):
    '''
        Exceptions raised by AWS URL code 
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AwsUrl(object):
    '''
        Construct a URL object.  After initial construction 
        the steps to follow are to add any additional parameters
        using add_param, finalize the URL using finalize,
        and sign using sign
    '''
    def __init__(self, method='GET', base_url = None, params={}, key = None, secret = None ):
        if base_url == None:
            self.base_url = 'http://webservices.amazon.com/onca/xml/'
        else:
            self.base_url = base_url
        self.method = method.upper()
        self.params = params
        self.key = key
        self.secret = secret

    def add_param( self, key, value ):
        '''
            Add another parameter ot the dictionary of
            URL parameters
        '''
        self.params[key] = value
        
    def signed_url(self):
        if self.method == None:
            self.method = 'GET'
        self.method = self.method.upper()
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        ''' For aws must create a string with paramters sorted and then
            connected by ampersands and of course must escape it all
        '''
        # Add Access Key to params
        self.params['AWSAccessKeyId'] = self.key
        # Convert dictionary of parameters into list of tuples for sorting
        params = [(k,v) for k,v in self.params.iteritems()]
        params.sort() # mutable will sort
        # Recombine into & separated list of parameters
        paramstring = ''
        for i in params:
            paramstring += '='.join(i)
            if i != params[-1]:
                paramstring += '&'
        # Now must quote (escape) params string, treating '=' as
        # reserved since otherwise quote() will quote it as well
        paramstring = urllib2.quote(paramstring, '=&')
        # Now form signature
        signature = self.method + '\n' + 'webservices.amazon.com' + '\n' + \
            '/onca/xml/' + '\n' + paramstring
        print 'For signing: ' + signature
        return self.base_url + paramstring



if __name__ == '__main__':
    print 'Enter URL and parameters and empty to terminate'
    params = {}
    while(True):
        try:
            param = raw_input('Enter parameter key: ')
            value = raw_input('Enter parameter value: ')
        except:
            break;
    try:
        key = raw_input('Enter Amazon key: ')
    except:
        sys.exit(0)

    try:
        secret = raw_input('Enter Amazon secret: ')
    except:
        sys.exit(0)

    aws_url = AwsUrl( 'GET', params, key = key, secret = secret )

    url = aws_url.signed_uri()


