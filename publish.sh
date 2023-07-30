#!/usr/bin/env bash

__usage(){
  echo "$0 <tag>" >&2
}
if ! command -v space > /dev/null; then
  exit 1
fi
if [[ "$#" != 1 ]]; then
  __usage
  exit 1
fi
tag="$1"
if [[ -z "${tag}" ]]; then
  __usage
  exit 1
fi
space validate && space push && space release -v "${tag}" --listed
