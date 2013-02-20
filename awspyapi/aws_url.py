#! /usr/bin/env python

import hashlib
import hmac
import urllib
from urllib2 import urlopen
from urllib import quote
from hashlib import *
import time
import sys
import base64
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
import webbrowser
import os
import sys

class AwsUrlException(Exception):
    '''
        Exception type raised by AWS URL code 
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
    def __init__(self, method='GET', base_url = None, params={}, tag = None, key = None, secret = None ):
        if tag == None:
            raise(AwsUrlException("Associate tag is a required parameter"))
        else:
            self.tag = tag
        if key == None:
            raise(AwsUrlException("Associate Key ID is a required parameter"))
        else:
            self.key = key
        if secret == None:
            raise(AwsUrlException("Associate secret is a required parameter"))
        else:
            self.secret = secret
        if base_url == None:
            self.base_url = 'http://webservices.amazon.com/onca/xml'
        else:
            self.base_url = base_url

        self.method = method.upper()
        self.params = params

    def add_param( self, key, value ):
        '''
            Add another parameter ot the dictionary of
            URL parameters
        '''
        self.params[key] = value
        
    def signed_url(self):
        if self.method == None:
            self.method = 'GET'
        # Add Timestamp to parameters
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        # Really caller shouldn't but for testing against test vectors 
        # makes it easier
        if 'Timestamp' not in self.params:
            self.params['Timestamp'] = self.timestamp

        # Add Access Key to params
        if 'AWSAccessKeyId' not in self.params:
            self.params['AWSAccessKeyId'] = self.key
        else:
            self.key = self.params['AWSAccessKeyId']
        if 'AssociateTag' not in self.params:
            self.params['AssociateTag'] = self.tag
            
        if 'Version' not in self.params:
            self.params['Version'] = '2009-01-06'

        ''' For aws must create a string with parameters sorted and then
            connected by ampersands and of course must escape it all.
        '''
        # Convert dictionary of parameters into list of tuples for sorting
        paramset = [(quote(k),quote(v)) for k,v in self.params.iteritems()]
        paramset.sort() # mutable paramset will sort
        # Recombine into & separated list of parameters
        paramstring = '&'.join(['%s=%s' % (k, v) for k, v in paramset])
        #paramstring ="&".join("%s=%s" % (k, urllib.quote(unicode(kwargs[k]).encode('utf-8'), safe = '~')) for k in paramset) 
        # Now form signature
        msg = self.method + "\n" + 'webservices.amazon.com' + "\n" + \
            '/onca/xml' + "\n" + paramstring
        '''
        print '--------------------------------------------------------------------'
        print 'For signing:'
        print msg
        print '--------------------------------------------------------------------'
        '''
        m = hmac.new(key=self.secret, digestmod=hashlib.sha256)
        m.update(msg)
        digest = m.digest()
        # Base64 encode to string and then escape it for final signature
        signature = base64.encodestring(digest).strip()
        ####
        # I bet this will be a problem. Might escape things that
        # shouldn't be?  Only supposed to escape '=' and '+'
        signature = quote(signature)

        return self.base_url + '?' + paramstring + '&Signature=' + signature

if __name__ == '__main__':
    print 'Testing module aws_url'
    try:
        tag = os.environ['AWS_TAG']
    except:
        print('Missing environment variable for tag')
        sys.exit(0)

    try:
        key = os.environ['AWS_KEY']
        print 'AWS key = ' + key
    except:
        print('Missing environment variable for key')
        sys.exit(0)

    try:
        secret = os.environ['AWS_SECRET']
        print 'AWS secret = ' + secret
    except:
        print('Missing environment variable for secret')
        sys.exit(0)


    # Note: Had to add the timestamp from the examples since the current one obviously would not
    # result in the same signature
    test_vectors = [{'url':
        'http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&Operation=ItemLookup&ItemId=0679722769&ResponseGroup=ItemAttributes,Offers,Images,Reviews&Version=2009-01-06&Timestamp=2009-01-01T12:00:00Z',
        'expected': 'http://webservices.amazon.com/onca/xml?AWSAccessKeyId=AKIAIOSFODNN7EXAMPLE&ItemId=0679722769&Operation=ItemLookup&ResponseGroup=ItemAttributes%2COffers%2CImages%2CReviews&Service=AWSECommerceService&Timestamp=2009-01-01T12%3A00%3A00Z&Version=2009-01-06&Signature=M%2Fy0%2BEAFFGaUAp4bWv%2FWEuXYah99pVsxvqtAuC8YN7I%3D'},
        {'url': 'http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&Operation=ItemLookup&ItemId=0679722769&ResponseGroup=ItemAttributes,Offers,Images,Reviews&Version=2009-01-06', 
        'expected': 'http://webservices.amazon.com/onca/xml?ItemId=0679722769&Operation=ItemLookup&ResponseGroup=ItemAttributes%2COffers%2CImages%2CReviews&Service=AWSECommerceService&Timestamp=2009-01-01T12%3A00%3A00Z&Version=2009-01-06&Signature=M%2Fy0%2BEAFFGaUAp4bWv%2FWEuXYah99pVsxvqtAuC8YN7I%3D' }
        ]

    #for url,signed in test_vectors.iteritems():
    for v in test_vectors:
        #print 'url = ' + url
        #print 'signed = ' + signed
        uri_params = v['url'].split('?')
        uri_params = uri_params[1].split('&')
        params = { a.split('=')[0]:a.split('=')[1] for a in uri_params }
        #print 'params: ', params
        aws_url = AwsUrl( 'GET', params = params, tag = tag, key = key, secret = secret )

        url_signed = aws_url.signed_url()

        #print 'Expected:'
        #print v['expected']
        #print 'Got:'
        #print url_signed

    # Now try actually fecthing the url obtained from processing test vector [1]
    #webbrowser.open_new_tab( url_signed )
    f = urlopen( url_signed )
    dom = parse(f)
    f.close()
    f = open('aws.xml', 'w')
    dom.writexml( f, addindent="  ", newl = "\n" )
    f.close()

    med_image = dom.getElementsByTagName("SmallImage")
   
    for i in med_image:
        img_url = i.getElementsByTagName("URL")
        for u in img_url:
            print 'Tag name: ', u.tagName
            url = u.firstChild.data
            webbrowser.open_new_tab(url)


