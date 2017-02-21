#!/bin/bash
InFile=$1
OutFile=$2

echo "[" >> $OutFile;

while read line
do
    
    if [[ $line == *\[\*\*\]* ]]; then
       echo " {" >> $OutFile;
       id=`echo $line | awk '{gsub(/\[/,"");gsub(/\]/,"");print $2}'`;
       echo "   \"ID\" : \"$id\"," >> $OutFile;

    elif [[ $line == *\-\>* ]]; then
       date_time=`echo $line | awk '{print $1}'`;
       utc_time=`echo $date_time | awk -F\. '{gsub(/-/," ",$1);gsub(/\//,"-",$1);print $1}' | xargs -i date -d "2017-{}" +%s`;
       echo "   \"UTC_Time\":\"$utc_time\"," >> $OutFile;

       source=`echo $line | awk '{print $2}'`;
       source_ip=`echo $source | awk -F\: '{print $1}'`;
       source_port=`echo $source | awk -F\: '{print $2}'`;
       echo "   \"Source_IP\" : \"$source_ip\"," >> $OutFile;
       echo "   \"Source_Port\" : \"$source_port\"," >> $OutFile;

       destination=`echo $line | awk '{print $4}'`;
       destination_ip=`echo $destination | awk -F\: '{print $1}'`;
       destination_port=`echo $destination | awk -F\: '{print $2}'`;
       echo "   \"Destination_IP\" : \"$destination_ip\"," >> $OutFile;
       echo "   \"Destination_Port\" : \"$destination_port\"," >> $OutFile;

    elif [[ $line == *TTL* ]]; then
       protocol=`echo $line | awk '{print $1}'`;
       echo "   \"Protocol\" : \"$protocol\"" >> $OutFile;
       echo " }," >> $OutFile;

    fi
done < $InFile

echo "]" >> $OutFile
