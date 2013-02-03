#! /usr/bin/env python
from aws_url import AwsUrl
import os
import sys
import urllib
from urllib2 import urlopen
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
try:
    import webbrowser
except:
    pass

class AwsSearchException(Exception):
    '''
        Exception type raised by AWS search code 
    '''
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AwsSearch(object):
    '''
    Perform a search for an item via Amazon Product Advertising API.
    Here is the prototypical URL which is for a search for the
    book 'Do Androids Dream of Electric Sheep'.  Obviously the
    linefeeds are added only for readability and it is actually
    one long URL

        http://webservices.amazon.com/onca/xml?Service=AWSECommerceService&
            Operation=ItemSearch&SubscriptionId=AKIAITKN5MQYJBWBO57Q&AssociateTag=0100-7722-6784&
            Version=2011-08-01&
            SearchIndex=Books&Condition=All&
            Title=Do Androids Dream of Electric Sheep&
            ResponseGroup=Images,ItemAttributes

        The SearchIndex must be one of the following, which I decided is best determined by using
        the Product Advertising API Scratchpad at http://associates-amazon.s3.amazonaws.com/scratchpad/index.html
        and putting in a bogus SearchIndex such as FooBar.  Then you get

        The value you specified for SearchIndex is invalid. Valid values include [
            'All','Apparel','Appliances','ArtsAndCrafts','Automotive',
            'Baby','Beauty','Blended','Books','Classical','Collectibles',
            'DVD','DigitalMusic','Electronics','GiftCards','GourmetFood',
            'Grocery','HealthPersonalCare','HomeGarden','Industrial','Jewelry',
            'KindleStore','Kitchen','LawnAndGarden','Marketplace','MP3Downloads',
            'Magazines','Miscellaneous','Music','MusicTracks','MusicalInstruments',
            'MobileApps','OfficeProducts','OutdoorLiving','PCHardware','PetSupplies',
            'Photo','Shoes','Software','SportingGoods','Tools','Toys','UnboxVideo',
            'VHS','Video','VideoGames','Watches','Wireless','WirelessAccessories' ]

        In fact, the get_categories method below returns a tuple of all of the above. 

        Likewise, from putting a bogus parameter in the search request I found the current
        list of possible parameters which is

            Your request should have atleast 1 of the following parameters: 
            
            'Keywords','Title','Power','BrowseNode','Artist','Author','Actor','Director',
            'AudienceRating','Manufacturer','MusicLabel','Composer','Publisher',
            'Brand','Conductor','Orchestra','TextStream','Cuisine','City','Neighborhood'
            
    '''

