#! /usr/bin/env python

import hashlib
import hmac
import urllib2
from hashlib import *
from urllib2 import *
from urllib import quote_plus
import time
import sys
import base64

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
            self.base_url = 'http://webservices.amazon.com/onca/xml'
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
        # Add Timestamp to parameters
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Really caller shouldn't but...
        if 'Timestamp' not in self.params:
            self.params['Timestamp'] = self.timestamp

        # Add Access Key to params
        if 'AWSAccessKeyId' not in self.params:
            self.params['AWSAccessKeyId'] = self.key
        else:
            self.key = self.params['AWSAccessKeyId']
        if 'Version' not in self.params:
            self.params['Version'] = '2009-01-06'

        ''' For aws must create a string with parameters sorted and then
            connected by ampersands and of course must escape it all.
        '''
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
        msg = self.method + '\x0a' + 'webservices.amazon.com' + '\x0a' + \
            '/onca/xml' + '\x0a' + paramstring
        print '--------------------------------------------------------------------'
        print 'For signing:'
        print msg
        print '--------------------------------------------------------------------'
        m = hmac.new(key=self.key, msg=msg, digestmod=hashlib.sha256)
        digest = m.digest()
        # Base64 encode to string and then escape it for final signature
        signature = base64.encodestring(digest).strip()
        ####
        # I bet this will be a problem. Might escape things that
        # shouldn't be?  Only supposed to escape '=' and '+'
        signature = quote_plus(signature)

        return self.base_url + '?' + paramstring + '&Signature=' + signature



if __name__ == '__main__':
    print 'Testing module aws_url'

    key = raw_input('Enter ID: ')
    secret = raw_input('Enter secret: ')

    # Note: Had to add the timestamp from the examples since the current one obviously would not
    # result in the same signature
    test_vectors = {
        'http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&Operation=ItemLookup&ItemId=0679722769&ResponseGroup=ItemAttributes,Offers,Images,Reviews&Version=2009-01-06&Timestamp=2009-01-01T12:00:00Z':
        'http://webservices.amazon.com/onca/xml?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&ItemId=0679722769&Operation=ItemLookup&ResponseGroup=ItemAttributes%2COffers%2CImages%2CReviews&Service=AWSECommerceService&Timestamp=2009-01-01T12%3A00%3A00Z&Version=2009-01-06&Signature=M%2Fy0%2BEAFFGaUAp4bWv%2FWEuXYah99pVsxvqtAuC8YN7I%3D',

        'http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&Operation=ItemLookup&ItemId=0679722769&ResponseGroup=ItemAttributes,Offers,Images,Reviews&Version=2009-01-06':
        'http://webservices.amazon.com/onca/xml?ItemId=0679722769&Operation=ItemLookup&ResponseGroup=ItemAttributes%2COffers%2CImages%2CReviews&Service=AWSECommerceService&Timestamp=2009-01-01T12%3A00%3A00Z&Version=2009-01-06&Signature=M%2Fy0%2BEAFFGaUAp4bWv%2FWEuXYah99pVsxvqtAuC8YN7I%3D'
        }

    secret = '1234567890' 

    for url,signed in test_vectors.iteritems():
        #print 'url = ' + url
        #print 'signed = ' + signed
        uri_params = url.split('?')
        uri_params = uri_params[1].split('&')
        params = { a.split('=')[0]:a.split('=')[1] for a in uri_params }
        #print 'params: ', params
        aws_url = AwsUrl( 'GET', params = params, key = key, secret = secret )

        url_signed = aws_url.signed_url()

        print 'Expected:'
        print signed
        print 'Got:'
        print url_signed



