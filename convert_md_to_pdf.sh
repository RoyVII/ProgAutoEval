#!/bin/bash

# Needs:
# Pandoc: https://pandoc.org/installing.html
# wkhtmltopdf (sudo apt install wkhtmltopdf)
# github-pandoc.css https://gist.github.com/dashed/6714393#file-github-pandoc-css

for d in */ ; do
    echo "$d"
    cd $d
    for md in *.md ; do
	    echo "$md"
	    outname=${md%".md"}
	    pandoc -s $md -f gfm -t html5 --output $outname.pdf --pdf-engine=wkhtmltopdf --css ../github-pandoc.css
	done
	cd ..
done



 
