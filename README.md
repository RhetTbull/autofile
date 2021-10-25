# autofile

Automatically move or copy files based on metadata associated with the files.  For example, file your photos based on EXIF metadata or use MP3 tags to file your music files.

autofile uses a template system to specify the target directory and/or filename based on the file's metadata.  For example: 

`autofile *.mp3 --target ~/Music --directory "{audio:artist}/{audio:album}"` 

Will move all mp3 files to new folders with `Artist/Album` naming scheme.  

The template system is very flexible and powerful allowing you to perform transforms on the metadata fields and use conditional logic. 

autofile understands metadata about audio files (MP3, OPP, etc), photo & video files, macOS specific metadata such as Finder tags as well as various filesystem related metadata. 

Photo and video metadata (EXIF, IPTC, XMP, etc.) requires that the third-party [exiftool](https://exiftool.org/) command line utility be installed. All other metadata works with no additional dependencies.

## Examples

File image files into directory structure with format "Camera Make/Year/Month/file.jpg":

```
$ ls -l ~/Pictures/NewPhotos
total 12160
-rw-r--r--@ 1 user  staff  3449684 Oct 24 07:10 IMG_1234.jpeg
-rw-r--r--@ 1 user  staff  2771656 Oct 23 12:53 IMG_1235.jpg

$ autofile --target ~/Pictures/FiledPhotos \
--directory "{exiftool:Make}/{exiftool:created.year}/{exiftool:created.month}" \
~/Pictures/NewPhotos/* 

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

File MP3 files into directory with with format "Artist/Album" and rename files with format "Track number - Track title.mp3" (and format track to be 2 digits with leading zeros):

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

$ autofile --target ~/Music/Filed \
--directory "{audio:artist}/{audio:album}" \
--filename "{format:int:02d,{audio:track}} - {audio:title}.mp3" \
~/Music/Unfiled/*.mp3 

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

## Supported Platforms

Currently macOS only. Tested on macOS 10.15.7 (Catalina) but should work fine on newer versions. With the exception of macOS specific metadata like Finder tags, this could be ported to linux fairly easily but I don't have a use case for this.  

Copy and move use native macOS calls to take advantage of advanced features copy-on-write that are not available with the standard python system calls. 

## Cautions and Warnings

This software is feature complete but not yet fully tested.  No warranty of any kind is implied or provided.  Please ensure you have a backup before using this software as it can rename and move your files with no undo feature.  I recommend you always run autofile with the `--dry-run` flag first to ensure you understand exactly what it will do.

## Command Line Reference

```
$ autofile --help
Usage: autofile [OPTIONS] FILES...

  move or copy files into directories based on a template string

Required: [all required]
  -t, --target TARGET_DIRECTORY  Target destination directory.

Filing templates: [at least 1 required]
  -D, --directory DIRECTORY_TEMPLATE
                                 Directory template for exporting files.
  -F, --filename FILENAME_TEMPLATE
                                 Filename template for exporting files.

Filter Options:
  -g, --glob PATTERN             Filter files to process with a glob pattern,
                                 e.g. '--glob "*.jpg"' --glob may be repeated
                                 to use more than one pattern. Multiple
                                 patterns treated as "OR", that is, a file that
                                 matches one or more patterns will be
                                 processed.
  -r, --regex PATTERN            Filter files to process with a regex pattern,
                                 e.g. '--regex "IMG_[1-3].*"' --regex may be
                                 repeated to use more than one pattern.
                                 Multiple patterns treated as "OR", that is, a
                                 file that matches one or more patterns will be
                                 processed. Any valid python regular express
                                 may be used.
  -f, --filter TEMPLATE_PATTERN  Filter files to process that match a metadata
                                 template pattern, e.g. '--filter
                                 "{mdls:kMDItemKind contains image}"'. --filter
                                 matches the file if TEMPLATE_PATTERN evaluates
                                 to a non-null value. --filter may be repeated
                                 to use more than one pattern. Multiple
                                 patterns treated as "OR", that is, a file that
                                 matches one or more patterns will be
                                 processed.

Options:
  -w, --walk                     Recursively walk directories.
  -Q, --quiet                    Turn off verbose output.
  -c, --copy                     Copy files instead of moving them.
  -h, --hardlink                 Hardlink files instead of moving them.
  -d, --dry-run                  Dry run mode; do not actually move/copy any
                                 files.

Other options:
  --version                      Show the version and exit.
  --help                         Show this message and exit.

Template System

autofile contains a rich templating system which allows fine-grained control   
over the output format of metadata. The templating system converts one or      
template statements, written in autofile templating language, to one or more   
rendered values using metadata information from the file being processed.      

In its simplest form, a template statement has the form: "{template_field}",   
for example "{size}" which resolves to the size of the file. Template fields   
may also have subfields delineated by a : as in "{audio:artist}" which resolves
to the artist name for an audio file (e.g. mp3).  In this example, the field is
audio and the subfield is artist.  Template fields may also have attributes    
delineated by a . as in "{created.year}" which resolves to the 4-digit year of 
the file creation date. In this example, the field is created and the attribute
is year.                                                                       

Template statements may contain one or more modifiers.  The full syntax is:    

"pretext{delim+template_field:subfield|filter[find,replace]                    
conditional?bool_value,default}posttext"                                       

