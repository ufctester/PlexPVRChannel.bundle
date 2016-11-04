#
# MOST IMPORTANT NOTE: BEFORE WRITING A CHANNEL, THERE MUST ALREADY BE A URL SERVICE FOR THE VIDEOS ON THE WEBSITE
# YOU WANT TO CREATE A CHANNEL FOR OR YOU WILL HAVE TO WRITE A URL SERVICE BEFORE YOU CAN WRITE THE CHANNEL. TO
# SEE IF A URL SERVICE ALREADY EXISTS, CHECK THE SERVICES BUNDLE IN THE PLEX PLUGIN FOLDER

# IMPORTANT NOTE: PYTHON IS VERY SENSITIVE TO PROPER INDENTIONS.  IF YOUR CHANNEL HAS IMPROPER INDENTIONS IT WILL
# NOT BE RECOGNIZED BY PLEX. I RUN THE PROGRAM THROUGH A CHECK MODULE ON A LOCAL VERSION OF PYTHON I HAVE LOADED
# PRIOR TO ACCESSING IT THROUGH PLEX TO MAKE SURE THERE ARE NO INDENTION ERRORS.

# You will need to decide how you want to set up your channel. If you want to have just one page that list all 
# the videos or if you want to break these videos down into subsections for different types of videos, individual shows, season, etc
# It is easiest to determine this system based on the structure of the website you are accessing. 

# You can hard code these choice in or pull the data from a web page or JSON data file and put it in a for loop to 
# automate the process. I created a basic example in the form of functions below to show the most common methods of 
# parsing data from different types of websites. When you want to produce results to the screen and have subpage come up # when they click on those results, you usually will use a
# DirectoryObject and include the name of the next function that will create that subpage called in the key.
# The key callback section sends your data to the next function that you will use to produce your next subpage.  Usually
# you will pass the value of the url onto your next function, but there are many attributes that can be sent.  It is good 
# to pass the title as well so it shows up at the top of the screen. Refer to the Framework Documentation to see the full
# list

# You will need a good working knowledge of xpath the parse the data properly.  Good sources for information related to 
# xpath are:
# 'http://devblog.plexapp.com/2012/11/14/xpath-for-channels-the-good-the-bad-and-the-fugly/'
# 'http://forums.plexapp.com/index.php/topic/49086-xpath-coding/'

# Here is a good article about working with Chrome Development Tools: 
# 'http://devblog.plexapp.com/2012/09/27/using-chromes-built-in-debugger-for-channel-development/'

# And here are a few pages that give you some pointers ON figuring out the basics of creating a channel
# 'http://devblog.plexapp.com/2011/11/16/a-beginners-guide-to-v2-1/'
# 'http://forums.plexapp.com/index.php/topic/28084-plex-plugin-development-walkthrough/'

# The title of your channel should be unique and as explanatory as possible.  The preifx is used for the channel
# store and shows you where the channel is executed in the log files
#
# __init__.py by Dave Spriet <davespriet@gmail.com>
# 
# Change History
#    v1.0.0 Initial Release
#

from Keyboard import Keyboard, DUMB_KEYBOARD_CLIENTS, MESSAGE_OVERLAY_CLIENTS
from DumbTools import DumbKeyboard, MESSAGE_OVERLAY_CLIENTS

import re

TITLE = 'Plex Request Channel'
PREFIX = '/video/plexpvr'

# The images below are the default graphic for your channel and should be saved or located in you Resources folder
# The art and icon should be a certain size for channel submission. The graphics should be good quality and not be blurry
# or pixelated. Icons must be 512x512 PNG files and be named, icon-default.png. The art must be 1280x720 JPG files and be
# named, art-default.jpg. The art shows up in the background of the PMC Client, so you want to make sure image you choose 
# is not too busy or distracting.  I tested out a few in PMC to figure out which one looked best.

ART = 'art-default.jpg'
ICON = 'plexpvr.png'

from Session import VERSION

CHANGELOG_URL = "https://raw.githubusercontent.com/ufctester/PlexPVRChannel.bundle/master/CHANGELOG"

### URL Constants for TheMovieDataBase ############################################################
TMDB_API_KEY = "096c49df1d0974ee573f0295acb9e3ce"
TMDB_API_URL = "http://api.themoviedb.org/3/"
TMDB_IMAGE_BASE_URL = "http://image.tmdb.org/t/p/"
POSTER_SIZE = "w500/"
BACKDROP_SIZE = "original/"
###################################################################################################

### URL Constants for OpenMovieDataBase 
OMDB_API_URL = "http://www.omdbapi.com/"
###################################################################################################

### URL Constants for TheTVDB 
TVDB_API_KEY = "B93EF22D769A70CB"
TVDB_API_URL = "http://thetvdb.com/api/"
TVDB_BANNER_URL = "http://thetvdb.com/banners/"
###################################################################################################

### Notification Constants 
PUSHBULLET_API_URL = "https://api.pushbullet.com/v2/"
PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"
PUSHOVER_API_KEY = "ajMtuYCg8KmRQCNZK2ggqaqiBw2UHi"
###################################################################################################

TV_SHOW_OBJECT_FIX_CLIENTS = ["Android", "Plex for Android"]

from LocalePatch import SetAvailableLanguages

LANGUAGES = ['en']

###################################################################################################
#   Start Code
#
# This (optional) function is initially called by the PMS framework to initialize the plug-in. This includes setting up
# the Plug-in static instance along with the displayed artwork. These setting below are pretty standard
# You first set up the containers and default for all possible objects.  You will probably mostly use Directory Objects
# and Videos Objects. But many of the other objects give you added entry fields you may want to use and set default thumb
# and art for. For a full list of objects and their parameters, refer to the Framework Documentation.
########################################################
def Start():

