this folder contains the programmes for compressing and normalising Japanese texts using mecab.
mecab installation, therefore, is a pre-requisite
you also need my python library, which can be found

https://github.com/yosato/myPythonLibs.git

the wrapper script is compress_normalise_jp.py and its basic usage is

python3 compress_normalise_jp.py <raw-corpus-path> <mecab-dictionary-path> [--exemplar-fp <path>] [--freqwd-fp <path>]

where the last two of the parameters (square brackets) are optional (but desirable, to be explained below).

Compression here means compression of vocabulary by not expanding to inflected forms. Broadly speaking, they are reduced to their lemmas, 

Normalisation means that of different orthographical forms into a canonical form. Typical examples are hiragana-katakana-kanji equivalents. The programme first judges if a probable normalisation is possible, and if so, render it to its canonical form. If there are multiple canonical forms probable, it shows those probable forms.

An exemplar is the single most dominant of all the variants. For example '許す' can be considered an exemplar amongst others, e.g. kana versions or '赦す', an esoteric rendering. This information can be written in the form <all-hiragana-version>\t<exemplar> per line in a file

With a frequent word file, you can restrict the normalisation to relatively frequent words as well. The file format is <occurrence>\t<word> per line in the descending order of occurrence.





