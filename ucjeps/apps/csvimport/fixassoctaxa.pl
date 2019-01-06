use strict;

while (<>) {
  chomp;
  s/\r//g; # just in case...
  my (@columns) = split "\t",$_,-1;
  @columns[23] =~ s/\|.*//; # get rid of all values except the first
  @columns[23] =~ s/associatedTaxa/associatedTaxa\tinteraction/; # handle header
  @columns[23] =~ s/^(.*?) \((.*?)\).*$/\1\t\2/; # split the field on ' ('
  @columns[23] = @columns[23] . "\t" unless @columns[23] =~ /\t/; # add a tab if needed
  #print scalar @columns, "\n";
  print join("\t",@columns). "\n";
}

