#!/usr/bin/env bash
echo "STATIC CODE ANALYSIS"
echo "===================="
echo

# FIXME pylint needs to run twice since there is no way
pylint -f colorized skabase
pylint skabase > skabase_sca.xml
