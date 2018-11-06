#!/bin/bash

./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 0  -R tmp/res00.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 1  -R tmp/res01.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 2  -R tmp/res02.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 3  -R tmp/res03.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 4  -R tmp/res04.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 5  -R tmp/res05.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 6  -R tmp/res06.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 7  -R tmp/res07.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 8  -R tmp/res08.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 9  -R tmp/res09.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 10 -R tmp/res10.csv voxforge_en &
./auto_review.py -m kaldi-generic-en-tdnn_f-latest -l en -s 12 -o 11 -R tmp/res11.csv voxforge_en &

wait

echo "to apply the review result, run:"
echo "./apply_review.py -l en voxforge_en tmp/*.csv"


