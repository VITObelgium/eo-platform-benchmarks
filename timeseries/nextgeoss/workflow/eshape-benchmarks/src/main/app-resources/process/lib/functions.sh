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
    ${ERR_NOINPUT}) msg="No input found";;
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
 
  if test -z "$input"
  then
	ciop-log "ERROR" "No input products found"
	cleanExit 50
  fi  

  local outputID=$(date '+%s')

  # Setup some folder to store the input products 
  local inputDir=${TMPDIR}/file-input
  ciop-log "INFO" "Creating dir - ${inputDir}"
  mkdir -p ${inputDir}

  local processDir=${TMPDIR}/process-dir
  ciop-log "INFO" "Creating dir - ${processDir}"
  mkdir -p ${processDir}

  local outputDir=${TMPDIR}/output-dir
  ciop-log "INFO" "Creating dir - ${outputDir}"
  mkdir -p ${outputDir}
 
 
  ciop-log "INFO" "Download products"
  files="$(curl "$input" -L --insecure | xmllint --format - | grep '<atom:link .*rel="enclosure"' | sed -E 's/.*href="([^"]+)".*/\1/')" 
  /opt/anaconda/envs/benchmarks/bin/python ${_CIOP_APPLICATION_PATH}/process/download.py -o ${inputDir} -p ${files} 
  
  ciop-log "INFO" "Copy the input bands to process dir ${processDir}"   
  cp ${inputDir}/$(ciop-getparam filter) ${processDir}/
  
  ciop-log "INFO" "Copying input geometry to file"
  echo $(ciop-getparam geojson) > ${processDir}/feature.geojson

  ciop-log "INFO" "Process band information"
  cd ${_CIOP_APPLICATION_PATH}/process
  /opt/anaconda/envs/benchmarks/bin/python run.py -d ${processDir} -f ".*tif" -g ${processDir}/feature.geojson -o ${outputDir}/result_${outputID}.json
 
  ciop-log "INFO" "Publishing results" 
  ciop-publish -m ${outputDir}/result_${outputID}.json

  ciop-log "INFO" "Cleaning up dirs"
  rm -rf ${inputDir}
  rm -rf ${processDir}
  rm -rf ${outputDir}
}
