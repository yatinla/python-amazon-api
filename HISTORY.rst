.. :changelog:

History
-------

0.4.1 (2013-02-21)
+++++++++++++++++++

- The AwsSearch construction would overwrite the callers
  search parameters with the list of all possible ones

- Remove accidental second version of get_item_bindings

- get_items_by_attributes really didn't work correctly at
  all.  Now it only returns the items that have Attributes
  with values that match all of those in the input dictionary.
  It is permissable for an item to havem multiple attributes
  with the same tag such as Actor and not all of them have
  to match but at least one has to match the desired value.
  This seems like the sensible thing for movie searches
  since they do have multiple Actor tags in the Attributes.
  

0.4.0 (2013-02-19)
+++++++++++++++++++

- Adding new functionality to return attributes
  like Author, RunningTime, and such.

  Removed more debugging prints

0.3.1 (2013-02-03)
+++++++++++++++++++

- Remove debugging prints

0.3.0 (2013-02-03)
+++++++++++++++++++

- Superbowl Sunday!! Signifant refactoring not
  necessarily backward compatible.  Add the ability
  to search for items by attributes and get all available
  bindings and specify a particular item when looking for
  the image URL or the DetailsPageURL.

0.2.1 (2013-02-02)
+++++++++++++++++++

- If run as main it now creates a simple HTML page to open
  in a browser with the medium image for the search result and
  it is clickable and goes to the main product page for the result

0.1.1 (2013-02-02)
+++++++++++++++++++

- Add aws_search.py with the AwsSearch class and also rename
  the module to awspyapi

0.1.0 (2012-12-20)
+++++++++++++++++++

- Initial version
