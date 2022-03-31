#!/bin/bash

curl -X POST -H "Content-Type: application/json" -d '{"label":"data-label", "description":"short description of the data","format":"EDF"}' http://localhost:5678/publish
