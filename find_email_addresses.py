#!/usr/bin/python
import sys
import urllib2
import re
import bs4
import requests

# stealing from Django
def is_valid_url(url):
    import re
    regex = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url is not None and regex.search(url)

# from StackOverflow 
class NoRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        infourl = urllib2.addinfourl(fp, headers, req.get_full_url())
        infourl.status = code
        infourl.code = code
        return infourl
    http_error_300 = http_error_302
    http_error_301 = http_error_302
    http_error_303 = http_error_302
    http_error_307 = http_error_302

originalUrl = str(sys.argv[1])
if not originalUrl.startswith('http'):
    startingUrl = 'http://' + originalUrl
else:
    startingUrl = originalUrl

# keep track of found URLs, and those that need to be processed in separated list
foundUrls = []
queuedUrls = [startingUrl]

# this is what we return
foundEmails = []

opener = urllib2.build_opener(NoRedirectHandler())
urllib2.install_opener(opener)

domain = originalUrl[originalUrl.rfind(".", 0, originalUrl.rfind("."))+1:]

session = requests.Session()
while (len(queuedUrls)):
    myUrl = queuedUrls.pop()
    try:
        response = session.get(myUrl)
    # To handle server errors
    except requests.exceptions.ConnectionError:
        continue
    # To handle too many redirects (301 to 302 to 301...)
    except requests.exceptions.TooManyRedirects:
        continue

    for h in response.history:
        if not originalUrl in h.url:
            continue
    html = response.text

    # use BeautifulSoup to do the parsing for us
    soup = bs4.BeautifulSoup(html, "html.parser")
    urls = [link['href'] for link in soup('a') if 'href' in link.attrs]
    emails = soup.select('a[href^=mailto]')

    for email in emails:
        # different formats for emails, let's parse it
        emailResult = re.findall('[a-zA-Z0-9+_\-\.]+@[0-9a-zA-Z][.-0-9a-zA-Z]*.[a-zA-Z]+', str(email))
        # just in case beautifulsoup is wrong
        if len(emailResult) == 0:
            continue
        email = emailResult[0]
        # reduce to email only
        if "?" in email:
            email = email.split("?")[0]
        # we are only interested by our domain
        if not domain in email:
            continue
        # let's avoid duplicates
        if not email in foundEmails:
            foundEmails.append(email)
    for url in urls:
        if url.startswith("//"):
            url = "http:" + url
        if "//" + originalUrl not in url:
            continue
        if not is_valid_url(url):
            continue
        if "?" in url:
            url = url.split("?")[0]
        if "#" in url:
            url = url.split("#")[0]
        # parse common files type that are not html
        if url.endswith(('.pdf', '.mov', '.ram')):
            continue
        # add newly found urls to lists
        if not url in foundUrls:
            foundUrls.append(url)
            queuedUrls.append(url)


print 'Found these email addresses:'
for email in foundEmails:
    print email
