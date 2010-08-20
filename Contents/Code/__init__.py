import re, string, datetime

VIDEO_PREFIX      = "/video/imovies"
BASE_URL = "http://imovies.blogspot.com"
LABEL_URL = "http://imovies.blogspot.com/search/label/%s"
FULL_LABEL_URL = "http://imovies.blogspot.com/search?label=%s&max-results=1000"
RSS_URL = "http://feeds.feedburner.com/FreePublicDomainMovies?format=xml"
CACHE_INTERVAL    = 1800
ICON = "icon-default.png"

####################################################################################################
def Start():
  Plugin.AddPrefixHandler(VIDEO_PREFIX, MainMenuVideo, "iMovies", ICON, "art-default.png")
  Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
  MediaContainer.art = R('art-default.png')
  MediaContainer.title1 = 'iMovies'
  HTTP.SetCacheTime(CACHE_INTERVAL)
  
def MainMenuVideo():
    dir = MediaContainer(mediaType='video')  
    dir.Append(Function(DirectoryItem(RecentAdditions, "Recent Additions", thumb=R(ICON))))
    for item in HTML.ElementFromURL(BASE_URL, errors='ignore').xpath('//div/span/a'):
        if(item.text):
            title = item.text.strip()
            url = FULL_LABEL_URL % title
            dir.Append(Function(DirectoryItem(Category, title=title, thumb=R(ICON)), url=url))
    return dir
    
#############################
def RecentAdditions(sender):
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle) 
    feed = RSS.FeedFromURL(RSS_URL)
    for entry in feed['items']: 
        title = entry.title
        updated = Datetime.ParseDate(entry.updated).strftime('%a %b %d, %Y')
        summary = entry.summary
        summaryText = HTML.ElementFromString(summary).xpath('descendant::text()')[0].strip()
        thumb = HTML.ElementFromString(summary).xpath('descendant::img')[0].get('src')
        Log(thumb)
        link = ""
        for item in entry.links:
            if item.has_key('title') and item.title == 'AVI':
                link = item['href']
        if(len(link) > 0):
            dir.Append(VideoItem(link, title=title, summary=summaryText, thumb=thumb, subtitle=updated))
    return dir
    
###################################
def Category(sender, url):
    
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle) 
    
    groupMap = ConstructGroupMap(url)
    groups = groupMap.keys()[:]
    groups.sort()
    for group in groups:
        groupItems = groupMap[group]
        if len(groupItems) > 1:
            dir.Append(Function(DirectoryItem(Group, title=group, thumb=R(ICON)), items=groupItems))
        else:
            groupItem = groupItems[0]
            title = group
            if group != groupItem[0]:
               title = group + " - " + groupItem[0]
            dir.Append(VideoItem(groupItem[4], title=title, subtitle=groupItem[1], summary=groupItem[2], thumb=groupItem[3]))
    return dir 

###############################
# Extracts grouped items with two assumptions:
#    Group Name - Episode Name
#    Group Name ep Episode Name
# 
def ConstructGroupMap(url):
    groupMap = dict()
    for item in HTML.ElementFromURL(url, errors='ignore').xpath('//div[@class="blogPost"]'):
       titleElement = item.xpath('preceding-sibling::h2')[-1]
       title = ""
       if len(titleElement.xpath('a')) > 0:
           title = titleElement.xpath('a')[0].text.strip()
       else:
           title = titleElement.text.strip()
           
       added = "Added "+Datetime.ParseDate(item.xpath('preceding-sibling::h3')[-1].text.strip()).strftime('%a %b %d, %Y')
       thumb = None
       if len(item.xpath("img")) > 0:
          thumb = item.xpath("img")[0].get('src')
       summary = str(item.xpath("descendant::text()")[1])
       videoUrl = ExtractVideoUrl(item)
       
       if(len(videoUrl) > 0):
           key = title
           entryTitle = title
           titleTokens = title.split(" - ")
           altTitleTokens = title.split(" ep ")
           if len(titleTokens) > 1:
               key = titleTokens[0].strip()
               entryTitle = titleTokens[-1].strip()
           elif len(altTitleTokens) > 1:
               key = altTitleTokens[0].strip()
               entryTitle = altTitleTokens[-1].strip()
               
           entryGroup = groupMap.get(key)
           if not entryGroup:
              entryGroup = []
              groupMap[key] = entryGroup
           entryGroup.append((entryTitle, added, summary, thumb, videoUrl))
    return groupMap

######################################
def Group(sender, items):
    
    dir = MediaContainer(viewGroup='Details', title2=sender.itemTitle) 
    for item in items:
        dir.Append(VideoItem(item[4], title=item[0], subtitle=item[1], summary=item[2], thumb=item[3]))
    return dir

################################################
def ExtractVideoUrl(item):
    potentials = item.xpath('descendant::a')
    allowable = ['MP4', 'AVI', 'FLV', 'MPG', 'OGV', 'WMV']
    for ext in allowable:
        for potential in potentials:
            if(ext == potential.text):
                videoUrl = potential.get('href')
                # tinyurl links all seem broken
                if videoUrl.find('tinyurl') < 0:
                    return videoUrl
    return ""

                 