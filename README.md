# twfy-vector-explorer
Vector research project

# Loading data

rsync -az --progress --exclude '.svn' --exclude 'tmp/' --relative data.theyworkforyou.com::parldata/scrapedxml/debates/debates201* data/pwdata
rsync -az --progress --exclude '.svn' --exclude 'tmp/' --relative data.theyworkforyou.com::parldata/scrapedxml/debates/debates202* data/pwdata
script/manage infer --transcript_type debates --chamber_type uk_commons --pattern 201
