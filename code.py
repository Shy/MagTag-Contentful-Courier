import time
import gc
import wifi
import random
import adafruit_requests
import ssl
import socketpool
import terminalio
from adafruit_magtag.magtag import MagTag

magtag = MagTag()

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("Credentials and tokens are kept in secrets.py, please add them there!")
    raise

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

endpoint = "https://graphql.contentful.com/content/v1/spaces/%s/" % (
    secrets["space_id"]
)
headers = {"Authorization": "Bearer %s" % (secrets["CDA_token"])}

# Get Dev Blog Posts
query = """query {
  blogPostCollection {
    items {
      sys {
        id
      }
    }
  }
}"""

print("Making blog post collection query.")
response = requests.post(endpoint, json={"query": query}, headers=headers)

# Get Individual Post
query = """{
  blogPost(id: \"%s\") {
    title
    publishDate
    slug
    authorsCollection {
      items {
        name
      }
    }
    introduction
  }
}
""" % (
    random.choice(response.json()["data"]["blogPostCollection"]["items"])["sys"]["id"]
)

print("Making blog post query.")
response = requests.post(endpoint, json={"query": query}, headers=headers)

# Formatting for the title text
magtag.add_text(
    text_font="/fonts/Lato-Bold-ltd-25.bdf",
    text_position=(10, 15),
)
magtag.set_text(response.json()["data"]["blogPost"]["title"], auto_refresh=False)

# Formatting for the author text
magtag.add_text(
    text_font="/fonts/Arial-Bold-12.pcf",
    text_position=(10, 38),
)

author_string = ""
for author in response.json()["data"]["blogPost"]["authorsCollection"]["items"]:
    if author_string == "":
        author_string = author["name"]
    else:
        author_string = author_string + " & " + author["name"]

magtag.set_text(
    val=author_string,
    index=1,
    auto_refresh=False,
)

# Formatting for the publish date
magtag.add_text(
    text_font="/fonts/Arial-12.bdf",
    text_position=(10, 60),
)

year = int(response.json()["data"]["blogPost"]["publishDate"][0:4])
month = int(response.json()["data"]["blogPost"]["publishDate"][5:7])
day = int(response.json()["data"]["blogPost"]["publishDate"][8:10])

months = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

strdate = "Published %s %d, %s" % (months[month - 1], day, year)
print(strdate)

slug = response.json()["data"]["blogPost"]["slug"]

blog_url = f"https://www.contentful.com/blog/{year}/{month:02}/{day:02}/{slug}/"

magtag.set_text(val=strdate, index=2, auto_refresh=False)
# Formatting for the introduction text
magtag.add_text(
    text_font=terminalio.FONT,
    text_position=(10, 94),
    line_spacing=0.8,
    text_wrap=47,  # wrap text at this count
)

magtag.set_text(
    val=response.json()["data"]["blogPost"]["introduction"][0:170] + "...",
    index=3,
)

endpoint = "https://api.courier.com/send/"
headers["Authorization"] = "Bearer %s" % (secrets["courier_token"])
headers["Accept"] = "application/json"
headers["Content-Type"] = "application/json"

courier_JSON = {
    "event": "MAGTAG_NOTIFICATION",
    "recipient": "discord_channel",
    "data": {
        "title": response.json()["data"]["blogPost"]["title"],
        "introduction": response.json()["data"]["blogPost"]["introduction"][0:170]
        + "...",
        "url": blog_url,
        "author": author_string,
        "publish_date": strdate,
    },
}

button_colors = ((255, 0, 0), (255, 150, 0), (0, 255, 255), (180, 0, 255))
button_tones = (1047, 1318, 1568, 2093)

button_a_pressed = False

print("Starting the loop, go ahead and press some buttons. :)")
while True:
    if magtag.peripherals.button_a_pressed:
        if button_a_pressed == False:
            for i, b in enumerate(magtag.peripherals.buttons):
                magtag.peripherals.neopixel_disable = False
                magtag.peripherals.neopixels[i] = button_colors[i]
                time.sleep(0.25)
                magtag.peripherals.neopixels[i] = (0, 0, 0)
            print("Making request to Courier")
            response = requests.post(endpoint, json=courier_JSON, headers=headers)
            button_a_pressed = True
            print("Courier response: ")
            print(response.json())

    if magtag.peripherals.button_d_pressed:
        for i, b in enumerate(magtag.peripherals.buttons):
            magtag.peripherals.neopixel_disable = False
            magtag.peripherals.neopixels[i] = button_colors[i]
            time.sleep(0.25)
            magtag.peripherals.neopixels[i] = (0, 0, 0)
            # magtag.peripherals.play_tone(button_tones[i], 0.25)
    else:
        button_a_pressed = False
        magtag.peripherals.neopixel_disable = True
pass
