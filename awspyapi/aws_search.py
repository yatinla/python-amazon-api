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
            'VHS','Video','VideoGames','Watches','Wireless','WirelessAccessories','movies-tv'])

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
        self.search_params = dict.copy(search_params)
        ''' When a search is actuall performed this will be set to the resultant dom '''
        self.search_result_dom = None


    def _get_attribute_value(self, item, attr):
        ''' Internal worker for the other methods that retrieve
            attributes such as Author etc.  Returns a set of
            values matching the given attribute since some
            cases such as Actor there are multiple values for
            the same key
        '''
        if attr == None:
            raise AwsSearchException("You must supply an attribute name such as 'Author'")
        if item == None:
            if self.search_result_dom == None:
                raise AwsSearchException("No search results available.  Did you search yet?")
            attributes = self.search_result_dom.getElementsByTagName('ItemAttributes')
        else:
            attributes = item.getElementsByTagName('ItemAttributes')

        ''' TODO: Maybe should return some particular string instead of empty? '''
        values = []
        if attributes != None:
            for a in attributes:
                e = a.getElementsByTagName(attr)
                for v in e:
                    values.append(v.firstChild.data)
        return values

    ''' The following are likely most relevant to books. '''
    def get_authors(self, item = None):
        ''' Get Authors 

            NOTE: returns a list in case there's more than one
        '''
        return self._get_attribute_value(item, 'Author')

    def get_pub_date(self, item = None):
        ''' Get publication date.  Really ought to be only one right?
            Only going to return one
        '''
        values = self._get_attribute_value(item, 'PublicationDate')
        if len(values) > 0:
            return values[0]
        else:
            return None

    def get_num_pages(self, item = None):
        ''' Get number of pages '''
        values = self._get_attribute_value(item, 'NumberOfPages')
        if len(values) > 0:
            return values[0]
        else:
            return None

    ''' And these are more for movies '''
    def get_actors(self, item=None):
        ''' Return a list of actors.  This one is
            definitely multi-valued
        '''
        return self._get_attribute_value( item, 'Actor')

    def get_mpaa_rating(self, item=None):
        ''' Get the movie rating, i.e., PG-13 etc. ''' 
        values = self._get_attribute_value( item, 'AudienceRating')
        if len(values) > 0:
            return values[0]
        else:
            return None

    def get_directors(self, item=None):
        ''' Get the list of directors.  Probably only one but... '''
        return self._get_attribute_value( item, 'Director')

    def get_product_group(self, item=None):
        ''' Like Movie or whatever.  Assume only one '''
        values = self._get_attribute_value( item, 'ProductGroup')
        if len(values) > 0:
            return values[0]
        else:
            return None


    def get_running_time(self, item=None):
        ''' Running time of movie in minutes is what I will ASSume
            for now since I've not seen otherwise but Amazon
            allows for the possibility of other units.
        <RunningTime Units="minutes">104</RunningTime>
        '''
        values = self._get_attribute_value( item, 'RunningTime')
        if len(values) > 0:
            return values[0]
        else:
            return None

    def get_release_date(self, item=None):
        ''' Release date of movie '''
        values = self._get_attribute_value( item, 'ReleaseDate')
        if len(values) > 0:
            return values[0]
        else:
            return None

    ''' These could be book or movie '''
    def get_binding(self, item=None):
        ''' Like Amazon Instant Video or Blu-ray or Paperback.  Assume only one '''
        values = self._get_attribute_value( item, 'Binding')
        if len(values) > 0:
            return values[0]
        else:
            return None

    def get_genres(self, item=None):
        ''' Like Science Fiction etc.  Maybe more than one sometimes? '''
        return self._get_attribute_value( item, 'Genre')
        if len(values) > 0:
            return values[0]
        else:
            return None

    ''' Here are others but I'm not going to worry about them now 
        <Languages>
          <Language>
            <Name>English</Name>
            <Type>Subtitled</Type>
          </Language>
        </Languages>
        <ProductTypeName>DOWNLOADABLE_MOVIE</ProductTypeName>
        <Studio>Warner Bros.</Studio>
        <Title>I Am Legend</Title>
    '''

    def get_small_image_url(self, item=None):
        return self._get_image_url('Small',item)

    def get_medium_image_url(self, item=None):
        return self._get_image_url('Medium',item)

    def get_large_image_url(self,item=None):
        return self._get_image_url('Large',item)

    def get_detail_page_url(self, item=None):
        '''
        This is the URL for the main product page.  If item==None
        it just finds the DetailPageURL for the first item found.
        Otherwise, it returns the one for the given item
        '''
        detail_page_url_node = None 

        if item == None: 
            if self.search_result_dom == None:
                raise AwsSearchException("No search results available.  Did you search yet?")
      
            ''' Return DetailPageUrl for the first item found '''
            items = self.search_result_dom.getElementsByTagName('Item')
            for item in items:
                detail_page_url_node = self.search_result_dom.getElementsByTagName('DetailPageURL')
                break
        else:
            detail_page_url_node = item.getElementsByTagName('DetailPageURL')
           
        url = None 
        if detail_page_url_node != None:
            for u in detail_page_url_node:
                url = u.firstChild.data
                break
        return url 

    def get_item_bindings(self, items=None):
    
        '''
        Return a set of strings for the available bindings in the list of items
        or the empty list if no bindings found.  Note that this is for all
        possible bindings in all items returned by the search
        '''
        if items == None:
            if self.search_result_dom == None:
                raise AwsSearchException("No search results available.  Did you search yet?")

        binding_set = set([])
        if items == None:
            bindings = self.search_result_dom.getElementsByTagName('Binding')
            for b in bindings:
                binding_set.add(b.firstChild.nodeValue)
        else:
            for i in items:
                bindings = i.getElementsByTagName('Binding')
                for b in bindings:
                    binding_set.add(b.firstChild.nodeValue)

        return binding_set

    def do_search(self):
        '''
        Perform the search given the provided parameters.  The result is returned as
        a minidom object but it is probably more useful to use the other methods
        such as get_small_image, get_item_asin, get_detail_page_url, etc. than 
        to work with the raw dom result.

            NOTE:   The search might "succeed" in the sense that it returns some XML
                    but that doesn't mean it was truly successful.  One should always
                    call get_errors() to see if there were any errors 
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
           
        ''' NOTE:  There might be an error in the search.  The caller
            should check with get_errors
        ''' 
        return self.search_result_dom

    def get_errors(self):
        ''' 
        This method should *always* be called if do_search does not
        return None as the result.  The XML DOM returned by do_search
        could still contain errors reported from the Amazon web services.

        Returns a list of strings each with an error code or None
        if no errors are found.  
            
        Typically there's only one like for example 

            'AWS.ECommerceService.NoExactMatches'
        '''
        errors = self.search_result_dom.getElementsByTagName('Errors')
        err_list = []
        if errors != None:
            for err in errors:
                code = err.getElementsByTagName("Code")
                for c in code:
                    err_list.append(c.firstChild.data)
                    break
        if len(err_list) == 0:
            return None
        else:
            return err_list

    def _get_image_url(self, size='Medium', item=None):
        ''' Internal worker for the other image URL methods.
            May return an empty string if URL not found for
            given image size which must be one of the valid
            sizes:

                Small
                Medium
                Large
        '''
        img_size = size+'Image'

        if item == None:
            if self.search_result_dom == None:
                raise AwsSearchException("No search results available.  Did you search yet?")
            img = self.search_result_dom.getElementsByTagName(img_size)
        else:
            img = item.getElementsByTagName(img_size)

        ''' TODO: Maybe should return some particular string instead of empty? '''
        url = None
        if img != None:
            for i in img:
                img_url = i.getElementsByTagName("URL")
                for u in img_url:
                    url = u.firstChild.data
                    break
                break

        return url

    def get_small_image_url(self, item=None):
        return self._get_image_url('Small',item)

    def get_medium_image_url(self, item=None):
        return self._get_image_url('Medium',item)

    def get_large_image_url(self,item=None):
        return self._get_image_url('Large',item)


    def get_detail_page_url(self, item=None):
        '''
        This is the URL for the main product page.  If item==None
        it just finds the DetailPageURL for the first item found.
        Otherwise, it returns the one for the given item
        '''
        detail_page_url_node = None 

        if item == None: 
            if self.search_result_dom == None:
                raise AwsSearchException("No search results available.  Did you search yet?")
      
            ''' Return DetailPageUrl for the first item found '''
            items = self.search_result_dom.getElementsByTagName('Item')
            for item in items:
                detail_page_url_node = self.search_result_dom.getElementsByTagName('DetailPageURL')
                break
        else:
            detail_page_url_node = item.getElementsByTagName('DetailPageURL')
           
        url = None 
        if detail_page_url_node != None:
            for u in detail_page_url_node:
                url = u.firstChild.data
                break
        return url 

    def get_items_by_attributes(self, attributes=None, loose=True):
        ''' 
        Given a completed search, look for the Item in the list of Items
        that has attributes matching those in the input dictionary.  
        Examples of attributes for a Movie:

            <Actor>Harrison Ford</Actor>
            <Actor>Rutger Hauer</Actor>
            <Actor>Sean Young</Actor>
            <Actor>Edward James Olmos</Actor>
            <AudienceRating>R (Restricted)</AudienceRating>
            <Binding>Amazon Instant Video</Binding>
            <Creator Role="Producer">Michael Deeley</Creator>
            <Creator Role="Writer">Hampton Fancher</Creator>
            <Creator Role="Writer">David Peoples</Creator>
            <Director>Ridley Scott</Director>
            <Genre>Science Fiction</Genre>
            <ProductGroup>Movie</ProductGroup>
            <ProductTypeName>DOWNLOADABLE_MOVIE</ProductTypeName>
            <ReleaseDate>2008-01-17</ReleaseDate>
            <RunningTime Units="minutes">118</RunningTime>
            <Studio>Warner Bros.</Studio>
            <Title>Blade Runner: The Final Cut</Title>


        So one could pass in the dictionary 
        
            attributes = {'Genre':'Science Fiction', 'Binding':'Amazon Instant Video'} 

        and it should return a list of one or more matching items.

        If the list of attributes is empty it just returns all items

        If loose is True then it matches so long as the desired attribute
        value is in the tag value, for example with loose=True then a search
        for Title = Blade Runner would match
            
                     Blade Runner Collector's Edition
                     
        whereas with loose = False that would not be a match.  Generally a 
        bad idea for movies since Amazon has a bazillion copies of some
        of them in all different bindings (DVD, Blu-ray, etc.) but if you
        insist on an exact match to the title then you might find only one
        if any.

        Return: List of matching DOM elements of type Item or empty list

        '''

        if self.search_result_dom == None:
            raise AwsSearchException("No search results available.  Did you search yet?")

        items = self.search_result_dom.getElementsByTagName('Item')

        matches = []

        for item in items:
            if attributes == None:
                ''' Just return all items '''
                matches.append(item)
            else:
                attribs = item.getElementsByTagName("ItemAttributes")
                count = 0
                for k,v in attributes.iteritems():
                    for a in attribs:
                        ''' If there is more than one attribute by the
                            same name, such as Actor, then so long
                            as one of them matches we're OK
                        '''
                        attr = a.getElementsByTagName(k)
                        for m in attr:
                            if m.tagName == k:
                                if loose:
                                    if v in m.firstChild.nodeValue:
                                        count += 1
                                else:
                                    if v == m.firstChild.nodeValue:
                                        count += 1
                    
                if count == len(attributes):
                    ''' All the desired attributes match this item '''
                    matches.append(item)

        return matches

        '''
        This is an example for how to walk the dom


        root = dom.documentElement

        for c in root.childNodes:
            if c.nodeType != c.TEXT_NODE:
                print c.tagName
                if c.tagName == "Items":
                    for item in c.childNodes:
                        if item.nodeType != item.TEXT_NODE:
                            print "\t" + item.tagName
                            attribs = item.getElementsByTagName("ItemAttributes")
                            for a in attribs:
                                if a.nodeType != item.TEXT_NODE:
                                    bindings = a.getElementsByTagName("Binding")
                                    for b in bindings:
                                        print b
                                        print b.firstChild.nodeValue
        '''

if __name__ == '__main__':
    '''
    Something to test with. You MUST have the AWS environment variables set
    '''
    if len(sys.argv) < 3:
        print ("Call as \n")
        print ("\taws_search SearchIndex Title [Author|Director]\n")
        print ("\t\tFor example:\n")
        print ("\t\t\taws_search Video 'The Thing', 'John Carpenter' \n");
        print ("Seems like Director might work best for movies and don't need author for books as much")
        sys.exit(0)

    print ("Search Index: %s" % sys.argv[1] )
    print ("Title: %s" % sys.argv[2] )

   
    srch_params = {'Title': sys.argv[2]} 
    if len(sys.argv) > 3:
        if 'Books' == sys.argv[1]:
            srch_params['Author'] = sys.argv[3]
        elif 'Video' == sys.argv[1]:
            srch_params['Director'] = sys.argv[3]
        else:
            pass

    print "srch_params before: ", srch_params
    s = AwsSearch( search_index = sys.argv[1], search_params=srch_params )
    print "srch_params after AwsSearch: ", srch_params

    dom = s.do_search()

    print "srch_params after do_search: ", srch_params

    if dom == None:
        print ("The search did not return a DOM!\n");
        sys.exit(-1)
    else:
        errs = s.get_errors()
        if errs != None:
            print("The search returned errors:")
            for i in errs:
                print 'Error code: ', i
            sys.exit(-1)
        else:
            print ("The search returned with no errors.")

        ''' First find exact match '''

        print "Look for exact match for ", srch_params
        items = s.get_items_by_attributes(srch_params)
        if items == None:
            print "Did not find any exact match for desired parameters"
            sys.exit(0)

        try:
            ''' First try without items '''
            print "Try without items to get bindings:"
            bindings = s.get_item_bindings()
            print "without items bindings: ", bindings
        except:
            print "get_item_bindings is broke without items param"

        ''' Get list of possible bindings with loose match '''
        bindings = s.get_item_bindings(items)
        print "Available bindings:"
        for b in bindings:
            print "\t",b

        for tries in range(0,5): 
            binding = raw_input('Enter binding type: ')

            ''' Find item with that binding type '''
            items = s.get_items_by_attributes({'Binding':binding})
            if len(items) == 0:
                print ("No items with that binding")
            else:
                break

        if items == None or len(items) == 0:
            print ("Didn't find items")
            sys.exit(-1) 

        ''' First try to get the medium image '''
        med_img_url = s.get_medium_image_url(items[0])
        if med_img_url != None:
            print ("Medium image URL = %s" % med_img_url )

        small_img_url = s.get_small_image_url(items[0])
        if small_img_url != None:
            print ("Small image URL = %s" % small_img_url )

        ''' Next try to get the main page for the item '''
        main_url = s.get_detail_page_url(items[0])
        if main_url != None:
            print ("Detail Page URL = %s" % main_url )


        product_group = s.get_product_group(items[0])
        if product_group != None:
            if product_group == 'Book':
                print "It is a Book"
                print "Here are some other attributes: "
                authors = s.get_authors(items[0])
                if authors != None:
                    print "Here are the authors:"
                    for a in authors:
                        print a
                pub_date = s.get_pub_date(items[0])
                if pub_date != None:
                    print "Published " + pub_date

            elif product_group == 'Movie' or product_group == 'DVD' or product_group == 'Blu-ray':
                print "It is a movie"
                print "Here are some other attributes: "
                run_time = s.get_running_time(items[0])
                if run_time != None:
                    print "Running time is " + run_time + " minutes"
                directors = s.get_directors(items[0])
                if directors != None:
                    print "Director(s):"
                    for d in directors:
                        print d
                rating = s.get_mpaa_rating(items[0])
                if rating != None:
                    print "The MPAA has rated this movie " + rating
            else:
                print "Product group is not recognized: " + product_group

        if main_url != None and med_img_url != None:
            ''' Make a simple web page, save it, and open it '''
            html = '<!DOCTYPE HTML><head><title>Click me!</title></head><html>'
            html += '<body><h1>Here is the search result</h1>'
            html += '<a href="'+main_url+'"><img src="'+med_img_url+'"></a></body></html>'

            f = open('aws.xml', 'w')
            dom.writexml( f, addindent="  ", newl = "\n" )
            f.close()
            print("Search results saved to aws.xml")
            f = open('index.html', 'w')
            f.write(html)
            f.close()
            print("A small web page with image and link to item saved to index.html")

            ''' Try to open result in web browser or if not just pretty dump the dom '''
            try:
                webbrowser.open_new_tab('index.html')
            except:
                print ("No web browser available.")
        else:
            print ("One or both of the image URL and the main URL were not found!")


