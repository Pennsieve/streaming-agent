#!/bin/bash

LABEL=
TITLE=
DESCRIPTION=
FORMAT=

curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"label":"TS-12345", "title":"the title of the stream", "description":"a short description of the data","format":"EDF"}' \
     http://localhost:5678/stream
