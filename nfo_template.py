from os import getenv

SELECTED_PARSER = getenv('SELECTED_PARSER')

if SELECTED_PARSER == 'tubi':
    from parsers.tubi.nfo_template import nfo_string 

elif SELECTED_PARSER == 'nhk':
   from parsers.nhk.nfo_template import nfo_string 

else:
    print("Selected parser not found")
    exit()
