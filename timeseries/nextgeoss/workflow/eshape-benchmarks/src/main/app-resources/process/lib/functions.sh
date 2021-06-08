#!/bin/bash

# define the exit codes
SUCCESS=0
ERR_PUBLISH=55
ERR_NOINPUT=50

# source the ciop functions (e.g. ciop-log, ciop-getparam)
source ${ciop_job_include}

###############################################################################
# Trap function to exit gracefully
# Globals:
#   SUCCESS
#   ERR_PUBLISH
# Arguments:
#   None
# Returns:
#   None
###############################################################################
function cleanExit ()
{
  local retval=$?
  local msg=""
  case "${retval}" in
    ${SUCCESS}) msg="Processing successfully concluded";;
    ${ERR_PUBLISH}) msg="Failed to publish the results";;
    *) msg="Unknown error";;
  esac

  [ "${retval}" != "0" ] && ciop-log "ERROR" "Error ${retval} - ${msg}, processing aborted" || ciop-log "INFO" "${msg}"
  exit ${retval}
}


###############################################################################
# Log an input string to the log file
# Globals:
#   None
# Arguments:
#   input reference to log
# Returns:
#   None
###############################################################################
function log_input()
{
  local input=${1}
  ciop-log "INFO" "processing input: ${input}"
}

###############################################################################
# Pass the input string to the next node, without storing it on HDFS
# Globals:
#   None
# Arguments:
#   input reference to pass
# Returns:
#   0 on success
#   ERR_PUBLISH if something goes wrong 
###############################################################################
function pass_next_node()
{
  local input=${1}
  echo "${input}" | ciop-publish -s || return ${ERR_PUBLISH}
}

###############################################################################
# Functions to retrieve the opensearch mapping
###############################################################################
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


###############################################################################
# Main function to process an input reference
# Globals:
#   None
# Arguments:
#   input reference to process
# Returns:
#   0 on success
#   ERR_PUBLISH if something goes wrong
#me $inputProduct)${id}.tif"##############################################################################
function main()
{
  local input=${1}
  # Log the input
  log_input ${input}
  
  # Setup some folder to store the input products
  
  local inputDir=${TMPDIR}/file-input
  mkdir -p ${inputDir}

  params=$(getosparams $input)
  ciop-log "INFO" "Querying opensearch client with params $params"
  enclosure="$(opensearch-client $params https://catalogue.nextgeoss.eu/opensearch/description.xml?osdd=SENTINEL2_L2A enclosure)"

  rm -rf ${inputDir}/$(basename ${enclosure}) 
  inputProduct=$( ciop-copy -U -o ${inputDir} "${enclosure}" )     # -U = disable automatic decompression of zip - files
  inputProduct="${inputProduct}$(basename ${enclosure})"
 
  ciop-log "INFO" "Downloaded product ${inputProduct} to ${inputDir}" 
  #ls -lh ${inputDir}
 
  [ $? -eq 0 ] && [ -e "${inputProduct}" ] || return ${ERR_NOINPUT}

  id=$([[ $input =~ .*identifier=(.*)\&? ]] && echo ${BASH_REMATCH[1]})
  newProduct="$(dirname $inputProduct)/${id}.zip"
  ciop-log "INFO" "Updating product ${inputProduct}  name to ${newProduct}"
  mv ${inputProduct} ${newProduct} 
  #ls -lh ${newProduct} 
  ciop-log "INFO" "Unzipping ${newProduct}"
  unzip -qq ${newProduct} -d $inputDir
  local processDir=${TMPDIR}/process-dir
  ls -lh ${inputDir}
  ciop-log "INFO" "Copy the input bands to process dir ${processDir}"   
  mkdir -p ${processDir}
  cp ${inputDir}/*SAFE/GRANULE/*/IMG_DATA/R10m/*B0[2,3,4]_10m.jp2 ${processDir}/
  ls -lh ${processDir}
 

  ciop-log "INFO" "Process band information"
  local outputDir=${TMPDIR}/output-dir
  local outputID=$(echo date '+%s')
  mkdir -p ${outputDir}

  source activate benchmarks
  cd ${_CIOP_APPLICATION_PATH}/process
  python run.py -d ${processDir} -f .* -o ${outputDir}/result_${outputID}.json
 # Just pass the input reference to the next node 
  ciop-publish -m ${processDir}/result.json
}
