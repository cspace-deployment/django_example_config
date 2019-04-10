use strict;

if (scalar @ARGV != 4) {
    print "\n";
    print "need 4 arguments:\n";
    print "before-&-after_file.csv input_file.csv output_file.csv column_to_change\n";
    print "\n";
    print "3 filenames and an integer (counting from 1)\n";
    print "\n";
    exit(1);
}

my ($change, $input, $output, $column_to_change) = @ARGV;

print "\n";
print 'change:      ' . $change . "\n";
print 'input:       ' . $input . "\n";
print 'output:      ' . $output . "\n";
print 'change col:  ' . $column_to_change . "\n";
print "\n";

$column_to_change--;

open(IN, $change) || die 'could not read ' . $change;

my $rewritein = 0;
my $harmless = 0;
my %REWRITE;
my %TARGET_VALUES;

while (<IN>) {
    chomp;
    next if (m/^#/);
    $rewritein++;
    my ($rewrite, $replacewith) = split(/\t/);
    if ($rewrite eq $replacewith) {
        $harmless++;
        next;
    }
    $REWRITE{$rewrite} = $replacewith;
    $TARGET_VALUES{$replacewith} = $rewrite;
}
close(IN);

open(OUT, ">$output") || die 'could not write to ' . $output;
open(IN, $input) || die 'could not read ' . $input;

my $linesin = 0;
my $linesout = 0;
my $changed = 0;
my $unchanged = 0;

while (<IN>) {
    chomp;
    next if (m/^#/);
    $linesin++;
    my @cells = split /\t/, $_, -1;
    my $source_column = @cells[$column_to_change];

    my $ischanged = 0;
    if (exists $REWRITE{$source_column}) {
        $ischanged++;
        @cells[$column_to_change] = $REWRITE{$source_column};
    }

    if ($ischanged > 0) {
        $changed++;
    }
    else {
        $unchanged++;
    }

    print OUT join("\t", @cells) . "\n";
    $linesout++;
}

print 'rewrite pairs read:    ' . $rewritein . "\n";
print 'vacuous pairs skipped: ' . $harmless . "\n";
print 'lines read:            ' . $linesin . "\n";
print 'lines output:          ' . $linesout . "\n";
print 'changed lines:         ' . $changed . "\n";
print 'unchanged lines:       ' . $unchanged . "\n";