Template statements are white-space sensitive meaning that white space (spaces,
tabs) changes the meaning of the template statement.                           

pretext and posttext are free form text.  For example, if an image file has    
Title (e.g. XMP:Title) "My file Title". the template statement "The title of   
the file is {exiftool:Title}", resolves to "The title of the file is My file   
Title".  The pretext in this example is "The title if the file is " and the    
template_field is {Title}.  Note: some punctuation such as commas cannot be    
used in the pretext or posttext.  For this reason, the template system provides
special punctuation templates like {comma} to insert punctuation where needed. 
For example: {exiftool:Make}{comma}{exiftool:Model} could resolve to           
Apple,iPhone SE.                                                               

delim: optional delimiter string to use when expanding multi-valued template   
values in-place                                                                

+: If present before template name, expands the template in place.  If delim   
not provided, values are joined with no delimiter.                             

e.g. if image file keywords are ["foo","bar"]:                                 

 • "{exiftool:Keywords}" renders to "foo", "bar"                               
 • "{,+exiftool:Keywords}" renders to: "foo,bar"                               
 • "{; +exiftool:Keywords}" renders to: "foo; bar"                             
 • "{+exiftool:Keywords}" renders to "foobar"                                  

template_field: The template field to resolve.                                 

:subfield: Templates may have sub-fields; reserved for future use.             

|filter: You may optionally append one or more filter commands to the end of   
the template field using the vertical pipe ('|') symbol.  Filters may be       
combined, separated by '|' as in: {user|capitalize|parens}.                    

Valid filters are:                                                             

 • lower: Convert value to lower case, e.g. 'Value' => 'value'.                
 • upper: Convert value to upper case, e.g. 'Value' => 'VALUE'.                
 • strip: Strip whitespace from beginning/end of value, e.g. ' Value ' =>      
   'Value'.                                                                    
 • titlecase: Convert value to title case, e.g. 'my value' => 'My Value'.      
 • capitalize: Capitalize first word of value and convert other words to lower 
   case, e.g. 'MY VALUE' => 'My value'.                                        
 • braces: Enclose value in curly braces, e.g. 'value => '{value}'.            
 • parens: Enclose value in parentheses, e.g. 'value' => '(value')             
 • brackets: Enclose value in brackets, e.g. 'value' => '[value]'              

e.g. if file keywords are ["FOO","bar"]:                                       

 • "{exiftool:Keywords|lower}" renders to "foo", "bar"                         
 • "{exiftool:Keywords|upper}" renders to: "FOO", "BAR"                        
 • "{exiftool:Keywords|capitalize}" renders to: "Foo", "Bar"                   
 • "{exiftool:Keywords|lower|parens}" renders to: "(foo)", "(bar)"             

e.g. if an image file description is "my description":                         

 • "{exiftool:Description|titlecase}" renders to: "My Description"             

[find,replace]: optional text replacement to perform on rendered template      
value.  For example, to replace "/" in a a keyword, you could use the template 
"{exiftool:Keywords[/,-]}".  Multiple replacements can be made by appending "|"
and adding another find|replace pair.  e.g. to replace both "/" and ":" in     
keywords: "{exiftool:Keywords[/,-|:,-]}".  find/replace pairs are not limited  
to single characters.  The "|" character cannot be used in a find/replace pair.

