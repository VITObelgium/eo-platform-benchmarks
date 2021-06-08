URL="http://catalogue-9.nextgeoss.eu/opensearch/search.atom?productType=SENTINEL2_L2A&bbox=5.186920166015626,51.23548217222581,5.217475891113282,51.25009723956958&timerange_start=2021-02-25&timerange_end=2021-06-06&identifier=S2A_MSIL2A_20210604T105031_N0300_R051_T31UFS_20210604T141149"

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
echo "opensearch-client $PARAMS -p count=1 https://catalogue.nextgeoss.eu/opensearch/description.xml?osdd=SENTINEL2_L2A enclosure" > commands.log

for enclosure in $(opensearch-client -v $PARAMS https://catalogue.nextgeoss.eu/opensearch/description.xml?osdd=SENTINEL2_L2A enclosure); 
do
	echo "Start 2 copy enclosure ${enclosure}"
        # Copy file to given input directory
	echo "ciop-copy -U -o /tmp \"${enclosure}\"" >> commands.log
	echo $enclosure >> enclosure.txt
        s2Product=$(ciop-copy -U -o ${INPUT_DIR} "${enclosure}")
done

echo $s2Product
