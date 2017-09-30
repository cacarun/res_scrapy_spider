from scrapy import cmdline

name = 'beauty'
cmd = 'scrapy crawl {0}'.format(name)
cmdline.execute(cmd.split())
