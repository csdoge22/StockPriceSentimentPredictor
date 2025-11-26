import ssl
import urllib.request
import certifi

ctx = ssl.create_default_context(cafile=certifi.where())
response = urllib.request.urlopen("https://google.com", context=ctx)
print(response.status)