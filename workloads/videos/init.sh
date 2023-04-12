#!/bin/sh

pvc.py create cas-data-video-input 16G
pvc.py create cas-data-video-output 32G

nrp_storage.py ./youtube-wnhvanMdx4s.1080p.mp4 pvc://cas-data-video-input:videos/

# Or equivalently, do it via two explicit steps:
# nrp_storage.py ./youtube-wnhvanMdx4s.1080p.mp4 s3:us-west:tmp.0762cb130f9d49ad9353e73c7c11a753/
# nrp_storage.py s3:us-west:tmp.0762cb130f9d49ad9353e73c7c11a753/ pvc://cas-data-video-input:videos/
