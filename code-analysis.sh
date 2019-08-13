#!/usr/bin/env bash
echo "STATIC CODE ANALYSIS"
echo "===================="
echo

echo "MODULE ANALYSIS"
echo "---------------"
pylint --rcfile=.pylintrc skabase

echo "TESTS ANALYSIS"
echo "--------------"
pylint --rcfile=.pylintrc -f json skabase/SKAAlarmHandler/test \
    skabase/SKABaseDevice/test \
    skabase/SKACapability/test \
    skabase/SKALogger/test \
    skabase/SKAMaster/test \
    skabase/SKAObsDevice/test \
    skabase/SKASubarray/test \
    skabase/SKATelState/test
