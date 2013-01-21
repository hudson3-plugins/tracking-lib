#!/bin/bash
echo "$1" "$2" "$3"
find . -name "$1" | xargs perl -pi -e 's/$2/$3/g'
