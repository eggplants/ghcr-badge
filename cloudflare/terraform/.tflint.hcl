# tflint --recursive enters each directory holding .tf files and reads the
# .tflint.hcl it finds there, so this lives next to the configuration it checks.
plugin "terraform" {
  enabled = true
  preset  = "all"
}