conditional: optional conditional expression that is evaluated as boolean      
(True/False) for use with the ?bool_value modifier.  Conditional expressions   
take the form ' not operator value' where not is an optional modifier that     
negates the operator.  Note: the space before the conditional expression is    
required if you use a conditional expression.  Valid comparison operators are: 

 • contains: template field contains value, similar to python's in             
 • matches: template field contains exactly value, unlike contains: does not   
   match partial matches                                                       
 • startswith: template field starts with value                                
 • endswith: template field ends with value                                    
 • <=: template field is less than or equal to value                           
 • >=: template field is greater than or equal to value                        
 • <: template field is less than value                                        
 • >: template field is greater than value                                     
 • ==: template field equals value                                             
 • !=: template field does not equal value                                     

The value part of the conditional expression is treated as a bare (unquoted)   
word/phrase.  Multiple values may be separated by '|' (the pipe symbol).  value
is itself a template statement so you can use one or more template fields in   
value which will be resolved before the comparison occurs.                     

For example:                                                                   

 • {exiftool:Keywords matches Beach} resolves to True if 'Beach' is a keyword. 
   It would not match keyword 'BeachDay'.                                      
 • {exiftool:Keywords contains Beach} resolves to True if any keyword contains 
   the word 'Beach' so it would match both 'Beach' and 'BeachDay'.             
 • {ISO < 100} resolves to True if the file's ISO is < 100.                    
 • {exiftool:Keywords|lower contains beach} uses the lower case filter to do   
   case-insensitive matching to match any keyword that contains the word       
   'beach'.                                                                    
 • {exiftool:Keywords|lower not contains beach} uses the not modifier to negate
   the comparison so this resolves to True if there is no keyword that matches 
   'beach'.                                                                    

?bool_value: Template fields may be evaluated as boolean (True/False) by       
appending "?" after the field name or "[find/replace]".  If a field is True or 
has any value, the value following the "?" will be used to render the template 
instead of the actual field value.  If the template field evaluates to False or
has no value (e.g. file has no title and field is "{audio:title}") then the    
default value following a "," will be used.                                    

e.g. if file has a title                                                       

 • "{audio:title?I have a title,I do not have a title}" renders to "I have a   
   title"                                                                      

and if it does not have a title:                                               

 • "{audio:title?I have a title,I do not have a title}" renders to "I do not   
   have a title"                                                               

,default: optional default value to use if the template name has no value.     
This modifier is also used for the value if False for boolean-type fields (see 
above) as well as to hold a sub-template for values like {created.strftime}.   
If no default value provided and the field is null, autofile will use a default
value of '_' (underscore character).                                           

Template fields such as created.strftime use the default value to pass the     
template to use for strftime.                                                  

e.g., if file date is 4 February 2020, 19:07:38,                               

 • "{created.strftime,%Y-%m-%d-%H%M%S}" renders to "2020-02-04-190738"         

If you want to include "{" or "}" in the output, use "{openbrace}" or          
"{closebrace}" template substitution.                                          

e.g. "{created.year}/{openbrace}{audio.title}{closebrace}" would result in     
"2020/{file Title}".                                                           

Some templates have additional modifiers that can be appended to the template  
name to access specific attributes of the template field. For example, the     
{filepath} template returns the path of the file being processed and           
{filepath.parent} returns the parent directory.                                

File Information Fields                                                        

Field    Description
{size}   Size of file in bytes
{uid}    User identifier of the file owner
{gid}    Group identifier of the file owner
{user}   User name of the file owner
{group}  Group name of the file owner

Date/Time Fields                                                               

Field       Description
{created}   File creation date/time
{modified}  File modification date/time
{accessed}  File last accessed date/time

Date/time fields may be formatted using "dot notation" attributes which are    
appended to the field name following a . (period). For example, {created.month}
resolves to the month name of the file's creation date in the user's locale,   
e.g. December.                                                                 

The following attributes are available:                                        

