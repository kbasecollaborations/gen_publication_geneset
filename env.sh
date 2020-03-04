export PATH=ncbi-blast-2.2.31+-src/c++/ReleaseMT/bin/blastp:$PATH
curl -L https://cpanmin.us | perl - App::cpanminus
 
 
cd ~/bin #make sure ~/bin is in the PATH
curl -L https://cpanmin.us/ -o cpanm
chmod +x cpanm
 
cpanm CGI
cpanm DBD::SQLite
 
export PERL5LIB=~/perl5/lib/perl5:$PERL5LIB
