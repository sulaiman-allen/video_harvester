from os import getenv
#SELECTED_PARSER = 'nhk'

SELECTED_PARSER = getenv('SELECTED_PARSER')

if SELECTED_PARSER == 'tubi':
    from parsers.tubi.write_nfo import write_nfo

else:
    from parsers.nhk.write_nfo import write_nfo