Attribute  Description
date       ISO date, e.g. 2020-03-22
year       4-digit year, e.g. 2021
yy         2-digit year, e.g. 21
month      Month name as locale's full name, e.g. December
mon        Month as locale's abbreviated name, e.g. Dec
mm         2-digit month, e.g. 12
dd         2-digit day of the month, e.g. 22
dow        Day of the week as locale's full name, e.g. Tuesday
doy        Julian day of year starting from 001
hour       2-digit hour, e.g. 10
min        2-digit minute, e.g. 15
sec        2-digit second, e.g. 30
strftime   Apply strftime template to date/time. Should be used in form
           {created.strftime,TEMPLATE} where TEMPLATE is a valid strftime
           template, e.g. {created.strftime,%Y-%U} would result in year-week
           number of year: '2020-23'. If used with no template will return null
           value. See https://strftime.org/ for help on strftime templates.

File Path Fields                                                               

Field       Description
{filepath}  The full path to the file being processed

The {filepath} fields returns the full path to the source file being processed.
Various attributes of the path can be accessed using "dot notation" (appended  
to the filepath field with a '.'). For example, {filepath.name} returns just   
the name of the file without the full path. {filepath.parent} returns the      
parent directory of the file.                                                  

Path attributes can be chained, for example {filepath.parent.name} returns just
the name of the immediate parent directory without the full directory path.    

For example, if the field {filepath} is '/Shared/files/IMG_1234.JPG':          

 • {filepath.parent} is '/Shared/files'                                        
 • {filepath.name} is 'IMG_1234.JPG'                                           
 • {filepath.stem} is 'IMG_1234'                                               
 • {filepath.suffix} is '.JPG'                                                 

The following attributes are available:                                        

Subfield  Description
name      The name of the file
stem      The name of the file without the suffix (extension)
suffix    The suffix (extension) of the file, including the leading `.`
parent    The parent directory of the file

String Formatting Fields                                                       

Field     Description
{strip}   Use in form '{strip,TEMPLATE}'; strips whitespace from begining and
          end of rendered TEMPLATE value(s).
{format}  Use in form, '{format:TYPE:FORMAT,TEMPLATE}'; converts TEMPLATE value
          to TYPE then formats the value using python string formatting codes
          specified by FORMAT; TYPE is one of: 'int', 'float', or 'str'.

The {strip} and {format} fields are used to format strings. {strip,TEMPLATE}   
strips whitespace from TEMPLATE. For example, {strip,{exiftool:Title}} will    
strip any excess whitespace from the title of an image file.                   

{format:TYPE:FORMAT,TEMPLATE} formats TEMPLATE using python string formatting  
codes. For example:                                                            

 • {format:int:02d,{audio:track}} will format the track number of an audio file
   to two digits with leading zeros.                                           
 • {format:str:-^30,{audio.title}} will center the title of an audio file and  
   pad it to 30 characters with '-'.                                           

TYPE must be one of 'int', 'float', or 'str'. See                              
https://docs.python.org/3.7/library/string.html#formatspec for more information
on valid FORMAT values.                                                        

macOS Metadata Fields                                                          

Field   Description
{mdls}  Get metadata attributes for file as returned by mdls command; use in
        form '{mdls:ATTRIBUTE}', for example, '{mdls:kMDItemContentType}'

{mdls:ATTRIBUTE} returns the value of the metadata ATTRIBUTE as returned by the
macOS mdls command. For example, {mdls:kMDItemContentType} returns the content 
type of the file, e.g. public.python-script or public.mp3 and                  
{mdls:kMDItemKind} returns a description of file type, e.g. Python Script or   
MP3 Audio.                                                                     

Finder Metadata                                                                

Field     Description
{finder}  Get metadata managed by macOS Finder such as tags and comments; use
          in form '{finder:SUBFIELD}', e.g. '{finder:tags}'

{finder} provides access to Finder metadata. It must be used in the form       
{finder:SUBFIELD} where SUBFIELD is one of the following:                      

Subfield  Description
tags      Finder tags (keywords)
comment   Finder comment

Uniform Type Identifier (UTI) Fields                                           

Field  Description
{uti}  Uniform Type Identifier (UTI) for file

The {uti} template returns the macOS Uniform Type Identifier (UTI) for the     
file. For example, {uti} for a file with extension .pdf would return           
com.adobe.pdf.                                                                 

Audio Files                                                                    

Field    Description
{audio}  Use in form '{audio:TAG}'; Returns tag value for various audio types
         include mp3,

