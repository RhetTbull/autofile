# autofile

Automatically move or copy files based on metadata associated with the files.

autofile uses a template system to specify the target directory and/or filename based on the file's metadata.  For example: 

`autofile *.mp3 --target ~/Music --directory "{audio:artist}/{audio:album}"` 

Will move all mp3 files to new folders with `Artist/Album` naming scheme.  

The template system is very flexible and powerful allowing you to perform transforms on the metadata fields and use conditional logic. 

autofile understands 

```
$ ls -l ~/Pictures/NewPhotos
total 12160
-rw-r--r--@ 1 user  staff  3449684 Oct 24 07:10 IMG_1234.jpeg
-rw-r--r--@ 1 user  staff  2771656 Oct 23 12:53 IMG_1235.jpg

$ autofile --target ~/Pictures/FiledPhotos --directory "{exiftool:Make}/{exiftool:created.year}/{exiftool:created.month}" ~/Pictures/NewPhotos/* --verbose
Processing 2 files
Moving /Users/user/Pictures/NewPhotos/IMG_1234.jpeg to /Users/user/Pictures/FiledPhotos/Apple/2021/October/IMG_1234.jpeg
Moving /Users/user/Pictures/NewPhotos/IMG_1235.jpg to /Users/user/Pictures/FiledPhotos/Apple/2021/October/IMG_1235.jpg
Done. Processed 2 files.
Done.

$ tree ~/Pictures/FiledPhotos
/Users/user/Pictures/FiledPhotos
└── Apple
    └── 2021
        └── October
            ├── IMG_1234.jpeg
            └── IMG_1235.jpg


```

```
$ls -1 ~/Music/Unfiled
file1.mp3
file10.mp3
file11.mp3
file12.mp3
file2.mp3
file3.mp3
file4.mp3
file5.mp3
file6.mp3
file7.mp3
file8.mp3
file9.mp3

$ autofile --target ~/Music/Filed --directory "{audio:artist}/{audio:album}" --filename "{format:int:02d,{audio:track}} - {audio:title}.mp3" ~/Music/Unfiled/*.mp3 --verbose
Processing 12 files
Moving /Users/user/Music/Unfiled/file1.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/01 - Story of My Life.mp3
Moving /Users/user/Music/Unfiled/file10.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/10 - The Mission : How Great Thou
Art.mp3
Moving /Users/user/Music/Unfiled/file11.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/11 - Because of You.mp3
Moving /Users/user/Music/Unfiled/file12.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/12 - Pictures at an Exhibition.mp3
Moving /Users/user/Music/Unfiled/file2.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/02 - Let It Go.mp3
Moving /Users/user/Music/Unfiled/file3.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/03 - Ants Marching : Ode to Joy.mp3
Moving /Users/user/Music/Unfiled/file4.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/04 - Fathers' Eyes.mp3
Moving /Users/user/Music/Unfiled/file5.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/05 - Kung Fu Piano: Cello Ascends.mp3
Moving /Users/user/Music/Unfiled/file6.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/06 - Summer Jam.mp3
Moving /Users/user/Music/Unfiled/file7.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/07 - Batman Evolution.mp3
Moving /Users/user/Music/Unfiled/file8.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/08 - Don't You Worry Child (feat. Shweta
Subram).mp3
Moving /Users/user/Music/Unfiled/file9.mp3 to /Users/user/Music/Filed/The Piano Guys/Wonders/09 - Home.mp3
Done. Processed 12 files.
Done.

$ tree ~/Music/Filed
/Users/user/Music/Filed
└── The\ Piano\ Guys
    └── Wonders
        ├── 01\ -\ Story\ of\ My\ Life.mp3
        ├── 02\ -\ Let\ It\ Go.mp3
        ├── 03\ -\ Ants\ Marching\ :\ Ode\ to\ Joy.mp3
        ├── 04\ -\ Fathers'\ Eyes.mp3
        ├── 05\ -\ Kung\ Fu\ Piano:\ Cello\ Ascends.mp3
        ├── 06\ -\ Summer\ Jam.mp3
        ├── 07\ -\ Batman\ Evolution.mp3
        ├── 08\ -\ Don't\ You\ Worry\ Child\ (feat.\ Shweta\ Subram).mp3
        ├── 09\ -\ Home.mp3
        ├── 10\ -\ The\ Mission\ :\ How\ Great\ Thou\ Art.mp3
        ├── 11\ -\ Because\ of\ You.mp3
        └── 12\ -\ Pictures\ at\ an\ Exhibition.mp3
```

