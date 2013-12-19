#!/bin/sh

HOME=`dirname $0`
cd $HOME

JAR="./lib/sflowrt.jar"
JVM_OPTS="-Xincgc -Xmx200m"
RT_OPTS="-Dsflow.port=6343 -Dhttp.port=8008"

exec java ${JVM_OPTS} ${RT_OPTS} -jar ${JAR}