# There are  few commands you may see appear in this section that are no longer needed.  Below is an explanation of them
# provided from a very helpful channel designer who was nice enough to explain their purpose to me:
#    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
# This a left-over from when plugins had more control over how the contents were displayed. ViewGroups were defined to 
# tell the client how to display the contents of the directory. Now, most (if not all) clients have a fairly rigid model
# for what types of content get display in which way. Generally, it is best to remove it from a plugins when since it
# gets ignored anyways. 
#
#    HTTP.CacheTime = CACHE_1HOUR
# This setting a global cache time for all HTTP requests made by the plugin. This over-rides the framework's default 
# cache period which,
# I don't remember off the top of my head. It is entirely optional, but if you're going to use it, the idea is to pick a 
# cache-time that is reasonable. Ie. store data for a long enough time that you can realistically reduce the load on
# external servers as well as speed up the load-time for HTTP-requests, but not so long that changes/additions are not
# caught in a reasonable time frame. IMO, unless you specifically want/need a specific cache-length, I would remove that
# line and allow the framework to manage the cache with its default settings.
#
#   HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'
# This assigning a specific User-Agent header for all HTTP requests made by the plugin. Generally speaking, each time a
# plugin is started, a user-agent is randomly selected from a list to be used for all HTTP requests. In some cases, a
# plugin will perform better using a specific user-agent instead of a randomly assigned one. For example, some websites
# return different data for Safari on an iPad, then what they return for Chrome or Firefox on a PC. Again, if you don't
# have a specific need to set a specific user-agent, I would remove that code from your channel.

# You set up the default attributes for all you object containers and objects.  You will probably mostly use Directory
# Objects and Videos Objects but many of the other objects give you added entry fields you may want to use.  For a full 
# list of objects and their parameters, refer to the Framework Documentation.

# Important Note: (R stands for Resources folder) to tell the channel where these images are located.

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)

    DirectoryObject.thumb = R(ICON)
    DirectoryObject.art = R(ART)
    EpisodeObject.thumb = R(ICON)
    EpisodeObject.art = R(ART)
    VideoClipObject.thumb = R(ICON)
    VideoClipObject.art = R(ART)

    Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    Log.Debug("Channel Version: " + VERSION)

    SetAvailableLanguages(LANGUAGES)

    # DICT[] 
    # DICT[] IS PART OF THE PLEX FRAMEWORK THAT ALLOWS YOU TO SAVE DATA IN A GLOBAL VARIABLE THAT IS RETAINED WHEN YOU EXIT THE PLUGIN
    # SO YOU CAN PULL IT UP IN MULTIPLE FUNCTIONS WITHOUT PASSING THE VARIABLES FROM FUNCTION TO FUNCTION. AND IT CAN BE ACCESSED AND USED
    # OVER MULTIPLE SESSIONS
    ## Initialize Dictionary
    if 'tv' not in Dict:
        Dict['tv'] = {}
    if 'movie' not in Dict:
        Dict['movie'] = {}
    if 'music' not in Dict:
        Dict['music'] = {}
    if 'register' not in Dict:
        Dict['register'] = {}
        Dict['register_reset'] = Datetime.TimestampFromDatetime(Datetime.Now())
    if 'blocked' not in Dict:
        Dict['blocked'] = []
    if 'sonarr_users' not in Dict:
        Dict['sonarr_users'] = []
    if 'sickbeard_users' not in Dict:
        Dict['sickbeard_users'] = []
    if 'debug' not in Dict:
        Dict['debug'] = False
    if 'DumbKeyboard-History' not in Dict:
        Dict['DumbKeyboard-History'] = []
    Dict.Save()


def ValidatePrefs():
    return


from Session import Session


###################################################################################################
# This tells Plex how to list you in the available channels and what type of channels this is 
@handler(PREFIX, TITLE, art=ART, thumb=ICON)
@route(PREFIX + '/main')

def MainMenu():
    Log.Info("=================== __init__::MainMenu ==================")
    sesh = Session(session_id=Hash.MD5(str(Datetime.Now())))
    return sesh.SMainMenu()

"""
List of Client.Product and Client.Platform

Client.Product 	        Description
--------------          ------------------------------------------------------------------
Plex for Android 	    Android phone
Plex for iOS 	        Apple phone
Plex Home Theater 	    This is for Plex Home Theater
Plex Media Player 	    This is for new Plex Media Player
Plex Web 	            Plex Web client, from web browser
Plex for Firefox TV 	Plex Firefox TV, (source), this one is a guess
Plex for Roku 	        Roku
OpenPHT 	            OpenPHT
Plex Chromecast 	    Chromecast
NotifyPlex 	            NZBGet
HTPC Manager 	        Windows Server (Windows-2012Server-6.2.9200). Not sure if correct.
Plex for Xbox One 	    Xbox One
Plex for Xbox 360       Xbox 360
Plex for Samsung        Samsung

Client.Platform 	    Description
---------------         -------------------------------------------------------------------
Android 	            Android phone
iOS 	                Apple phone
Safari 	                This is a guess from looking at a Service URL code.
Chrome              	Plex Web client on Chrome internet browser
Plex Home Theater 	    This is for Plex Home Theater
Konvergo 	            Plex Media Player, (running on a Raspberry PI 2 B)
tvOS 	                New AppleTV
MacOSX 	                MacOSX
Linux 	                Linux
Windows 	            Windows
LGTV 	                LGTV
Roku 	                Roku
Chromecast          	Chromecast
NZBGet 	                NZBGet
Xbox One            	Xbox One
Xbox 360                Xbox 360
Samsung                 Samsung

"""
