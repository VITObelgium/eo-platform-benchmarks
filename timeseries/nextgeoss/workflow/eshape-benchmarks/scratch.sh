URL="http://catalogue-9.nextgeoss.eu/opensearch/search.atom?productType=TERRASCOPE_SENTINEL_2_LAI_V2&bbox=5.186920166015626,51.23548217222581,5.217475891113282,51.25009723956958&timerange_start=2018-03-20&timerange_end=2018-03-23&identifier=S2A_20180322T105021_31UFS_LAI_20M_V200"

function getosparams() {
        URL=$1	
	PARAMS=${URL##*\?}
	PARAMS_ARR=(${PARAMS//[&]/ })
	declare -A PARAM_MAPPING
	PARAM_MAPPING['identifier']="{http://a9.com/-/opensearch/extensions/geo/1.0/}uid"
	PARAM_MAPPING['timerange_start']="{http://a9.com/-/opensearch/extensions/time/1.0/}start"
	PARAM_MAPPING['timerange_end']="{http://a9.com/-/opensearch/extensions/time/1.0/}end"
	PARAM_MAPPING['bbox']="{http://a9.com/-/opensearch/extensions/geo/1.0/}box"
	PARAM_MAPPING['count']="{http://a9.com/-/spec/opensearch/1.1/}count"


	COMMAND_PARAMS=""
	for param in "${PARAMS_ARR[@]}"
	do
		p=(${param//[=]/ })

		if [[ ! -z ${PARAM_MAPPING[${p[0]}]} ]]; then
			COMMAND_PARAMS+=" -p ${PARAM_MAPPING[${p[0]}]}=${p[1]}"
		fi	
	done
	echo $COMMAND_PARAMS

}

echo "$URL"

INPUT_DIR='/tmp/s2-biopar-input'

mkdir -p $INPUT_DIR

PARAMS=$(getosparams $URL)
echo $PARAMS
echo "opensearch-client $PARAMS -p count=1 https://catalogue.nextgeoss.eu/opensearch/description.xml?osdd=TERRASCOPE_SENTINEL_2_LAI_V2 enclosure" > commands.log

for enclosure in $(opensearch-client -v $PARAMS https://catalogue.nextgeoss.eu/opensearch/description.xml?osdd=TERRASCOPE_SENTINEL_2_LAI_V2 enclosure); 
do
	echo "Start 2 copy enclosure ${enclosure}"
        # Copy file to given input directory
	echo "ciop-copy -U -o /tmp \"${enclosure}\"" >> commands.log
	echo $enclosure >> enclosure.txt
        s2Product=$(ciop-copy -U -o ${INPUT_DIR} "${enclosure}")
done

echo $s2Product
