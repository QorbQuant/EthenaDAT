"""HTTP smoke check; run against Wrangler dev or the deployed canonical origin."""
import json, sys, urllib.request, urllib.error, xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
BASE = sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8777'
class Page(HTMLParser):
    def __init__(self):
        super().__init__(); self.headings=0; self.canon=[]; self.links=[]; self.ids={}; self.schemas=[]; self.mode=None; self.boot=''; self.active=''; self.text={}; self.capture=None
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='h1': self.headings+=1
        if tag=='link' and a.get('rel')=='canonical': self.canon.append(a['href'])
        if tag=='a': self.links.append(a.get('href',''))
        if 'id' in a: self.ids[a['id']]=a; self.capture=a['id']
        if tag=='script':
            self.mode='schema' if a.get('type')=='application/ld+json' else 'boot' if a.get('id')=='dashboard-bootstrap' else None
            self.active=''
    def handle_data(self,data):
        if self.mode: self.active+=data
        if self.capture: self.text[self.capture]=self.text.get(self.capture,'')+data
    def handle_endtag(self,tag):
        if tag=='script':
            if self.mode=='schema': self.schemas.append(json.loads(self.active))
            if self.mode=='boot': self.boot=json.loads(self.active)
            self.mode=None
        self.capture=None

def get(path):
    return urllib.request.urlopen(urllib.request.Request(BASE+path,headers={'User-Agent':'EthenaDashSEOCheck/1.0'}),timeout=20)
xml=get('/sitemap.xml').read(); urls=[n.text for n in ET.fromstring(xml).iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')]
links=set()
for url in urls:
    path=urlsplit(url).path
    with get(path) as r:
        assert r.status==200
        html=r.read().decode(); p=Page(); p.feed(html)
    assert p.headings==1,(path,'h1',p.headings)
    assert p.canon==[url],(path,p.canon)
    assert len(p.schemas)==1,(path,'schema')
    assert 'noindex' not in html.lower(),path
    if path in ['/stablecoinx/','/ethenapay/']:
        key='sx' if path=='/stablecoinx/' else 'pay'
        assert 'hidden' not in p.ids['full-'+key]
        assert p.boot[key]['series']['date']
        assert p.text['sx-price' if key=='sx' else 'pay-hero-spend'].strip() not in ('','—')
        assert '<tr><td>' in html
        assert '<path d="M' in html
        assert html.index('dashboard-bootstrap')>html.index('defer src="/assets/app.js"')
    links.update(urlsplit(href).path for href in p.links if href.startswith('/') and not href.startswith('//'))
    print('PASS',path,'one H1, canonical, schema, initial HTML')
for link in links:
    assert get(link).status==200,link
try:
    get('/this-page-does-not-exist-seo-test')
    raise AssertionError('404 missing')
except urllib.error.HTTPError as e:
    assert e.code==404
assert b'Sitemap: https://ethenadash.com/sitemap.xml' in get('/robots.txt').read()
print('PASS',len(links),'internal links; robots and real 404')