# Immutable set of valid search indices 
    valid_search_indices = set([
            'All','Apparel','Appliances','ArtsAndCrafts','Automotive',
            'Baby','Beauty','Blended','Books','Classical','Collectibles',
            'DVD','DigitalMusic','Electronics','GiftCards','GourmetFood',
            'Grocery','HealthPersonalCare','HomeGarden','Industrial','Jewelry',
            'KindleStore','Kitchen','LawnAndGarden','Marketplace','MP3Downloads',
            'Magazines','Miscellaneous','Music','MusicTracks','MusicalInstruments',
            'MobileApps','OfficeProducts','OutdoorLiving','PCHardware','PetSupplies',
            'Photo','Shoes','Software','SportingGoods','Tools','Toys','UnboxVideo',
            'VHS','Video','VideoGames','Watches','Wireless','WirelessAccessories'])

    # Immutable list of valid search parameters
    valid_search_params = set([
            'Keywords','Title','Power','BrowseNode','Artist','Author','Actor','Director',
            'AudienceRating','Manufacturer','MusicLabel','Composer','Publisher',
            'Brand','Conductor','Orchestra','TextStream','Cuisine','City','Neighborhood'])

    def __init__(self, tag=None, key=None, secret=None, search_index ='Books', 
                    search_params = {'Title': 'To Kill a Mockinbird'}):
        '''
            Constructor for search including search_index and a model set of search parameters
            that is only intended to serve as an example but should return a valid result.

            If the AWS Tag isn't provided then an attempt is made to get it from the AWS_TAG
            environment variable which throws an exception if it fails.

            If the key isn't provided an attempt is made to get it from the AWS_KEY 
            environment variable which throws an exception if it fails.

            If the secret isn't provided and attempt is made to get it from the 
            AWS_SECRET environment variable which throws an exception if it fails

        '''                         
        if (tag == None):
            ''' Attempt to get tag from environment variable AWS_TAG '''
            try:
                self.tag = os.environ['AWS_TAG']
            except:
                raise AwsSearchException("Please set the AWS_TAG environment variable or provide it to the constructor")
        else:
            self.tag = tag

        if (key == None):
            ''' Attempt to get key from environment variable AWS_KEY '''
            try:
                self.key = os.environ['AWS_KEY']
            except:
                raise AwsSearchException("Please set the AWS_KEY environment variable or provide it to the constructor")
        else:
            self.key = key
                    

        if (secret == None):
            ''' Attempt to get secret from environment variable AWS_SECRET '''
            try:
                self.secret = os.environ['AWS_SECRET']
            except:
                raise AwsSearchException("Please set the AWS_SECRET environment variable or provide it to the constructor")
        else:
            self.secret = secret
        
        ''' Validate the search_index is in the set of valid ones '''            
        if not search_index in AwsSearch.valid_search_indices:
            raise AwsSearchException("Invalid search index.  See valid_search_indices set")
       
        ''' Likewise for all parameters '''
        for k,v in search_params.iteritems():
            if not k in AwsSearch.valid_search_params:
                raise AwsSearchException("Paramter %s is not a valid parameter" % k )

        self.search_index = search_index
        self.search_params = search_params
        ''' When a search is actuall performed this will be set to the resultant dom '''
        self.search_result_dom = None

    def do_search(self):
        '''
        Perform the search given the provided parameters.  The result is returned as
        a minidom object but it is probably more useful to use the other methods
        such as get_small_image, get_item_asin, get_detail_page_url, etc. than 
        to work with the raw dom result
        '''
         
        ''' Create and sign the URL.  For the AWS URL we must create the SearchIndex parameter '''
        self.search_params['SearchIndex'] = self.search_index
        ''' And the ResponseGroup 
            
            TODO: Should make parameter too but this could be default
        '''
        self.search_params['ResponseGroup'] ='Images,ItemAttributes'
        ''' And of course need the operation '''
        self.search_params['Operation'] = 'ItemSearch'

        aws_url = AwsUrl( 'GET', params = self.search_params, tag = self.tag, key = self.key, secret = self.secret )

        ''' Sign the URL '''
        url_signed = aws_url.signed_url()

        f = urlopen( url_signed )
        self.search_result_dom = parse(f)
        f.close()

        if self.search_result_dom.getElementsByTagName('Errors'):
            ''' TODO: Return list of all errors maybe as a dictionary like
             
                {'Code': 'Your request is missing the Service parameter. Please add  the Service parameter to your request and retry'}
            '''
            raise  AwsSearchException("An error occurred")
            
        return self.search_result_dom

    def _get_image_url(self, size='Medium'):
        ''' Internal worker for the other image URL methods.
            May return an empty string if URL not found for
            given image size which must be one of the valid
            sizes:

                Small
                Medium
                Large
        '''
        img_size = size+'Image'
        if self.search_result_dom == None:
            raise AwsSearchException("No search results available.  Did you search yet?")

        img = self.search_result_dom.getElementsByTagName(img_size)
        ''' TODO: Maybe should return some particular string instead of empty? '''
        url = '' 
        if img != None:
            for i in img:
                img_url = i.getElementsByTagName("URL")
                for u in img_url:
                    url = u.firstChild.data
                    break

        return url

    def get_small_image_url(self):
        return self._get_image_url('Small')

    def get_medium_image_url(self):
        return self._get_image_url('Medium')

    def get_large_image_url(self):
        return self._get_image_url('Large')

if __name__ == '__main__':
    '''
    Something to test with. You MUST have the AWS environment variables set
    '''
    if len(sys.argv) != 3:
        print ("Call as \n")
        print ("\taws_search SearchIndex Title\n")
        print ("\t\tFor example:\n")
        print ("\t\t\taws_search Books 'To Kill a Mockingbird'\n");
        sys.exit(0)

    print ("Search Index: %s" % sys.argv[1] )
    print ("Title: %s" % sys.argv[2] )

    s = AwsSearch( search_index = sys.argv[1], search_params = {'Title':sys.argv[2] } )

    try:
        dom = s.do_search()
    except e as AwsSearchException:
        print("The search failed: %s", str(e))
        sys.exit(-1)

    if dom == None:
        print ("The search failed\n");
    else:
        print ("The search succeeded.")

        ''' First try to get the medium image '''
        url = s.get_medium_image_url()
        print ("Medium image URL = %s" % url )
        ''' Try to open result in web browser or if not just pretty dump the dom '''
        try:
            webbrowser.open_new_tab(url)
            f = open('aws.xml', 'w')
            dom.writexml( f, addindent="  ", newl = "\n" )
            f.close()
        except:
            print ("No web browser available.  Saving result to file aws.xml")
            f = open('aws.xml', 'w')
            dom.writexml( f, addindent="  ", newl = "\n" )
            f.close()



