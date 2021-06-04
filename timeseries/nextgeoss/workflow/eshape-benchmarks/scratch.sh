URL="http://catalogue-0.nextgeoss.eu/opensearch/search.atom?productType=SENTINEL2_L1C&timerange_start=2021-02-20&timerange_end=2021-06-01&bbox=-2.227906,55.656955,-2.221469,55.660054&count=1&identifier=S2B_MSIL1C_20210221T113319_N0209_R080_T30UWG_20210221T122848"

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
echo "opensearch-client $PARAMS -p count=1 https://catalogue-0.nextgeoss.eu/opensearch/description.xml?osdd=SENTINEL2_L1C enclosure" > commands.log

for enclosure in $(opensearch-client -v $PARAMS https://catalogue-0.nextgeoss.eu/opensearch/description.xml?osdd=SENTINEL2_L1C enclosure); 
do
	echo "Start 2 copy enclosure ${enclosure}"
        # Copy file to given input directory
	echo "ciop-copy -U -o /tmp \"${enclosure}\"" >> commands.log
	echo $enclosure >> enclosure.txt
        s2Product=$(ciop-copy -U -o ${INPUT_DIR} "${enclosure}")
done

echo $s2Product
