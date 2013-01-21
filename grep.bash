#!/bin/bash
echo "$1" "$2"
grep -r --include "$1" "$2" *
