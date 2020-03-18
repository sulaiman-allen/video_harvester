from string import Template
nfo_string = Template(\
'''
<episodedetails>
  <title>$title</title>
  <season>$season</season>
  <episode>$episode</episode>
  <aired>$date</aired>
  <plot>$plot</plot>
</episodedetails>
'''
)