The {audio} field provides access to audio-file related tags for audio files.  
The following formats are supported:                                           

 • MP3 (ID3 v1, v1.1, v2.2, v2.3+)                                             
 • Wave/RIFF                                                                   
 • OGG                                                                         
 • OPUS                                                                        
 • FLAC                                                                        
 • WMA                                                                         
 • MP4/M4A/M4B                                                                 
 • AIFF/AIFF-C                                                                 

The {audio} field must be used with one or more the following subfields in the 
form: {audio:SUBFIELD}, for example: {audio:title} or {audio:artist}.          

Subfield      Description
album         album as string
albumartist   album artist as string
artist        artist name as string
audio_offset  number of bytes before audio data begins
bitrate       bitrate in kBits/s
comment       file comment as string
composer      composer as string
disc          disc number
disc_total    the total number of discs
duration      duration of the song in seconds
filesize      file size in bytes
genre         genre as string
samplerate    samples per second
title         title of the song
track         track number as string
track_total   total number of tracks as string
year          year or data as string

Photo and Video Files                                                          

Field       Description
{exiftool}  Format: '{exiftool:GROUP:TAGNAME}'; use exiftool
            (https://exiftool.org) to extract metadata, in form GROUP:TAGNAME
            or TAGNAME, from image. E.g. '{exiftool:Make}' to get camera make,
            or {exiftool:IPTC:Keywords} to extract keywords. See
            https://exiftool.org/TagNames/ for list of valid tag names.  Group
            name is optional (e.g. EXIF, IPTC, etc) but if specified, should be
            the same as used in `exiftool -G`, e.g. '{exiftool:EXIF:Make}'.
            exiftool must be installed in the path to use this template field
            (https://exiftool.org/).

The {exiftool} template uses the third-party exiftool app                      
(https://exiftool.org) to extract metadata from photo and video files.         

It must be used with one or more subfields which are exiftool tags, for        
example: {exiftool:EXIF:Make} for camera make, or {exiftool:IPTC:Keywords} for 
keywords. The exiftool Group name (e.g. IPTC) is optional.                     

There are two derived subfields: created and modified which represent the      
created date or the modified date, respectively. These subfields are datetime  
values and you can access the various attributes of the datetime by using an   
attribute name following a period, e.g. {exiftool:created.year} for the 4-digit
year.                                                                          

The following attributes are supported:                                        

Attribute  Description
date       ISO date, e.g. 2020-03-22
year       4-digit year, e.g. 2021
yy         2-digit year, e.g. 21
month      Month name as locale's full name, e.g. December
mon        Month as locale's abbreviated name, e.g. Dec
mm         2-digit month, e.g. 12
dd         2-digit day of the month, e.g. 22
dow        Day of the week as locale's full name, e.g. Tuesday
doy        Julian day of year starting from 001
hour       2-digit hour, e.g. 10
min        2-digit minute, e.g. 15
sec        2-digit second, e.g. 30
strftime   Apply strftime template to date/time. Should be used in form
           {created.strftime,TEMPLATE} where TEMPLATE is a valid strftime
           template, e.g. {created.strftime,%Y-%U} would result in year-week
           number of year: '2020-23'. If used with no template will return null
           value. See https://strftime.org/ for help on strftime templates.

Punctuation Fields                                                             

Field           Description
{comma}         A comma: ','
{semicolon}     A semicolon: ';'
{questionmark}  A question mark: '?'
{pipe}          A vertical pipe: '|'
{openbrace}     An open brace: '{'
{closebrace}    A close brace: '}'
{openparens}    An open parentheses: '('
{closeparens}   A close parentheses: ')'
{openbracket}   An open bracket: '['
{closebracket}  A close bracket: ']'
{newline}       A newline: '\n'
{lf}            A line feed: '\n', alias for {newline}
{cr}            A carriage return: '\r'
{crlf}          a carriage return + line feed: '\r\n'

Within the template system, many punctuation characters have special meaning,  
e.g. {} indicates a template field and this means that some punctuation        
characters cannot be inserted into the template. Thus, if you want to insert   
punctuation into the rendered template value, you can use these punctuation    
fields to do so. For example, {openbrace}value{closebrace} will render to      
{value}.                                                                       
```

## Contributions

Contributions of all kinds are welcome!  If you find a bug or have an idea to improve autofile, please open an issue!
